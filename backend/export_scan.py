import json
from pathlib import Path

from scanner.crypto_scanner import scan_repository
from analysis.report_builder import build_report


TARGET = "demo_repo"


mosca_inputs = {
    "data_lifetime": 12,
    "migration_time": 4,
    "quantum_horizon": 10,
    "business_criticality": "Critical",
}


scan_results = scan_repository(TARGET)

report = build_report(
    scan_results,
    mosca_inputs,
)


output_directory = Path("output")
output_directory.mkdir(
    exist_ok=True
)

output_file = (
    output_directory
    / "scan_results.json"
)


with output_file.open(
    "w",
    encoding="utf-8",
) as file:
    json.dump(
        report,
        file,
        indent=2,
        ensure_ascii=False,
    )


print()
print("ECDAT scan completed.")
print(
    f"Target                  : "
    f"{report['target']}"
)
print(
    f"Files scanned           : "
    f"{report['total_files_scanned']}"
)
print(
    f"Crypto artifacts        : "
    f"{report['total_artifacts']}"
)
print(
    f"Quantum-vulnerable      : "
    f"{report['quantum_vulnerable_assets']}"
)
print(
    f"JSON report             : "
    f"{output_file}"
)
