from analysis.scan_diff import build_scan_diff


def make_artifact(
    artifact_id,
    algorithm,
    security_risk,
    quantum_risk,
    evidence_id,
    recommendation_id,
    migration_id,
):
    return {
        "artifact_id": artifact_id,
        "artifact_type": "algorithm",
        "algorithm": algorithm,
        "algorithm_family": None,
        "key_size": None,
        "mode": None,
        "curve": None,
        "version": None,
        "purpose": "unknown",
        "detection_method": "api_invocation",
        "application_id": "application:demo_repo",
        "component_id": None,
        "risk": {
            "security": {
                "level": security_risk,
            },
            "quantum": {
                "level": quantum_risk,
            },
        },
        "mosca": {
            "status": "NOT_AT_RISK",
            "risk": "LOW",
        },
        "recommendation_ids": [recommendation_id],
        "migration_option_ids": [migration_id],
        "evidence_ids": [evidence_id],
        "details": {},
    }


def test_line_movement_and_removal():
    tls_before = make_artifact(
        "payment_service.py:27:TLS",
        "TLS",
        "MEDIUM",
        "MEDIUM",
        "evidence:payment_service.py:27:TLS",
        "recommendation:payment_service.py:27:TLS:inspect",
        "migration:payment_service.py:27:TLS:PQC / hybrid TLS",
    )

    md5_before = make_artifact(
        "payment_service.py:23:MD5",
        "MD5",
        "CRITICAL",
        "LOW",
        "evidence:payment_service.py:23:MD5",
        "recommendation:payment_service.py:23:MD5:replace",
        "migration:payment_service.py:23:MD5:SHA-256",
    )

    tls_after = make_artifact(
        "payment_service.py:23:TLS",
        "TLS",
        "MEDIUM",
        "MEDIUM",
        "evidence:payment_service.py:23:TLS",
        "recommendation:payment_service.py:23:TLS:inspect",
        "migration:payment_service.py:23:TLS:PQC / hybrid TLS",
    )

    from_scan = {
        "scan_id": "scan-A",
        "canonical_artifacts": [
            tls_before,
            md5_before,
        ],
    }

    to_scan = {
        "scan_id": "scan-B",
        "canonical_artifacts": [
            tls_after,
        ],
    }

    result = build_scan_diff(
        from_scan,
        to_scan,
    )

    assert len(result["added_artifact_ids"]) == 0
    assert len(result["removed_artifact_ids"]) == 1
    assert "MD5" in result["removed_artifact_ids"][0]

    assert len(result["changed_artifact_ids"]) == 0

    assert len(result["risk_increased"]) == 0
    assert len(result["risk_decreased"]) == 0
    assert len(result["mosca_changed"]) == 0

    assert len(result["recommendation_changed"]) == 0
    assert len(result["migration_changed"]) == 0

    assert len(result["evidence_relocated"]) == 1
    assert len(result["evidence_changed"]) == 0

    relocation = result["evidence_relocated"][0]

    assert relocation["from_artifact_id"] == (
        "payment_service.py:27:TLS"
    )
    assert relocation["to_artifact_id"] == (
        "payment_service.py:23:TLS"
    )

    print("PASS: Semantic temporal diff regression test.")


if __name__ == "__main__":
    test_line_movement_and_removal()
