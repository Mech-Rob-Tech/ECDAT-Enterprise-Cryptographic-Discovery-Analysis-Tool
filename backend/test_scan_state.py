from analysis.report_builder import build_report
from model.scan_state_builder import build_scan_state
from scanner.crypto_scanner import scan_repository


def main():
    repository = "backend/demo_repo"

    scan_results = scan_repository(
        repository
    )

    report = build_report(
        scan_results,
        mosca_inputs={
            "data_lifetime": 12,
            "migration_time": 4,
            "quantum_horizon": 10,
            "business_criticality": "Critical",
        },
    )

    state = build_scan_state(
        report
    )

    assert state.scan_id
    assert state.target
    assert state.generated_at
    assert len(state.application_ids) == 1
    assert len(state.artifact_ids) == 6
    assert state.risk_landscape
    assert state.summary

    print(
        "===== SCAN STATE BUILDER TEST ====="
    )
    print(
        f"Scan ID            : {state.scan_id}"
    )
    print(
        f"Target             : {state.target}"
    )
    print(
        f"Applications       : "
        f"{len(state.application_ids)}"
    )
    print(
        f"Artifacts          : "
        f"{len(state.artifact_ids)}"
    )
    print(
        "Risk Landscape     : present"
    )
    print(
        "Summary            : present"
    )
    print(
        "PASS: ScanState projection works."
    )


if __name__ == "__main__":
    main()
