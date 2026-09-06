import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1]),
)

from starlette.testclient import TestClient
from api import app


client = TestClient(app)


def test_snapshot():
    r = client.get("/knowledge/snapshot")

    assert r.status_code == 200

    snapshot = r.json()["snapshot"]

    assert snapshot["knowledge_version"] == "0.5.0"
    assert len(snapshot["knowledge_hash"]) == 64


def test_search():
    r = client.get(
        "/knowledge",
        params={"q": "ML-KEM"},
    )

    assert r.status_code == 200

    names = {
        item["name"]
        for item in r.json()["records"]
    }

    assert "ML-KEM" in names


def test_detail():
    r = client.get("/knowledge/ML-DSA")

    assert r.status_code == 200

    assert (
        r.json()["resolution"]["algorithm"]["name"]
        == "ML-DSA"
    )


def test_unknown():
    r = client.get(
        "/knowledge/DOES-NOT-EXIST"
    )

    assert r.status_code == 404


def test_resolve_rsa_signature():
    r = client.post(
        "/knowledge/resolve",
        json={
            "query": "RSA-2048",
            "purpose": "digital_signature",
        },
    )

    assert r.status_code == 200

    body = r.json()

    assert body["resolution"]["status"] == "RESOLVED"

    targets = {
        item["target_algorithm"]
        for item in body["resolution"]["migrations"]
    }

    assert "ML-DSA" in targets


def test_resolve_tls_hybrid():
    r = client.post(
        "/knowledge/resolve",
        json={
            "query": "X25519MLKEM768",
            "target_type": "protocol",
            "target_name": "TLS 1.3",
        },
    )

    assert r.status_code == 200

    body = r.json()

    assert (
        body["resolution"]["algorithm"]["name"]
        == "X25519MLKEM768"
    )

    assert (
        body["resolution"]["compatibility"][0]["status"]
        == "supported"
    )


def test_migrations():
    r = client.get(
        "/knowledge/migrations",
        params={
            "source": "RSA",
            "purpose": "digital_signature",
        },
    )

    assert r.status_code == 200
    assert r.json()["total"] >= 1


def test_freshness():
    r = client.get(
        "/knowledge/freshness",
        params={
            "as_of": "2026-09-05",
        },
    )

    assert r.status_code == 200
    assert (
        r.json()["freshness"]["state"]
        == "fresh"
    )


def test_compatibility():
    r = client.get(
        "/knowledge/compatibility",
        params={
            "algorithm": "X25519MLKEM768",
            "target_name": "TLS 1.3",
        },
    )

    assert r.status_code == 200
    assert r.json()["total"] == 1
