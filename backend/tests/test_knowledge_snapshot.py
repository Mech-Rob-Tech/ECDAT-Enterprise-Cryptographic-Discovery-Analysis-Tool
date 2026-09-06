from knowledge.service import KnowledgeService
from analysis.report_builder import build_report


def test_knowledge_service_snapshot_has_identity():
    snapshot = KnowledgeService().snapshot()

    assert snapshot["knowledge_version"]
    assert snapshot["knowledge_hash"]
    assert snapshot["generated_at"]


def test_report_contains_knowledge_snapshot():
    report = build_report(
        {
            "artifacts": [],
            "applications": [],
            "evidence": [],
        }
    )

    snapshot = report["knowledge_snapshot"]

    assert snapshot["knowledge_version"] == KnowledgeService().version
    assert snapshot["knowledge_hash"] == KnowledgeService().integrity_hash
    assert snapshot["generated_at"] == (
        KnowledgeService().registry.manifest.generated_at
    )


def test_scan_state_preserves_knowledge_snapshot():
    from model.scan_state_builder import build_scan_state

    report = build_report(
        {
            "artifacts": [],
            "applications": [],
            "evidence": [],
        }
    )

    state = build_scan_state(report)

    assert state.knowledge_snapshot == report["knowledge_snapshot"]
