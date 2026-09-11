import json
from pathlib import Path

from starlette.testclient import TestClient

from api import app
from storage.scan_history import HISTORY_DIR, save_scan_state


client = TestClient(app)


def make_dependency(
    dependency_id,
    source,
    target,
    relationship="COMPONENT_USES_LIBRARY",
    confidence="high",
    evidence_ids=None,
    protocol=None,
):
    return {
        "dependency_id": dependency_id,
        "source_node_id": source,
        "target_node_id": target,
        "relationship_type": relationship,
        "confidence": confidence,
        "evidence_ids": evidence_ids or [],
        "protocol": protocol,
        "purpose": None,
        "effective_from": None,
        "effective_until": None,
        "observed_at": None,
        "scan_id": None,
        "source_type": "repository_dependency_discovery",
        "source_reference": "requirements.txt:1",
        "record_version": 1,
    }


def save_fixture(scan_id, dependencies):
    save_scan_state(
        {
            "scan_id": scan_id,
            "application_ids": [],
            "generated_at": "2026-09-11T00:00:00Z",
            "target": "test-repository",
            "artifact_ids": [],
            "canonical_artifacts": [],
            "evidence": [],
            "business_contexts": [],
            "relationships": [],
            "dependencies": dependencies,
            "risk_landscape": {},
            "summary": {},
            "metadata": {},
        }
    )


def test_dependencies_requires_scan_id():
    response = client.get("/dependencies")

    assert response.status_code == 400
    assert response.json()["error"] == "scan_id is required."


def test_dependencies_returns_persisted_records():
    scan_id = "api-dependency-list"
    dependencies = [
        make_dependency(
            "dep-1",
            "component-a",
            "library-x",
        ),
        make_dependency(
            "dep-2",
            "library-x",
            "service-y",
            relationship="SERVICE_DEPENDS_ON_SERVICE",
        ),
    ]

    save_fixture(scan_id, dependencies)

    response = client.get(
        "/dependencies",
        params={"scan_id": scan_id},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["scan_id"] == scan_id
    assert payload["total"] == 2
    assert [
        item["dependency_id"]
        for item in payload["dependencies"]
    ] == ["dep-1", "dep-2"]


def test_dependency_detail_returns_one_record():
    scan_id = "api-dependency-detail"

    save_fixture(
        scan_id,
        [
            make_dependency(
                "dep-1",
                "component-a",
                "library-x",
                evidence_ids=["evidence-1"],
            ),
        ],
    )

    response = client.get(
        "/dependencies/dep-1",
        params={"scan_id": scan_id},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["scan_id"] == scan_id
    assert payload["dependency"]["dependency_id"] == "dep-1"
    assert payload["dependency"]["evidence_ids"] == [
        "evidence-1"
    ]


def test_dependency_detail_does_not_cross_scan_boundary():
    save_fixture(
        "api-scan-a",
        [
            make_dependency(
                "shared-id",
                "component-a",
                "library-a",
            ),
        ],
    )

    save_fixture(
        "api-scan-b",
        [
            make_dependency(
                "shared-id",
                "component-b",
                "library-b",
            ),
        ],
    )

    response = client.get(
        "/dependencies/shared-id",
        params={"scan_id": "api-scan-b"},
    )

    assert response.status_code == 200
    assert (
        response.json()["dependency"]["target_node_id"]
        == "library-b"
    )


def test_dependency_detail_returns_404_for_unknown_dependency():
    scan_id = "api-dependency-missing"

    save_fixture(
        scan_id,
        [
            make_dependency(
                "dep-1",
                "component-a",
                "library-x",
            ),
        ],
    )

    response = client.get(
        "/dependencies/missing",
        params={"scan_id": scan_id},
    )

    assert response.status_code == 404
    assert response.json()["error"] == "Dependency not found."


def test_dependency_endpoints_return_404_for_unknown_scan():
    response = client.get(
        "/dependencies",
        params={"scan_id": "does-not-exist"},
    )

    assert response.status_code == 404

    response = client.get(
        "/dependencies/component-a/closure",
        params={"scan_id": "does-not-exist"},
    )

    assert response.status_code == 404


def test_dependency_closure_endpoint():
    scan_id = "api-dependency-closure"

    save_fixture(
        scan_id,
        [
            make_dependency(
                "dep-1",
                "component-a",
                "library-x",
                protocol="TLS",
            ),
            make_dependency(
                "dep-2",
                "library-x",
                "service-y",
                protocol="TLS",
            ),
        ],
    )

    response = client.get(
        "/dependencies/component-a/closure",
        params={
            "scan_id": scan_id,
            "external_node_id": "service-y",
        },
    )

    assert response.status_code == 200

    closure = response.json()["closure"]

    assert closure["root_node_id"] == "component-a"
    assert closure["direct_dependencies"] == ["library-x"]
    assert closure["indirect_dependencies"] == ["service-y"]
    assert closure["external_dependencies"] == ["service-y"]
    assert closure["affected_protocols"] == ["TLS"]
    assert closure["closure_depth"] == 2


def test_dependency_paths_endpoint():
    scan_id = "api-dependency-paths"

    save_fixture(
        scan_id,
        [
            make_dependency(
                "dep-1",
                "component-a",
                "library-x",
            ),
            make_dependency(
                "dep-2",
                "library-x",
                "service-y",
            ),
        ],
    )

    response = client.get(
        "/dependencies/component-a/paths/service-y",
        params={"scan_id": scan_id},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["total"] == 1
    assert payload["paths"][0]["node_ids"] == [
        "component-a",
        "library-x",
        "service-y",
    ]


def test_dependency_migration_order_endpoint():
    scan_id = "api-dependency-migration"

    save_fixture(
        scan_id,
        [
            make_dependency(
                "dep-1",
                "application-a",
                "gateway-a",
            ),
            make_dependency(
                "dep-2",
                "gateway-a",
                "crypto-library",
            ),
        ],
    )

    response = client.get(
        "/dependencies/application-a/migration-order",
        params={"scan_id": scan_id},
    )

    assert response.status_code == 200

    assert response.json()["migration_order"] == [
        ["crypto-library"],
        ["gateway-a"],
        ["application-a"],
    ]


def test_legacy_scan_without_dependencies_is_supported():
    scan_id = "api-legacy-scan"

    save_scan_state(
        {
            "scan_id": scan_id,
            "application_ids": [],
            "generated_at": "2026-09-11T00:00:00Z",
            "target": "legacy",
            "artifact_ids": [],
            "canonical_artifacts": [],
            "evidence": [],
            "business_contexts": [],
            "relationships": [],
            "risk_landscape": {},
            "summary": {},
            "metadata": {},
        }
    )

    response = client.get(
        "/dependencies",
        params={"scan_id": scan_id},
    )

    assert response.status_code == 200
    assert response.json()["dependencies"] == []
    assert response.json()["total"] == 0
