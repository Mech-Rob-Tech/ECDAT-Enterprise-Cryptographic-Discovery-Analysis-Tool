from analysis.report_builder import build_report


def _scan_results():
    return {
        "target": "intelligence-demo",
        "total_files_scanned": 1,
        "artifacts": [
            {
                "artifact_id": "artifact:test-intelligence",
                "application_id": "app:payment",
                "algorithm": "RSA",
                "type": "cryptographic_artifact",
                "purpose": "signature",
                "security_risk": "HIGH",
                "quantum_risk": "CRITICAL",
                "risk": {
                    "security": {"level": "HIGH"},
                    "quantum": {"level": "CRITICAL"},
                },
                "details": {},
            }
        ],
        "applications": [
            {
                "application_id": "app:payment",
                "name": "payment",
                "path": "/tmp/payment",
            }
        ],
        "business_contexts": [
            {
                "context_id": "business:payment",
                "application_id": "app:payment",
                "operational_criticality": "CRITICAL",
                "financial_impact": "HIGH",
                "regulatory_exposure": "HIGH",
                "customer_impact": "HIGH",
                "confidence": "high",
            }
        ],
        "risk_summary": {},
        "quantum_vulnerable_assets": 1,
    }


def test_report_contains_deterministic_intelligence_snapshot():
    first = build_report(_scan_results())
    second = build_report(_scan_results())

    assert first["intelligence"] == second["intelligence"]
    assert len(first["intelligence"]["decisions"]) == 1
    assert len(first["intelligence"]["actions"]) == 1

    decision = first["intelligence"]["decisions"][0]
    action = first["intelligence"]["actions"][0]

    assert decision["artifact_id"] == first["canonical_artifacts"][0]["artifact_id"]
    assert decision["application_id"] == first["canonical_artifacts"][0]["application_id"]
    assert decision["business_context_ids"] == ["business:payment"]
    assert decision["decision"] == "ACTION"
    assert decision["policy_version"] == "0.8"

    assert action["decision_id"] == decision["decision_id"]
    assert action["artifact_id"] == decision["artifact_id"]
    assert action["action"] in {"MIGRATE", "REMEDIATE"}
    assert action["priority"] == "HIGH"


def test_report_intelligence_preserves_canonical_migration_linkage():
    report = build_report(_scan_results())

    decision = report["intelligence"]["decisions"][0]
    action = report["intelligence"]["actions"][0]

    migration_ids = set(decision["migration_option_ids"])
    report_migration_ids = {
        option["option_id"]
        for option in report["migration_options"]
    }

    assert migration_ids <= report_migration_ids

    if action["migration_option_id"] is not None:
        assert action["migration_option_id"] in migration_ids
