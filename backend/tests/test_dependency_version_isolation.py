"""PostgreSQL integration coverage for version-scoped dependencies."""

from datetime import datetime, timezone

from sqlalchemy import delete
from sqlalchemy.orm import Session

from model.dependency import Dependency
from persistence.database import create_database_engine
from persistence.models import NodeRecord, ScanRecord
from persistence.repositories.dependency import (
    PostgreSQLDependencyRepository,
)
from persistence.repositories.scan_version import (
    PostgreSQLScanVersionRepository,
)


SCAN_ID = "sequence-2b-isolation-test"


def make_dependency(
    dependency_id: str,
    source: str,
    target: str,
) -> Dependency:
    return Dependency(
        dependency_id=dependency_id,
        source_node_id=source,
        target_node_id=target,
        relationship_type="COMPONENT_USES_LIBRARY",
        confidence="high",
        directness="direct",
        evidence_ids=[],
        protocol=None,
        purpose=None,
        effective_from=None,
        effective_until=None,
        observed_at=datetime.now(
            timezone.utc
        ).isoformat(),
        scan_id=None,
        source_type="test",
        source_reference=f"{dependency_id}.py:1",
        record_version=1,
    )


def test_dependency_snapshots_are_version_isolated():
    engine = create_database_engine()

    with Session(engine) as session:
        session.execute(
            delete(ScanRecord).where(
                ScanRecord.scan_id == SCAN_ID
            )
        )
        session.commit()

        session.add(
            ScanRecord(
                scan_id=SCAN_ID,
                target="/tmp/ecdat-v06-isolation",
                generated_at=datetime.now(timezone.utc),
                record_version=1,
            )
        )
        session.commit()

        versions = PostgreSQLScanVersionRepository(
            session
        )

        v1 = versions.create_version(
            scan_id=SCAN_ID,
            created_at=datetime(
                2026,
                9,
                11,
                14,
                0,
                tzinfo=timezone.utc,
            ),
            summary={"dependency_count": 2},
        )

        session.flush()

        v2 = versions.create_version(
            scan_id=SCAN_ID,
            created_at=datetime(
                2026,
                9,
                11,
                15,
                0,
                tzinfo=timezone.utc,
            ),
            summary={"dependency_count": 2},
        )

        session.flush()

        node_ids = [
            "component:a",
            "library:crypto",
            "component:b",
            "library:tls",
            "component:c",
            "library:pqc",
        ]

        session.add_all(
            [
                NodeRecord(
                    node_id=node_id,
                    node_type=node_id.split(":", 1)[0],
                    display_name=node_id,
                    attributes={},
                    record_version=1,
                )
                for node_id in node_ids
            ]
        )

        session.flush()

        dependencies = PostgreSQLDependencyRepository(
            session
        )

        dependency_a = make_dependency(
            "sequence-2b-dependency-a",
            "component:a",
            "library:crypto",
        )

        dependency_b = make_dependency(
            "sequence-2b-dependency-b",
            "component:b",
            "library:tls",
        )

        dependency_c = make_dependency(
            "sequence-2b-dependency-c",
            "component:c",
            "library:pqc",
        )

        dependencies.save_dependencies(
            [dependency_a, dependency_b],
            scan_version_id=v1.scan_version_id,
        )

        dependencies.save_dependencies(
            [dependency_b.__class__(
                dependency_id=dependency_b.dependency_id + "-v2",
                source_node_id=dependency_b.source_node_id,
                target_node_id=dependency_b.target_node_id,
                relationship_type=dependency_b.relationship_type,
                confidence=dependency_b.confidence,
                directness=dependency_b.directness,
                evidence_ids=[],
                protocol=dependency_b.protocol,
                purpose=dependency_b.purpose,
                effective_from=dependency_b.effective_from,
                effective_until=dependency_b.effective_until,
                observed_at=dependency_b.observed_at,
                scan_id=None,
                source_type=dependency_b.source_type,
                source_reference=dependency_b.source_reference,
                record_version=dependency_b.record_version,
            ), dependency_c],
            scan_version_id=v2.scan_version_id,
        )

        session.commit()

        v1_dependencies = dependencies.list_dependencies(
            scan_version_id=v1.scan_version_id
        )

        v2_dependencies = dependencies.list_dependencies(
            scan_version_id=v2.scan_version_id
        )

        assert [
            item.dependency_id
            for item in v1_dependencies
        ] == [
            dependency_a.dependency_id,
            dependency_b.dependency_id,
        ]

        assert [
            item.dependency_id
            for item in v2_dependencies
        ] == [
            dependency_b.dependency_id + "-v2",
            dependency_c.dependency_id,
        ]

        assert not {
            item.dependency_id
            for item in v1_dependencies
        } & {
            item.dependency_id
            for item in v2_dependencies
        }

        assert (
            len(v1_dependencies) == 2
        )

        assert (
            len(v2_dependencies) == 2
        )
