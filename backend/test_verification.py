from analysis.verification import (
    build_verification,
    verification_to_dict,
)


def artifact(
    artifact_id,
    algorithm,
    security,
    quantum,
    mosca_status,
    evidence_id,
):
    return {
        "artifact_id": artifact_id,
        "artifact_type": "algorithm",
        "algorithm": algorithm,
        "algorithm_family": None,
        "application_id": "application:test",
        "component_id": "component:test",
        "risk": {
            "security": {
                "level": security,
            },
            "quantum": {
                "level": quantum,
            },
        },
        "mosca": {
            "status": mosca_status,
            "risk": "HIGH"
            if mosca_status == "AT_RISK"
            else "LOW",
        },
        "evidence_ids": [
            evidence_id
        ],
        "recommendation_ids": [],
        "migration_option_ids": [],
    }


def test_verified_when_vulnerable_artifact_disappears():
    before_artifact = artifact(
        "artifact:rsa",
        "RSA",
        "HIGH",
        "HIGH",
        "AT_RISK",
        "evidence:rsa:1",
    )

    from_scan = {
        "scan_id": "scan:A",
        "canonical_artifacts": [
            before_artifact,
        ],
    }

    to_scan = {
        "scan_id": "scan:B",
        "canonical_artifacts": [],
    }

    diff = {
        "removed_artifact_ids": [
            "artifact:rsa",
        ],
    }

    result = build_verification(
        from_scan,
        to_scan,
        diff,
        "artifact:rsa",
    )

    assert result.status == "VERIFIED"
    assert result.risk_before == "HIGH"
    assert result.risk_after == "ABSENT"
    assert result.mosca_before == "AT_RISK"
    assert result.mosca_after == "ABSENT"

    print(
        "PASS: Verification succeeds when "
        "vulnerable artifact disappears."
    )


def test_verified_when_risk_improves():
    before_artifact = artifact(
        "artifact:rsa",
        "RSA",
        "HIGH",
        "HIGH",
        "AT_RISK",
        "evidence:rsa:1",
    )

    after_artifact = artifact(
        "artifact:replacement",
        "ML-KEM",
        "LOW",
        "LOW",
        "NOT_AT_RISK",
        "evidence:mlkem:1",
    )

    from_scan = {
        "scan_id": "scan:A",
        "canonical_artifacts": [
            before_artifact,
        ],
    }

    to_scan = {
        "scan_id": "scan:B",
        "canonical_artifacts": [
            after_artifact,
        ],
    }

    diff = {
        "removed_artifact_ids": [
            "artifact:rsa",
        ],
        "added_artifact_ids": [
            "artifact:replacement",
        ],
    }

    result = build_verification(
        from_scan,
        to_scan,
        diff,
        "artifact:rsa",
        replacement_artifact_id="artifact:replacement",
    )

    assert result.status == "VERIFIED"
    assert result.risk_before == "HIGH"
    assert result.risk_after == "LOW"
    assert result.mosca_before == "AT_RISK"
    assert result.mosca_after == "NOT_AT_RISK"

    print(
        "PASS: Verification succeeds when "
        "replacement materially improves risk."
    )


def test_failed_when_exposure_remains():
    before_artifact = artifact(
        "artifact:rsa",
        "RSA",
        "HIGH",
        "HIGH",
        "AT_RISK",
        "evidence:rsa:1",
    )

    after_artifact = artifact(
        "artifact:rsa",
        "RSA",
        "HIGH",
        "HIGH",
        "AT_RISK",
        "evidence:rsa:2",
    )

    from_scan = {
        "scan_id": "scan:A",
        "canonical_artifacts": [
            before_artifact,
        ],
    }

    to_scan = {
        "scan_id": "scan:B",
        "canonical_artifacts": [
            after_artifact,
        ],
    }

    diff = {}

    result = build_verification(
        from_scan,
        to_scan,
        diff,
        "artifact:rsa",
    )

    assert result.status == "FAILED"
    assert result.risk_before == "HIGH"
    assert result.risk_after == "HIGH"
    assert "risk remains HIGH" in result.remaining_exposure

    print(
        "PASS: Verification fails when "
        "cryptographic exposure remains."
    )


def test_serialization():
    before_artifact = artifact(
        "artifact:rsa",
        "RSA",
        "HIGH",
        "HIGH",
        "AT_RISK",
        "evidence:rsa:1",
    )

    from_scan = {
        "scan_id": "scan:A",
        "canonical_artifacts": [
            before_artifact,
        ],
    }

    to_scan = {
        "scan_id": "scan:B",
        "canonical_artifacts": [],
    }

    result = build_verification(
        from_scan,
        to_scan,
        {},
        "artifact:rsa",
        migration_option_id="migration:rsa:replacement",
    )

    serialized = verification_to_dict(result)

    assert serialized["status"] == "VERIFIED"
    assert serialized["from_scan_id"] == "scan:A"
    assert serialized["to_scan_id"] == "scan:B"
    assert serialized["migration_option_id"] == (
        "migration:rsa:replacement"
    )

    print(
        "PASS: Verification serialization."
    )


if __name__ == "__main__":
    test_verified_when_vulnerable_artifact_disappears()
    test_verified_when_risk_improves()
    test_failed_when_exposure_remains()
    test_serialization()

    print(
        "PASS: Verification engine regression suite."
    )
