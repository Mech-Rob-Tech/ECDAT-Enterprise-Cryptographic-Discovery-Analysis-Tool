import json
from pathlib import Path

from scanner.crypto_scanner import scan_repository
from analysis.report_builder import build_report
from model.canonical import build_canonical_scan
from model.validation import validate_canonical_scan


DEMO_ROOT = (
    Path(__file__).resolve().parents[2]
    / "demo"
    / "intelligence-repository"
)


def _real_demo_scan():
    scan = scan_repository(DEMO_ROOT)

    context_file = DEMO_ROOT / "ecdat-business-context.json"
    context = json.loads(context_file.read_text())

    scan["business_contexts"] = context["business_contexts"]

    return scan


def _intelligence_projection(report):
    return {
        "decisions": report["intelligence"]["decisions"],
        "actions": report["intelligence"]["actions"],
    }


def test_real_demo_exercises_full_backend_pipeline():
    scan = _real_demo_scan()

    # v0.5 — canonical model + graph validation
    canonical = build_canonical_scan(scan)

    validation_errors = validate_canonical_scan(canonical)

    assert validation_errors == []
    assert len(canonical.artifacts) == len(scan["artifacts"])
    assert len(canonical.business_contexts) == 1

    # v0.6 — dependency discovery
    assert len(canonical.dependencies) > 0

    # v0.7/v0.8 — report, risk landscape, decisions, actions
    first = build_report(scan)
    second = build_report(scan)

    first_intelligence = _intelligence_projection(first)
    second_intelligence = _intelligence_projection(second)

    # Deterministic intelligence contract
    assert first_intelligence == second_intelligence

    decisions = first["intelligence"]["decisions"]
    actions = first["intelligence"]["actions"]

    assert len(decisions) == len(canonical.artifacts)
    assert len(actions) == len(canonical.artifacts)

    # v0.7 risk/MOSCA/business-impact presence
    for decision in decisions:
        assert decision["security_risk"] is not None
        assert decision["quantum_risk"] is not None
        assert decision["consequence_level"] is not None
        assert decision["business_context_ids"] == ["business:payment"]

        if decision["mosca_risk"] is not None:
            assert decision["mosca_status"] is not None

    # v0.8 DecisionRecord → ActionVector linkage
    decision_by_id = {
        decision["decision_id"]: decision
        for decision in decisions
    }

    for action in actions:
        assert action["decision_id"] in decision_by_id
        assert action["artifact_id"] == decision_by_id[
            action["decision_id"]
        ]["artifact_id"]

    # The real RSA findings must produce actionable intelligence.
    rsa_decisions = [
        decision
        for decision in decisions
        if decision["quantum_risk"] in {"HIGH", "CRITICAL"}
    ]

    assert len(rsa_decisions) >= 2

    assert all(
        decision["decision"] == "ACTION"
        for decision in rsa_decisions
    )

    rsa_actions = [
        action
        for action in actions
        if action["artifact_id"]
        in {decision["artifact_id"] for decision in rsa_decisions}
    ]

    assert all(
        action["priority"] == "HIGH"
        for action in rsa_actions
    )

    assert all(
        action["verification_required"] is True
        for action in rsa_actions
    )
