"""API-level tests for historical scan-to-impact analysis."""

import json

from starlette.testclient import TestClient

import api
from model.dependency import Dependency


client = TestClient(api.app)


def _dependency(
    dependency_id,
    source,
    target,
    *,
    evidence_ids=(),
):
    return Dependency(
        dependency_id=dependency_id,
        source_node_id=source,
        target_node_id=target,
        relationship_type="COMPONENT_USES_LIBRARY",
        confidence="high",
        directness="direct",
        evidence_ids=list(evidence_ids),
        source_type="repository_dependency_discovery",
        source_reference="requirements.txt:1",
        record_version=1,
    ).__dict__


def _scan(
    scan_id,
    dependencies,
    *,
    business_contexts=(),
    evidence=(),
):
    return {
        "scan_id": scan_id,
        "application_ids": ["application:payment"],
        "generated_at": scan_id,
        "target": "/tmp/payment",
        "artifact_ids": [],
        "canonical_artifacts": [],
        "evidence": list(evidence),
        "business_contexts": list(business_contexts),
        "relationships": [],
        "dependencies": list(dependencies),
        "risk_landscape": {},
        "summary": {},
        "metadata": {},
    }


def test_impact_api_compares_historical_scan_states(
    monkeypatch,
):
    states = {
        "scan-a": _scan(
            "scan-a",
            [
                _dependency(
                    "dep-payment",
                    "component:payment",
                    "library:openssl",
                    evidence_ids=("e-old",),
                )
            ],
        ),
        "scan-b": _scan(
            "scan-b",
            [
                _dependency(
                    "dep-payment",
                    "component:payment",
                    "library:pqc",
                    evidence_ids=("e-new",),
                )
            ],
            business_contexts=[
                {
                    "context_id": "ctx-payment",
                    "application_id": "component:payment",
                    "operational_criticality": "CRITICAL",
                    "financial_impact": "HIGH",
                    "regulatory_exposure": "HIGH",
                    "customer_impact": "HIGH",
                    "source": "declared",
                    "confidence": "high",
                    "evidence_ids": ["business-e1"],
                }
            ],
            evidence=[
                {
                    "evidence_id": "e-new",
                    "text": "PQC dependency observed",
                    "file": "requirements.txt",
                    "line": 1,
                }
            ],
        ),
    }

    monkeypatch.setattr(
        api,
        "load_scan_state",
        states.get,
    )

    response = client.post(
        "/impact",
        json={
            "from_scan_id": "scan-a",
            "to_scan_id": "scan-b",
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["from_scan_id"] == "scan-a"
    assert payload["to_scan_id"] == "scan-b"

    assert payload["dependency_changes"] == [
        {
            "dependency_id": "dep-payment",
            "change_type": "modified",
            "affected_source_node": "component:payment",
            "affected_target_node": "library:pqc",
        }
    ]

    assert payload["dependency_delta"]["modified"] == [
        "dep-payment"
    ]

    assessment = payload["impact_assessment"]

    assert assessment["known_count"] == 1
    assert assessment["conditional_count"] == 0
    assert assessment["unresolved_count"] == 0

    payment = next(
        item
        for item in assessment["attributions"]
        if item["node_id"] == "component:payment"
    )

    assert payment["impact_status"] == "KNOWN"
    assert payment["business_consequence"] == "CRITICAL"
    assert payment["attribution_confidence"] == "high"

    assert assessment["attribution_paths"]
    assert assessment["attribution_relations"]

    relation = assessment["attribution_relations"][0]

    assert relation["relation_type"] == "IMPACTS"
    assert relation["derivation"] == "DERIVED"
    assert relation["source_id"] == "library:pqc"
    assert relation["target_id"] == "component:payment"


def test_impact_api_returns_404_for_missing_source_scan(
    monkeypatch,
):
    monkeypatch.setattr(
        api,
        "load_scan_state",
        lambda scan_id: None,
    )

    response = client.post(
        "/impact",
        json={
            "from_scan_id": "missing",
            "to_scan_id": "scan-b",
        },
    )

    assert response.status_code == 404


def test_impact_api_returns_404_for_missing_target_scan(
    monkeypatch,
):
    states = {
        "scan-a": _scan(
            "scan-a",
            [],
        )
    }

    monkeypatch.setattr(
        api,
        "load_scan_state",
        states.get,
    )

    response = client.post(
        "/impact",
        json={
            "from_scan_id": "scan-a",
            "to_scan_id": "missing",
        },
    )

    assert response.status_code == 404


def test_impact_api_requires_both_scan_ids():
    response = client.post(
        "/impact",
        json={
            "from_scan_id": "scan-a",
        },
    )

    assert response.status_code == 400


def test_impact_api_is_deterministic(
    monkeypatch,
):
    states = {
        "scan-a": _scan(
            "scan-a",
            [
                _dependency(
                    "dep-payment",
                    "component:payment",
                    "library:openssl",
                )
            ],
        ),
        "scan-b": _scan(
            "scan-b",
            [
                _dependency(
                    "dep-payment",
                    "component:payment",
                    "library:pqc",
                )
            ],
        ),
    }

    monkeypatch.setattr(
        api,
        "load_scan_state",
        states.get,
    )

    request = {
        "from_scan_id": "scan-a",
        "to_scan_id": "scan-b",
    }

    first = client.post(
        "/impact",
        json=request,
    )

    second = client.post(
        "/impact",
        json=request,
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()
