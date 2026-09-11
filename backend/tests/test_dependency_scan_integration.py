from pathlib import Path

from model.canonical import build_canonical_scan


def test_canonical_scan_contains_repository_dependencies(
    tmp_path: Path,
):
    repository = tmp_path / "sample-repository"
    repository.mkdir()

    (repository / "requirements.txt").write_text(
        "cryptography==45.0.0\n"
        "requests==2.32.0\n",
        encoding="utf-8",
    )

    (repository / "crypto.py").write_text(
        "from cryptography.hazmat.primitives import hashes\n",
        encoding="utf-8",
    )

    scan = build_canonical_scan(
        {
            "target": str(repository),
            "total_files_scanned": 2,
            "artifacts": [],
            "risk_summary": {},
            "quantum_vulnerable_assets": 0,
        }
    )

    assert scan.dependencies

    targets = {
        dependency.target_node_id
        for dependency in scan.dependencies
    }

    assert "library:cryptography" in targets

    for dependency in scan.dependencies:
        assert dependency.source_node_id
        assert dependency.target_node_id
        assert (
            dependency.relationship_type
            == "COMPONENT_USES_LIBRARY"
        )
        assert (
            dependency.source_type
            == "repository_dependency_discovery"
        )
        assert dependency.source_reference
