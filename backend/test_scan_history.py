from storage.scan_history import (
    load_scan_state,
    list_scan_states,
    save_scan_state,
)


def main():
    scan_state = {
        "scan_id": "test-scan-001",
        "generated_at": "2026-09-04T12:00:00+00:00",
        "target": "demo_repo",
        "application_ids": [
            "application:demo_repo"
        ],
        "artifact_ids": [
            "artifact:rsa",
            "artifact:ecdsa",
        ],
        "risk_landscape": {
            "version": "1.1",
            "applications": [],
            "points": [],
        },
        "summary": {
            "total_artifacts": 2,
        },
        "metadata": {
            "test": True,
        },
    }

    path = save_scan_state(
        scan_state
    )

    loaded = load_scan_state(
        "test-scan-001"
    )

    states = list_scan_states()

    assert path.exists()
    assert loaded is not None
    assert loaded["scan_id"] == "test-scan-001"
    assert len(states) >= 1

    print(
        "===== SCAN HISTORY STORAGE TEST ====="
    )
    print(
        f"Stored path       : {path}"
    )
    print(
        f"Loaded scan       : "
        f"{loaded['scan_id']}"
    )
    print(
        f"Historical scans  : "
        f"{len(states)}"
    )
    print(
        "PASS: Scan history storage works."
    )


if __name__ == "__main__":
    main()

