"""End-to-end dynamic scan-to-impact tests."""

from analysis.impact_pipeline import assess_scan_change
from model.dependency import Dependency


def dependency(
    dependency_id,
    source,
    target,
    *,
    evidence=(),
    confidence="high",
):
    return Dependency(
        dependency_id=dependency_id,
        source_node_id=source,
        target_node_id=target,
        relationship_type="COMPONENT_USES_LIBRARY",
        confidence=confidence,
        directness="direct",
        evidence_ids=list(evidence),
        source_type="repository_dependency_discovery",
        source_reference="requirements.txt:1",
        record_version=1,
    )


def scan_state(
    dependencies,
    *,
    business_contexts=(),
    evidence=(),
):
    return {
        "scan_id": "scan:test",
        "application_ids": ["application:payment"],
        "dependencies": list(dependencies),
        "business_contexts": list(business_contexts),
        "evidence": list(evidence),
    }


def test_dynamic_scan_change_detects_added_dependency():
    previous = scan_state([])

    current = scan_state(
        [
            dependency(
                "dep-crypto",
                "component:payment",
                "library:openssl",
                evidence=("e1",),
            )
        ]
    )

    result = assess_scan_change(previous, current)

    assert result.changed_dependency_ids == ("dep-crypto",)
    assert result.dependency_delta.added == ("dep-crypto",)
    assert result.dependency_delta.removed == ()
    assert result.dependency_delta.modified == ()


def test_dynamic_scan_change_detects_modified_dependency():
    previous = scan_state(
        [
            dependency(
                "dep-crypto",
                "component:payment",
                "library:openssl-3",
                evidence=("old",),
            )
        ]
    )

    current = scan_state(
        [
            dependency(
                "dep-crypto",
                "component:payment",
                "library:ml-kem",
                evidence=("new",),
            )
        ]
    )

    result = assess_scan_change(previous, current)

    assert result.changed_dependency_ids == ("dep-crypto",)
    assert result.dependency_delta.modified == ("dep-crypto",)


def test_dynamic_scan_change_propagates_to_real_dependants():
    previous = scan_state(
        [
            dependency(
                "dep-payment-crypto",
                "component:payment",
                "library:openssl",
                evidence=("old",),
            )
        ]
    )

    current = scan_state(
        [
            dependency(
                "dep-payment-crypto",
                "component:payment",
                "library:pqc",
                evidence=("new",),
            ),
            dependency(
                "dep-api-payment",
                "component:api",
                "component:payment",
                evidence=("e-api",),
            ),
        ]
    )

    result = assess_scan_change(previous, current)

    affected = {
        item.node_id
        for item in result.propagation_result.affected_nodes
    }

    assert "component:payment" in affected
    assert "component:api" in affected


def test_dynamic_scan_change_attributes_critical_business_context():
    previous = scan_state(
        [
            dependency(
                "dep-payment-crypto",
                "component:payment",
                "library:openssl",
                evidence=("old",),
            )
        ]
    )

    current = scan_state(
        [
            dependency(
                "dep-payment-crypto",
                "component:payment",
                "library:pqc",
                evidence=("new",),
            ),
        ],
        business_contexts=[
            {
                "context_id": "ctx-payment",
                "application_id": "component:payment",
                "operational_criticality": "CRITICAL",
                "financial_impact": "HIGH",
                "regulatory_exposure": "HIGH",
                "customer_impact": "HIGH",
                "source": "declared",
                "confidence": "high",
                "evidence_ids": ["business-e1"],
            }
        ],
    )

    result = assess_scan_change(previous, current)

    attribution = result.impact_assessment.attributions

    assert attribution
    payment = next(
        item
        for item in attribution
        if item.node_id == "component:payment"
    )

    assert payment.impact_status == "KNOWN"
    assert payment.business_consequence == "CRITICAL"
    assert payment.attribution_confidence == "high"


def test_dynamic_scan_change_is_deterministic():
    dependency_old = dependency(
        "dep-crypto",
        "component:payment",
        "library:openssl",
        evidence=("old",),
    )

    dependency_new = dependency(
        "dep-crypto",
        "component:payment",
        "library:pqc",
        evidence=("new",),
    )

    previous = scan_state([dependency_old])
    current = scan_state([dependency_new])

    first = assess_scan_change(previous, current)
    second = assess_scan_change(previous, current)

    assert first == second
    assert (
        first.impact_assessment.digest
        == second.impact_assessment.digest
    )


def test_first_scan_has_no_dynamic_impact():
    current = scan_state(
        [
            dependency(
                "dep-crypto",
                "component:payment",
                "library:openssl",
            )
        ]
    )

    result = assess_scan_change(
        scan_state([]),
        current,
    )

    assert result.changed_dependency_ids == ("dep-crypto",)


def test_unchanged_scan_produces_no_impact():
    dependency_current = dependency(
        "dep-crypto",
        "component:payment",
        "library:openssl",
        evidence=("same",),
    )

    previous = scan_state([dependency_current])
    current = scan_state([dependency_current])

    result = assess_scan_change(previous, current)

    assert result.changed_dependency_ids == ()
    assert result.dependency_delta.added == ()
    assert result.dependency_delta.removed == ()
    assert result.dependency_delta.modified == ()
    assert result.propagation_result.affected_nodes == ()
    assert result.impact_assessment.attributions == ()
