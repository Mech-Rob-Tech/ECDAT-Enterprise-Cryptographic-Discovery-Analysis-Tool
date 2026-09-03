from scanner.crypto_scanner import scan_repository
from model.canonical import build_canonical_scan
from model.validation import validate_canonical_scan


def main():
    target = "demo_repo"

    scan_results = scan_repository(target)

    canonical = build_canonical_scan(
        scan_results
    )

    print("===== PHASE 2D GRAPH VALIDATION =====")

    print(
        f"Applications       : "
        f"{len(canonical.applications)}"
    )

    print(
        f"Components         : "
        f"{len(canonical.components)}"
    )

    print(
        f"Artifacts          : "
        f"{len(canonical.artifacts)}"
    )

    print(
        f"Evidence           : "
        f"{len(canonical.evidence)}"
    )

    print(
        f"Relationships      : "
        f"{len(canonical.relationships)}"
    )

    print(
        f"Risk assessments   : "
        f"{len(canonical.risk_assessments)}"
    )

    print(
        f"MOSCA assessments  : "
        f"{len(canonical.mosca_assessments)}"
    )

    print(
        f"Recommendations    : "
        f"{len(canonical.recommendations)}"
    )

    print(
        f"Migration options  : "
        f"{len(canonical.migration_options)}"
    )

    print(
        f"Verification states: "
        f"{len(canonical.verification)}"
    )

    errors = validate_canonical_scan(
        canonical
    )

    print()
    print("===== VALIDATION =====")

    if errors:
        print(
            f"FAIL: {len(errors)} validation error(s)"
        )

        for index, error in enumerate(
            errors,
            start=1,
        ):
            print(
                f"{index:02d}. {error}"
            )

        raise SystemExit(1)

    print(
        "PASS: Canonical graph is structurally valid."
    )


if __name__ == "__main__":
    main()
