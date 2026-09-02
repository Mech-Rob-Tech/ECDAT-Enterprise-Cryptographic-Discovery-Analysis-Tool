from scanner.crypto_scanner import scan_repository


results = scan_repository("demo_repo")


print()
print(f"Target                 : {results['target']}")
print(f"Files scanned          : {results['total_files_scanned']}")
print(f"Cryptographic artefacts: {results['total_artifacts']}")

print()
print("Risk Summary")
print("-" * 30)

for level, count in results["risk_summary"].items():
    print(f"{level.upper():10}: {count}")

print()


for finding in results["artifacts"]:

    print("=" * 70)

    print(
        f"Algorithm      : {finding['algorithm']}"
    )

    print(
        f"Type           : {finding['type']}"
    )

    print(
        f"File           : {finding['file']}"
    )

    print(
        f"Line           : {finding['line']}"
    )

    print(
        f"Evidence       : {finding['evidence']}"
    )

    if finding["details"]:
        print(
            f"Details        : {finding['details']}"
        )

    print(
        f"Quantum Risk   : {finding['quantum_risk']}"
    )

    print(
        f"Risk Reason    : {finding['risk_reason']}"
    )

    print(
        f"Recommendation : {finding['recommendation']}"
    )


print("=" * 70)