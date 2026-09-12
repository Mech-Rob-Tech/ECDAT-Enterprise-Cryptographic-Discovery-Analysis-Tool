from starlette.testclient import TestClient

import ai.api as ai_api

from api import app


client = TestClient(app)


def build_report():
    return {
        "summary": {
            "total_artifacts": 1,
        },
        "canonical_artifacts": [
            {
                "artifact_id": "artifact:rsa",
                "algorithm": "RSA",
                "application_id": (
                    "application:test"
                ),
                "component_id": (
                    "component:auth"
                ),
                "evidence_ids": [
                    "evidence:rsa"
                ],
                "recommendation_ids": [],
                "migration_option_ids": [],
                "verification_id": None,
            }
        ],
        "evidence": [
            {
                "evidence_id": "evidence:rsa",
                "file": "auth.py",
                "line": 10,
                "text": "RSA usage",
            }
        ],
        "recommendations": [],
        "migration_options": [],
        "relationships": [],
        "business_contexts": [],
        "metadata": {},
    }


def valid_payload():
    return {
        "answer": (
            "RSA usage was detected."
        ),
        "confidence": "high",
        "evidence_refs": [
            {
                "reference_id": (
                    "artifact:rsa"
                ),
                "reference_type": (
                    "artifact"
                ),
                "source": None,
                "description": None,
            }
        ],
        "assumptions": [],
        "missing_context": [],
        "advisory_only": True,
    }


class FakeProvider:
    provider_name = "groq"
    model_name = "fake-model"

    def __init__(
        self,
        payload=None,
    ):
        self.payload = (
            payload
            or valid_payload()
        )

    def generate_structured(
        self,
        **kwargs,
    ):
        return self.payload


def test_ai_query_returns_grounded_response(
    monkeypatch,
):
    monkeypatch.setattr(
        ai_api,
        "create_ai_provider",
        lambda: FakeProvider(),
    )

    response = client.post(
        "/ai/query",
        json={
            "question": (
                "What was detected?"
            ),
            "scan_id": "scan:test",
            "artifact_id": "artifact:rsa",
            "report": build_report(),
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert (
        body["projection"]
        == "ai_query"
    )

    assert (
        body["response"][
            "advisory_only"
        ]
        is True
    )


def test_ai_query_requires_question():
    response = client.post(
        "/ai/query",
        json={
            "scan_id": "scan:test",
            "report": build_report(),
        },
    )

    assert response.status_code == 400


def test_ai_request_requires_scan_or_report():
    response = client.post(
        "/ai/query",
        json={
            "question": "Explain."
        },
    )

    assert response.status_code == 400


def test_ai_missing_scan_returns_404(
    monkeypatch,
):
    monkeypatch.setattr(
        ai_api,
        "load_scan_state",
        lambda scan_id: None,
    )

    response = client.post(
        "/ai/query",
        json={
            "question": "Explain.",
            "scan_id": "scan:missing",
        },
    )

    assert response.status_code == 404


def test_ai_rejects_invalid_audience():
    response = client.post(
        "/ai/query",
        json={
            "question": "Explain.",
            "scan_id": "scan:test",
            "report": build_report(),
            "audience": "space_wizard",
        },
    )

    assert response.status_code == 400


def test_ai_rejects_hallucinated_reference(
    monkeypatch,
):
    payload = valid_payload()

    payload["evidence_refs"][0][
        "reference_id"
    ] = "artifact:invented"

    monkeypatch.setattr(
        ai_api,
        "create_ai_provider",
        lambda: FakeProvider(
            payload
        ),
    )

    response = client.post(
        "/ai/query",
        json={
            "question": "Explain.",
            "scan_id": "scan:test",
            "artifact_id": "artifact:rsa",
            "report": build_report(),
        },
    )

    assert response.status_code == 502


def test_ai_summary_has_default_question(
    monkeypatch,
):
    monkeypatch.setattr(
        ai_api,
        "create_ai_provider",
        lambda: FakeProvider(),
    )

    response = client.post(
        "/ai/summary",
        json={
            "scan_id": "scan:test",
            "report": build_report(),
        },
    )

    assert response.status_code == 200

    assert (
        response.json()["projection"]
        == "ai_summary"
    )