from pathlib import Path

from analysis.report_builder import build_report


DEMO_ROOT = (
    Path(__file__).resolve().parents[2]
    / "demo"
    / "intelligence-repository"
)


def _demo_scan_results():
    return {
        "target": str(DEMO_ROOT),
        "total_files_scanned": 2,
        "artifacts": [
            {
                "artifact_id": "artifact:demo-rsa",
                "application_id": "application:intelligence-repository",
                "algorithm": "RSA",
                "type": "cryptographic_artifact",
                "purpose": "signature",
                "security_risk": "HIGH",
                "quantum_risk": "CRITICAL",
                "risk": {
                    "security": {"level": "HIGH"},
                    "quantum": {"level": "CRITICAL"},
                },
                "details": {
                    "key_size": 2048
                },
            }
        ],
        "applications": [
            {
                "application_id": "application:intelligence-repository",
                "name": "intelligence-repository",
                "path": str(DEMO_ROOT),
            }
        ],
        "business_contexts": [
            {
                "context_id": "business:payment",
                "application_id": "application:intelligence-repository",
                "business_unit": "Payments",
                "owner": "Payments Engineering",
                "service": "Payment Processing",
                "data_classification": "CONFIDENTIAL",
                "data_lifetime_years": 10,
                "operational_criticality": "CRITICAL",
                "financial_impact": "HIGH",
                "regulatory_exposure": "HIGH",
                "customer_impact": "HIGH",
                "risk_appetite": "LOW",
                "source": "declared",
                "confidence": "high",
            }
        ],
        "risk_summary": {},
        "quantum_vulnerable_assets": 1,
    }


def test_demo_intelligence_is_deterministic_and_business_aware():
    first = build_report(_demo_scan_results())
    second = build_report(_demo_scan_results())

    assert first["intelligence"] == second["intelligence"]

    decisions = first["intelligence"]["decisions"]
    actions = first["intelligence"]["actions"]

    assert len(decisions) == 1
    assert len(actions) == 1

    decision = decisions[0]
    action = actions[0]

    assert decision["business_context_ids"] == ["business:payment"]
    assert decision["decision"] == "ACTION"
    assert decision["policy_version"] == "0.8"

    assert action["decision_id"] == decision["decision_id"]
    assert action["action"] in {"MIGRATE", "REMEDIATE"}
    assert action["priority"] == "HIGH"
    assert action["verification_required"] is True
