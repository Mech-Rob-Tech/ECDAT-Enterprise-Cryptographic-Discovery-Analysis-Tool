"""Tests for deterministic v0.7 impact attribution."""

from analysis.impact_attribution import (
    CONDITIONAL,
    KNOWN,
    UNRESOLVED,
    build_impact_assessment,
)
from analysis.incremental_dependency import (
    AffectedNode,
    PropagationPath,
    PropagationResult,
)
from model.business_context import BusinessContext


def _propagation(status_node="app-2", depth=1):
    path = PropagationPath(
        origin_dependency_id="dep-1",
        node_ids=("app-1", status_node),
        dependency_ids=("dep-1",),
        evidence_ids=("ev-dep",),
    )
    return PropagationResult(
        affected_nodes=(
            AffectedNode(
                node_id=status_node,
                depth=depth,
                origin_dependency_ids=("dep-1",),
                paths=(path,),
            ),
        ),
        paths=(path,),
    )


def test_known_context_produces_known_attribution():
    context = BusinessContext(
        context_id="ctx-1",
        application_id="app-2",
        operational_criticality="CRITICAL",
        source="declared",
        confidence="high",
        evidence_ids=["ev-business"],
    )

    result = build_impact_assessment(
        _propagation(),
        [context],
        root_node_ids=["app-1"],
    )

    item = result.attributions[0]
    assert item.impact_status == KNOWN
    assert item.impact_type == "INDIRECT"
    assert item.business_consequence == "CRITICAL"
    assert item.evidence_ids == ("ev-dep",)
    assert item.business_evidence_ids == ("ev-business",)


def test_missing_business_context_is_unresolved_not_known():
    result = build_impact_assessment(
        _propagation(),
        [],
        root_node_ids=["app-1"],
    )

    item = result.attributions[0]
    assert item.impact_status == UNRESOLVED
    assert item.business_consequence == "UNRESOLVED"
    assert result.unresolved_count == 1
    assert result.known_count == 0


def test_unresolved_business_context_is_not_promoted_to_known():
    context = BusinessContext(
        context_id="ctx-1",
        application_id="app-2",
        source="unresolved",
        confidence="low",
        evidence_ids=[],
    )

    result = build_impact_assessment(_propagation(), [context])

    assert result.attributions[0].impact_status == UNRESOLVED
    assert result.known_count == 0


def test_low_confidence_context_is_conditional():
    context = BusinessContext(
        context_id="ctx-1",
        application_id="app-2",
        financial_impact="HIGH",
        source="inferred",
        confidence="low",
    )

    result = build_impact_assessment(_propagation(), [context])

    assert result.attributions[0].impact_status == CONDITIONAL
    assert result.conditional_count == 1


def test_result_is_deterministic():
    contexts = [
        BusinessContext(
            context_id="ctx-b",
            application_id="app-2",
            source="declared",
            confidence="high",
            evidence_ids=["ev-b"],
        ),
        BusinessContext(
            context_id="ctx-a",
            application_id="app-2",
            source="declared",
            confidence="high",
            evidence_ids=["ev-a"],
        ),
    ]

    first = build_impact_assessment(
        _propagation(), contexts, root_node_ids=["app-1"]
    )
    second = build_impact_assessment(
        _propagation(), list(reversed(contexts)), root_node_ids=["app-1"]
    )

    assert first.digest == second.digest
    assert first.attributions == second.attributions
