"""Deterministic, evidence-backed downstream impact attribution.

This module consumes dependency propagation results and business context. It
attributes impact; it does not discover dependencies, traverse the graph, or
make migration/remediation decisions.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

from analysis.attribution import AttributionPath, AttributionRelation


KNOWN = "KNOWN"
CONDITIONAL = "CONDITIONAL"
UNRESOLVED = "UNRESOLVED"
DIRECT = "DIRECT"
INDIRECT = "INDIRECT"


def _sorted_unique(values: Iterable[str] | None) -> tuple[str, ...]:
    if values is None:
        return ()
    return tuple(sorted({str(value) for value in values if value is not None}))


def _value(item: object, key: str, default: object = None) -> object:
    if isinstance(item, Mapping):
        return item.get(key, default)
    return getattr(item, key, default)


@dataclass(frozen=True)
class ImpactAttribution:
    """Attribution for one downstream node."""

    node_id: str
    impact_status: str
    impact_type: str
    depth: int
    origin_dependency_ids: tuple[str, ...]
    dependency_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    business_context_ids: tuple[str, ...]
    business_evidence_ids: tuple[str, ...]
    business_consequence: str
    attribution_confidence: str


@dataclass(frozen=True)
class ImpactAssessment:
    """Complete deterministic impact assessment."""

    root_node_ids: tuple[str, ...]
    attributions: tuple[ImpactAttribution, ...]
    attribution_paths: tuple[AttributionPath, ...]
    attribution_relations: tuple[AttributionRelation, ...]
    known_count: int
    conditional_count: int
    unresolved_count: int
    digest: str

    def canonical_bytes(self) -> bytes:
        rows = [
            "roots=[" + ",".join(self.root_node_ids) + "]",
        ]
        for item in self.attributions:
            rows.append(
                "ATTRIBUTION|" + "|".join(
                    [
                        item.node_id,
                        item.impact_status,
                        item.impact_type,
                        str(item.depth),
                        ",".join(item.origin_dependency_ids),
                        ",".join(item.dependency_ids),
                        ",".join(item.evidence_ids),
                        ",".join(item.business_context_ids),
                        ",".join(item.business_evidence_ids),
                        item.business_consequence,
                        item.attribution_confidence,
                    ]
                )
            )

        for path in sorted(
            self.attribution_paths,
            key=lambda item: (
                item.root_node_id,
                item.affected_node_id,
                item.depth,
                item.dependency_ids,
                item.evidence_ids,
            ),
        ):
            rows.append(
                "PATH|" + path.canonical_bytes().decode("utf-8")
            )

        for relation in sorted(
            self.attribution_relations,
            key=lambda item: item.relation_id,
        ):
            rows.append(
                "RELATION|" + relation.canonical_bytes().decode("utf-8")
            )

        return "\n".join(rows).encode("utf-8")


class ImpactAttributionEngine:
    """Attribute propagated cryptographic impact to business context.

    Structural propagation is supplied by the v0.6 engine. This layer only
    joins that result with business context and evidence, preserving the
    distinction between known, conditional, and unresolved attribution.
    """

    _SEVERITY = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}

    def assess(
        self,
        propagation_result: object,
        business_contexts: Iterable[object] = (),
        *,
        root_node_ids: Iterable[str] = (),
        context_evidence_ids: Iterable[str] | None = None,
    ) -> ImpactAssessment:
        context_by_application: dict[str, list[object]] = {}
        for context in business_contexts:
            application_id = _value(context, "application_id")
            if application_id:
                context_by_application.setdefault(str(application_id), []).append(context)

        attributions: list[ImpactAttribution] = []
        attribution_paths: list[AttributionPath] = []
        attribution_relations: list[AttributionRelation] = []

        affected_nodes = tuple(
            _value(propagation_result, "affected_nodes", ()) or ()
        )

        for affected in affected_nodes:
            node_id = str(_value(affected, "node_id"))
            depth = int(_value(affected, "depth", 0) or 0)
            origin_ids = _sorted_unique(_value(affected, "origin_dependency_ids", ()))

            paths = tuple(_value(affected, "paths", ()) or ())

            for propagation_path in paths:
                attribution_path = AttributionPath.from_propagation_path(
                    propagation_path
                )
                attribution_paths.append(attribution_path)

                relation_seed = attribution_path.canonical_bytes()
                relation_id = (
                    "rel-"
                    + hashlib.sha256(relation_seed).hexdigest()[:32]
                )

                attribution_relations.append(
                    AttributionRelation(
                        relation_id=relation_id,
                        relation_type="IMPACTS",
                        source_id=attribution_path.root_node_id,
                        target_id=attribution_path.affected_node_id,
                        derivation=AttributionRelation.DERIVED,
                        origin_dependency_ids=(
                            attribution_path.dependency_ids
                        ),
                        evidence_ids=(
                            attribution_path.evidence_ids
                        ),
                        confidence="derived",
                    )
                )

            dependency_ids = _sorted_unique(
                dependency_id
                for path in paths
                for dependency_id in (_value(path, "dependency_ids", ()) or ())
            )
            evidence_ids = _sorted_unique(
                evidence_id
                for path in paths
                for evidence_id in (_value(path, "evidence_ids", ()) or ())
            )
            dependency_ids = _sorted_unique((*dependency_ids, *origin_ids))

            contexts = context_by_application.get(node_id, [])
            context_ids = _sorted_unique(_value(context, "context_id") for context in contexts)
            business_evidence = _sorted_unique(
                evidence_id
                for context in contexts
                for evidence_id in (_value(context, "evidence_ids", ()) or ())
            )
            business_evidence = _sorted_unique(
                (*business_evidence, *(context_evidence_ids or ()))
            )

            unresolved = not contexts
            conditional = False
            consequences: list[str] = []
            confidences: list[str] = []

            for context in contexts:
                source = str(_value(context, "source", "unresolved") or "unresolved").lower()
                confidence = str(_value(context, "confidence", "low") or "low").lower()
                consequence = self._business_consequence(context)
                consequences.append(consequence)
                confidences.append(confidence)
                if source == "unresolved":
                    unresolved = True
                elif confidence in {"low", "unknown", "unresolved"}:
                    conditional = True

            if unresolved:
                status = UNRESOLVED
                consequence = "UNRESOLVED"
                attribution_confidence = "low"
            elif conditional:
                status = CONDITIONAL
                consequence = max(consequences, key=self._severity_rank)
                attribution_confidence = "conditional"
            else:
                status = KNOWN
                consequence = max(consequences, key=self._severity_rank)
                attribution_confidence = self._best_confidence(confidences)

            impact_type = DIRECT if depth == 0 else INDIRECT
            attributions.append(
                ImpactAttribution(
                    node_id=node_id,
                    impact_status=status,
                    impact_type=impact_type,
                    depth=depth,
                    origin_dependency_ids=origin_ids,
                    dependency_ids=dependency_ids,
                    evidence_ids=evidence_ids,
                    business_context_ids=context_ids,
                    business_evidence_ids=business_evidence,
                    business_consequence=consequence,
                    attribution_confidence=attribution_confidence,
                )
            )

        attributions.sort(key=lambda item: (item.depth, item.node_id))

        attribution_paths = sorted(
            {
                path
                for path in attribution_paths
            },
            key=lambda item: (
                item.root_node_id,
                item.affected_node_id,
                item.depth,
                item.dependency_ids,
                item.evidence_ids,
            ),
        )

        attribution_relations = sorted(
            {
                relation
                for relation in attribution_relations
            },
            key=lambda item: item.relation_id,
        )

        roots = _sorted_unique(root_node_ids)

        provisional = ImpactAssessment(
            root_node_ids=roots,
            attributions=tuple(attributions),
            attribution_paths=tuple(attribution_paths),
            attribution_relations=tuple(attribution_relations),
            known_count=sum(item.impact_status == KNOWN for item in attributions),
            conditional_count=sum(item.impact_status == CONDITIONAL for item in attributions),
            unresolved_count=sum(item.impact_status == UNRESOLVED for item in attributions),
            digest="",
        )
        digest = hashlib.sha256(provisional.canonical_bytes()).hexdigest()
        return ImpactAssessment(
            root_node_ids=provisional.root_node_ids,
            attributions=provisional.attributions,
            attribution_paths=provisional.attribution_paths,
            attribution_relations=provisional.attribution_relations,
            known_count=provisional.known_count,
            conditional_count=provisional.conditional_count,
            unresolved_count=provisional.unresolved_count,
            digest=digest,
        )

    @staticmethod
    def _business_consequence(context: object) -> str:
        values = [
            str(_value(context, field, "MEDIUM") or "MEDIUM").upper()
            for field in (
                "operational_criticality",
                "financial_impact",
                "regulatory_exposure",
                "customer_impact",
            )
        ]
        return max(values, key=ImpactAttributionEngine._severity_rank)

    @staticmethod
    def _severity_rank(value: str) -> int:
        return {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}.get(value, 0)

    @staticmethod
    def _best_confidence(values: Sequence[str]) -> str:
        rank = {"low": 0, "medium": 1, "high": 2}
        if not values:
            return "low"
        return max(values, key=lambda value: rank.get(value, 0))


def build_impact_assessment(
    propagation_result: object,
    business_contexts: Iterable[object] = (),
    *,
    root_node_ids: Iterable[str] = (),
    context_evidence_ids: Iterable[str] | None = None,
) -> ImpactAssessment:
    """Build a deterministic evidence-backed impact assessment."""
    return ImpactAttributionEngine().assess(
        propagation_result,
        business_contexts,
        root_node_ids=root_node_ids,
        context_evidence_ids=context_evidence_ids,
    )
