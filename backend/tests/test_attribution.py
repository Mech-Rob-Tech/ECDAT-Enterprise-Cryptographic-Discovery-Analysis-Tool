from analysis.attribution import AttributionPath, AttributionRelation
from analysis.incremental_dependency import PropagationPath


def test_attribution_path_is_deterministic():
    path_a = AttributionPath(
        root_node_id="crypto:rsa",
        affected_node_id="application:payments",
        dependency_ids=("d2", "d1", "d2"),
        relationship_ids=("r2", "r1"),
        evidence_ids=("e3", "e1", "e3"),
        depth=3,
    )

    path_b = AttributionPath(
        root_node_id="crypto:rsa",
        affected_node_id="application:payments",
        dependency_ids=("d1", "d2"),
        relationship_ids=("r1", "r2"),
        evidence_ids=("e1", "e3"),
        depth=3,
    )

    assert path_a == path_b


def test_attribution_path_is_derived_from_propagation_path():
    propagation_path = PropagationPath(
        origin_dependency_id="d-origin",
        node_ids=(
            "crypto:rsa",
            "component:openssl",
            "application:payments",
        ),
        dependency_ids=("d2", "d1"),
        evidence_ids=("e2", "e1"),
    )

    attribution = AttributionPath.from_propagation_path(
        propagation_path,
        relationship_ids=("r2", "r1"),
    )

    assert attribution.root_node_id == "crypto:rsa"
    assert attribution.affected_node_id == "application:payments"
    assert attribution.depth == 2
    assert attribution.dependency_ids == ("d1", "d2")
    assert attribution.relationship_ids == ("r1", "r2")
    assert attribution.evidence_ids == ("e1", "e2")


def test_attribution_path_canonical_bytes_are_stable():
    path = AttributionPath(
        root_node_id="crypto:rsa",
        affected_node_id="application:payments",
        dependency_ids=("d1",),
        relationship_ids=("r1",),
        evidence_ids=("e1",),
        depth=2,
    )

    assert path.canonical_bytes() == (
        b"crypto:rsa|application:payments|2|d1|r1|e1"
    )


def test_empty_propagation_path_is_rejected():
    class EmptyPath:
        node_ids = ()
        dependency_ids = ()
        evidence_ids = ()

    try:
        AttributionPath.from_propagation_path(EmptyPath())
    except ValueError as exc:
        assert "at least one node" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_attribution_relation_preserves_observed_vs_derived():
    observed = AttributionRelation(
        relation_id="r1",
        relation_type="DEPENDS_ON",
        source_id="service:a",
        target_id="crypto:rsa",
        derivation="observed",
        origin_dependency_ids=("d2", "d1"),
        evidence_ids=("e2", "e1"),
        confidence="high",
    )

    derived = AttributionRelation(
        relation_id="r2",
        relation_type="IMPACTS",
        source_id="crypto:rsa",
        target_id="application:payments",
        derivation="derived",
        origin_dependency_ids=("d1",),
        evidence_ids=("e1",),
        confidence="medium",
    )

    assert observed.derivation == "OBSERVED"
    assert derived.derivation == "DERIVED"
    assert observed.origin_dependency_ids == ("d1", "d2")
    assert observed.evidence_ids == ("e1", "e2")


def test_attribution_relation_rejects_unknown_derivation():
    try:
        AttributionRelation(
            relation_id="r1",
            relation_type="IMPACTS",
            source_id="a",
            target_id="b",
            derivation="guessed",
        )
    except ValueError as exc:
        assert "OBSERVED or DERIVED" in str(exc)
    else:
        raise AssertionError("expected ValueError")
