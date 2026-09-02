from datetime import datetime

from analysis.mosca import calculate_mosca_risk


QUANTUM_VULNERABLE_ALGORITHMS = {
    "RSA",
    "ECDSA",
    "ECDH",
    "Diffie-Hellman",
}


def build_artifact_record(
    artifact,
    mosca_inputs=None
):
    details = artifact.get("details", {})

    record = {
        "algorithm": artifact.get("algorithm"),
        "type": artifact.get("type"),

        "key_size": details.get("key_size"),
        "mode": details.get("mode"),
        "curve": details.get("curve"),
        "version": details.get("version"),

        "file": artifact.get("file"),
        "line": artifact.get("line"),
        "evidence": artifact.get("evidence"),

        "quantum_risk": artifact.get(
            "quantum_risk"
        ),

        "risk_reason": artifact.get(
            "risk_reason"
        ),

        "mosca_risk": None,
        "mosca_status": None,
        "mosca_explanation": None,

        "recommendation": artifact.get(
            "recommendation"
        ),
    }

    algorithm = artifact.get("algorithm")

    if (
        mosca_inputs
        and algorithm
        in QUANTUM_VULNERABLE_ALGORITHMS
    ):
        mosca = calculate_mosca_risk(
            data_lifetime=mosca_inputs[
                "data_lifetime"
            ],
            migration_time=mosca_inputs[
                "migration_time"
            ],
            quantum_horizon=mosca_inputs[
                "quantum_horizon"
            ],
            business_criticality=mosca_inputs[
                "business_criticality"
            ],
        )

        record["mosca_risk"] = mosca[
            "mosca_risk"
        ]

        record["mosca_status"] = mosca[
            "mosca_status"
        ]

        record["mosca_explanation"] = mosca[
            "mosca_explanation"
        ]

    return record


def build_dashboard_report(
    scan_results,
    mosca_inputs=None
):
    artifacts = []

    for artifact in scan_results["artifacts"]:
        artifacts.append(
            build_artifact_record(
                artifact,
                mosca_inputs
            )
        )

    quantum_vulnerable_count = sum(
        1
        for artifact in artifacts
        if artifact["algorithm"]
        in QUANTUM_VULNERABLE_ALGORITHMS
    )

    return {
        "target": scan_results["target"],

        "generated_at": datetime.now().isoformat(
            timespec="seconds"
        ),

        "prototype_scope": (
            "Source-code cryptographic discovery"
        ),

        "total_files_scanned": scan_results[
            "total_files_scanned"
        ],

        "total_artifacts": scan_results[
            "total_artifacts"
        ],

        "quantum_vulnerable_assets":
            quantum_vulnerable_count,

        "risk_summary": scan_results[
            "risk_summary"
        ],

        "mosca_inputs": mosca_inputs,

        "artifacts": artifacts,
    }