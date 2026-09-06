from analysis.report_builder import build_report
from model.canonical import build_canonical_scan
from knowledge.service import KnowledgeService


def _artifact():
    return {
        "artifact_id": "artifact:test-provenance",
        "algorithm": "RSA",
        "type": "cryptographic_artifact",
        "purpose": "signature",
        "risk": {
            "quantum": {
                "level": "HIGH",
            }
        },
        "details": {},
    }


def test_canonical_recommendation_preserves_knowledge_provenance():
    service = KnowledgeService()

    artifact = _artifact()

    result = build_canonical_scan(
        {
            "target": "provenance-test",
            "total_files_scanned": 1,
            "artifacts": [artifact],
            "risk_summary": {},
            "quantum_vulnerable_assets": 1,
        }
    )

    assert result.recommendations

    recommendation = result.recommendations[0]

    assert recommendation.knowledge_version == service.version
    assert recommendation.knowledge_hash == service.integrity_hash
    assert recommendation.status in {
        "RESOLVED",
        "CONFLICT",
        "UNRESOLVED",
    }

    assert isinstance(recommendation.candidate_ids, list)
    assert isinstance(recommendation.candidates, list)

    if recommendation.candidates:
        candidate = recommendation.candidates[0]

        assert candidate["relationship_id"]
        assert candidate["target_algorithm"]
        assert "relationship_type" in candidate
        assert "hybrid" in candidate


def test_report_preserves_recommendation_and_migration_provenance():
    service = KnowledgeService()

    report = build_report(
        {
            "target": "provenance-test",
            "total_files_scanned": 1,
            "artifacts": [_artifact()],
            "risk_summary": {},
            "quantum_vulnerable_assets": 1,
        }
    )

    assert report["knowledge_snapshot"]["knowledge_version"] == service.version
    assert report["knowledge_snapshot"]["knowledge_hash"] == service.integrity_hash

    recommendations = report["recommendations"]
    assert recommendations

    recommendation = recommendations[0]

    assert recommendation["knowledge_version"] == service.version
    assert recommendation["knowledge_hash"] == service.integrity_hash
    assert "candidate_ids" in recommendation
    assert "candidates" in recommendation
    assert "explainability" in recommendation

    for option in report["migration_options"]:
        assert option["knowledge_version"] == service.version
        assert option["knowledge_hash"] == service.integrity_hash
        assert option["relationship_id"]
        assert option["target_algorithm"]
