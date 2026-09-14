"""
ECDAT impact-attribution primitives.

PropagationPath is the structural output produced by the dependency
propagation engine.

AttributionPath is the deterministic analytical explanation derived
from that structural result. It deliberately preserves the distinction
between propagation and attribution.
"""

from dataclasses import dataclass
from typing import Iterable, Tuple


def _sorted_unique(values: Iterable[str] | None) -> Tuple[str, ...]:
    if values is None:
        return ()

    return tuple(
        sorted(
            {
                str(value)
                for value in values
                if value is not None
            }
        )
    )


@dataclass(frozen=True)
class AttributionPath:
    """
    Deterministic analytical explanation of an impact path.

    The path is derived from an existing PropagationPath. It does not
    perform traversal itself.

    root_node_id:
        Origin node from which the propagation path began.

    affected_node_id:
        Final node attributed as affected.

    dependency_ids:
        Observed dependency edges traversed by propagation.

    relationship_ids:
        Optional derived relationship identifiers associated with the
        analytical attribution.

    evidence_ids:
        Evidence supporting the dependency/relationship path.

    depth:
        Number of propagation hops represented by the path.
    """

    root_node_id: str
    affected_node_id: str
    dependency_ids: Tuple[str, ...] = ()
    relationship_ids: Tuple[str, ...] = ()
    evidence_ids: Tuple[str, ...] = ()
    depth: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "dependency_ids",
            _sorted_unique(self.dependency_ids),
        )

        object.__setattr__(
            self,
            "relationship_ids",
            _sorted_unique(self.relationship_ids),
        )

        object.__setattr__(
            self,
            "evidence_ids",
            _sorted_unique(self.evidence_ids),
        )

        if self.depth < 0:
            raise ValueError("depth must be >= 0")

    @classmethod
    def from_propagation_path(
        cls,
        path: object,
        *,
        relationship_ids: Iterable[str] | None = None,
    ) -> "AttributionPath":
        """
        Convert an existing PropagationPath into an attribution path.

        This method intentionally accepts the structural path object rather
        than re-running dependency traversal.
        """

        node_ids = tuple(
            getattr(path, "node_ids", ())
        )

        if not node_ids:
            raise ValueError(
                "Propagation path must contain at least one node"
            )

        dependency_ids = tuple(
            getattr(path, "dependency_ids", ())
        )

        evidence_ids = tuple(
            getattr(path, "evidence_ids", ())
        )

        return cls(
            root_node_id=str(node_ids[0]),
            affected_node_id=str(node_ids[-1]),
            dependency_ids=dependency_ids,
            relationship_ids=(
                tuple(relationship_ids)
                if relationship_ids is not None
                else ()
            ),
            evidence_ids=evidence_ids,
            depth=max(0, len(node_ids) - 1),
        )

    def canonical_bytes(self) -> bytes:
        """
        Stable canonical representation used by deterministic hashing.
        """

        payload = "|".join(
            (
                self.root_node_id,
                self.affected_node_id,
                str(self.depth),
                ",".join(self.dependency_ids),
                ",".join(self.relationship_ids),
                ",".join(self.evidence_ids),
            )
        )

        return payload.encode("utf-8")


@dataclass(frozen=True)
class AttributionRelation:
    """
    Evidence-backed relationship used by an impact attribution.

    relation_type:
        Identifies the semantic relationship.

    derivation:
        OBSERVED when directly supplied by evidence.
        DERIVED when constructed analytically from other relationships.

    source_id / target_id:
        Canonical entities connected by the relationship.

    origin_dependency_ids:
        Observed dependency records supporting the relationship.

    evidence_ids:
        Evidence records supporting the relationship.

    confidence:
        Confidence assigned to this particular relationship.
    """

    relation_id: str
    relation_type: str
    source_id: str
    target_id: str
    derivation: str = "OBSERVED"
    origin_dependency_ids: Tuple[str, ...] = ()
    evidence_ids: Tuple[str, ...] = ()
    confidence: str = "unknown"

    OBSERVED = "OBSERVED"
    DERIVED = "DERIVED"

    def __post_init__(self) -> None:
        derivation = str(self.derivation).upper()

        if derivation not in {
            self.OBSERVED,
            self.DERIVED,
        }:
            raise ValueError(
                "derivation must be OBSERVED or DERIVED"
            )

        object.__setattr__(
            self,
            "derivation",
            derivation,
        )

        object.__setattr__(
            self,
            "origin_dependency_ids",
            _sorted_unique(self.origin_dependency_ids),
        )

        object.__setattr__(
            self,
            "evidence_ids",
            _sorted_unique(self.evidence_ids),
        )

    def canonical_bytes(self) -> bytes:
        payload = "|".join(
            (
                self.relation_id,
                self.relation_type,
                self.source_id,
                self.target_id,
                self.derivation,
                ",".join(self.origin_dependency_ids),
                ",".join(self.evidence_ids),
                self.confidence,
            )
        )

        return payload.encode("utf-8")
