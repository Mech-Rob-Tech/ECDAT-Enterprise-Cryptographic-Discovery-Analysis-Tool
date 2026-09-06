import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1]),
)

from knowledge.compatibility import version_matches
from knowledge.service import KnowledgeService


def test_version_constraints():
    assert version_matches(
        "3.2",
        "3.0",
        "4.0",
    )

    assert not version_matches(
        "2.9",
        "3.0",
        "4.0",
    )


def test_tls_hybrid_compatibility():
    service = KnowledgeService()

    result = service.resolve(
        "X25519MLKEM768",
        target_type="protocol",
        target_name="TLS 1.3",
    )

    assert len(result.compatibility) == 1
    assert result.compatibility[0].status == "supported"
