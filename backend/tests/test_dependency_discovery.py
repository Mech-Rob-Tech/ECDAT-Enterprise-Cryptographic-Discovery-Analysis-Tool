from pathlib import Path

from analysis.dependency_discovery import discover_repository_dependencies


def test_discovers_crypto_dependencies_from_manifest_and_python_usage(tmp_path: Path):
    (tmp_path / "requirements.txt").write_text(
        "cryptography==45.0.0\nrequests==2.32.0\npyOpenSSL>=25\n",
        encoding="utf-8",
    )
    source = tmp_path / "service.py"
    source.write_text(
        "from cryptography.hazmat.primitives import hashes\n"
        "import ssl\n"
        "import requests\n",
        encoding="utf-8",
    )

    dependencies = discover_repository_dependencies(
        tmp_path,
        application_id="app:payments",
        scan_id="scan:001",
    )

    targets = {item.target_node_id for item in dependencies}
    assert targets == {
        "library:cryptography",
        "library:pyopenssl",
        "library:python-stdlib",
    }

    manifest = [
        item for item in dependencies
        if item.source_reference == "requirements.txt:1"
    ]
    assert len(manifest) == 1
    assert manifest[0].confidence == "high"
    assert manifest[0].source_type == "repository_dependency_discovery"
    assert manifest[0].scan_id == "scan:001"

    imports = [
        item for item in dependencies
        if item.source_reference == "service.py:1"
    ]
    assert len(imports) == 1
    assert imports[0].confidence == "medium"


def test_discovery_is_deterministic_and_ignores_build_directories(tmp_path: Path):
    (tmp_path / "requirements.txt").write_text(
        "cryptography==45.0.0\n",
        encoding="utf-8",
    )
    ignored = tmp_path / "node_modules" / "example.py"
    ignored.parent.mkdir()
    ignored.write_text(
        "from cryptography import x509\n",
        encoding="utf-8",
    )

    first = discover_repository_dependencies(
        tmp_path,
        application_id="app:test",
    )
    second = discover_repository_dependencies(
        tmp_path,
        application_id="app:test",
    )

    assert first == second
    assert len(first) == 1
    assert first[0].source_node_id == "app:test:component:requirements.txt"


def test_invalid_repository_root_is_rejected(tmp_path: Path):
    missing = tmp_path / "does-not-exist"

    try:
        discover_repository_dependencies(
            missing,
            application_id="app:test",
        )
    except ValueError as exc:
        assert "not a directory" in str(exc)
    else:
        raise AssertionError("expected ValueError")
