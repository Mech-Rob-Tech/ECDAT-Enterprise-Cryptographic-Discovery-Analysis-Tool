"""PostgreSQL scan-version repository for ECDAT v0.6."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from persistence.models import ScanVersionRecord
from persistence.repositories.scan_version_contract import (
    ScanVersionRepository,
)


class PostgreSQLScanVersionRepository(ScanVersionRepository):
    """SQLAlchemy-backed repository for immutable scan versions.

    Transaction ownership remains with the caller.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def _normalize_created_at(
        created_at: Optional[datetime],
    ) -> datetime:
        value = created_at or datetime.now(timezone.utc)

        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)

        return value

    def create_version(
        self,
        *,
        scan_id: str,
        created_at: Optional[datetime] = None,
        summary: Optional[dict] = None,
        metadata_payload: Optional[dict] = None,
        knowledge_snapshot: Optional[dict] = None,
    ) -> ScanVersionRecord:
        normalized_scan_id = str(scan_id).strip()

        if not normalized_scan_id:
            raise ValueError("scan_id is required.")

        latest = self.get_latest_version(
            normalized_scan_id
        )

        next_version = (
            latest.version_number + 1
            if latest is not None
            else 1
        )

        record = ScanVersionRecord(
            scan_version_id=(
                f"{normalized_scan_id}-v{next_version}"
            ),
            scan_id=normalized_scan_id,
            version_number=next_version,
            created_at=self._normalize_created_at(
                created_at
            ),
            summary=dict(summary or {}),
            metadata_payload=dict(
                metadata_payload or {}
            ),
            knowledge_snapshot=dict(
                knowledge_snapshot or {}
            ),
        )

        self._session.add(record)

        return record

    def get_version(
        self,
        scan_version_id: str,
    ) -> Optional[ScanVersionRecord]:
        normalized_id = str(
            scan_version_id
        ).strip()

        if not normalized_id:
            return None

        return self._session.get(
            ScanVersionRecord,
            normalized_id,
        )

    def get_latest_version(
        self,
        scan_id: str,
    ) -> Optional[ScanVersionRecord]:
        normalized_scan_id = str(
            scan_id
        ).strip()

        if not normalized_scan_id:
            return None

        statement = (
            select(ScanVersionRecord)
            .where(
                ScanVersionRecord.scan_id
                == normalized_scan_id
            )
            .order_by(
                ScanVersionRecord.version_number.desc()
            )
            .limit(1)
        )

        return self._session.scalar(statement)

    def list_versions(
        self,
        scan_id: str,
    ) -> Tuple[ScanVersionRecord, ...]:
        normalized_scan_id = str(
            scan_id
        ).strip()

        if not normalized_scan_id:
            return ()

        statement = (
            select(ScanVersionRecord)
            .where(
                ScanVersionRecord.scan_id
                == normalized_scan_id
            )
            .order_by(
                ScanVersionRecord.version_number.asc()
            )
        )

        return tuple(
            self._session.scalars(statement).all()
        )
