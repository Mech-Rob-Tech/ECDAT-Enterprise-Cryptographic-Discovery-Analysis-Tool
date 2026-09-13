"""PostgreSQL dependency repository for ECDAT v0.6."""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Sequence, Tuple

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from model.dependency import Dependency
from persistence.models import (
    DependencyEvidenceRecord,
    DependencyRecord,
)
from persistence.repositories.dependency_contract import DependencyRepository


class PostgreSQLDependencyRepository(DependencyRepository):
    """SQLAlchemy-backed repository for observed dependency facts.

    Transaction ownership deliberately remains outside this repository.
    Callers provide the Session and control commit/rollback boundaries.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None

        if isinstance(value, datetime):
            return value

        normalized = str(value).replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)

    @staticmethod
    def _format_datetime(
        value: Optional[datetime],
    ) -> Optional[str]:
        if value is None:
            return None

        return value.isoformat()

    def _to_domain(
        self,
        record: DependencyRecord,
        evidence_ids: Sequence[str],
    ) -> Dependency:
        return Dependency(
            dependency_id=record.dependency_id,
            source_node_id=record.source_node_id,
            target_node_id=record.target_node_id,
            relationship_type=record.relationship_type,
            confidence=record.confidence,
            directness=record.directness,
            evidence_ids=list(
                sorted(set(evidence_ids))
            ),
            protocol=record.protocol,
            purpose=record.purpose,
            effective_from=self._format_datetime(
                record.effective_from
            ),
            effective_until=self._format_datetime(
                record.effective_until
            ),
            observed_at=self._format_datetime(
                record.observed_at
            ),
            scan_id=record.scan_version_id,
            source_type=record.source_type,
            source_reference=record.source_reference,
            record_version=record.record_version,
        )

    def list_dependencies(
        self,
        *,
        scan_version_id: Optional[str] = None,
        source_node_id: Optional[str] = None,
        target_node_id: Optional[str] = None,
        relationship_type: Optional[str] = None,
    ) -> Tuple[Dependency, ...]:
        statement = select(DependencyRecord)

        if scan_version_id is not None:
            statement = statement.where(
                DependencyRecord.scan_version_id
                == scan_version_id
            )

        if source_node_id is not None:
            statement = statement.where(
                DependencyRecord.source_node_id
                == source_node_id
            )

        if target_node_id is not None:
            statement = statement.where(
                DependencyRecord.target_node_id
                == target_node_id
            )

        if relationship_type is not None:
            statement = statement.where(
                DependencyRecord.relationship_type
                == relationship_type
            )

        statement = statement.order_by(
            DependencyRecord.source_node_id,
            DependencyRecord.target_node_id,
            DependencyRecord.relationship_type,
            DependencyRecord.dependency_id,
        )

        records = self._session.scalars(statement).all()

        if not records:
            return ()

        dependency_ids = [
            record.dependency_id
            for record in records
        ]

        evidence_statement = select(
            DependencyEvidenceRecord
        ).where(
            DependencyEvidenceRecord.dependency_id.in_(
                dependency_ids
            )
        )

        evidence_records = self._session.scalars(
            evidence_statement
        ).all()

        evidence_by_dependency = {}

        for item in evidence_records:
            evidence_by_dependency.setdefault(
                item.dependency_id,
                [],
            ).append(item.evidence_id)

        return tuple(
            self._to_domain(
                record,
                evidence_by_dependency.get(
                    record.dependency_id,
                    [],
                ),
            )
            for record in records
        )

    def get_dependency(
        self,
        dependency_id: str,
    ) -> Optional[Dependency]:
        record = self._session.get(
            DependencyRecord,
            dependency_id,
        )

        if record is None:
            return None

        evidence_records = self._session.scalars(
            select(
                DependencyEvidenceRecord
            ).where(
                DependencyEvidenceRecord.dependency_id
                == dependency_id
            )
        ).all()

        return self._to_domain(
            record,
            [
                item.evidence_id
                for item in evidence_records
            ],
        )

    def save_dependencies(
        self,
        dependencies: Sequence[Dependency],
        *,
        scan_version_id: str,
    ) -> None:
        for dependency in dependencies:
            existing = self._session.get(
                DependencyRecord,
                dependency.dependency_id,
            )

            if existing is not None:
                raise ValueError(
                    "Dependency already exists: "
                    + dependency.dependency_id
                )

            record = DependencyRecord(
                dependency_id=dependency.dependency_id,
                scan_version_id=scan_version_id,
                source_node_id=dependency.source_node_id,
                target_node_id=dependency.target_node_id,
                relationship_type=dependency.relationship_type,
                confidence=dependency.confidence,
                directness=dependency.directness,
                protocol=dependency.protocol,
                purpose=dependency.purpose,
                effective_from=self._parse_datetime(
                    dependency.effective_from
                ),
                effective_until=self._parse_datetime(
                    dependency.effective_until
                ),
                observed_at=self._parse_datetime(
                    dependency.observed_at
                ),
                source_type=dependency.source_type,
                source_reference=dependency.source_reference,
                record_version=dependency.record_version,
            )

            self._session.add(record)

            for evidence_id in sorted(
                set(dependency.evidence_ids)
            ):
                self._session.add(
                    DependencyEvidenceRecord(
                        dependency_id=dependency.dependency_id,
                        evidence_id=evidence_id,
                    )
                )

    def delete_scan_version_dependencies(
        self,
        scan_version_id: str,
    ) -> None:
        dependency_ids = self._session.scalars(
            select(
                DependencyRecord.dependency_id
            ).where(
                DependencyRecord.scan_version_id
                == scan_version_id
            )
        ).all()

        if dependency_ids:
            self._session.execute(
                delete(
                    DependencyEvidenceRecord
                ).where(
                    DependencyEvidenceRecord.dependency_id.in_(
                        dependency_ids
                    )
                )
            )

        self._session.execute(
            delete(DependencyRecord).where(
                DependencyRecord.scan_version_id
                == scan_version_id
            )
        )
