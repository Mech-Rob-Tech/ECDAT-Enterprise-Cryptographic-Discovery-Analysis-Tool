"""Scan-version repository contract for ECDAT v0.6."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Tuple

from persistence.models import ScanVersionRecord


class ScanVersionRepository(ABC):
    """Persistence contract for immutable scan versions."""

    @abstractmethod
    def create_version(
        self,
        *,
        scan_id: str,
        created_at,
        summary: Optional[dict] = None,
        metadata_payload: Optional[dict] = None,
        knowledge_snapshot: Optional[dict] = None,
    ) -> ScanVersionRecord:
        """Create the next immutable version for a scan."""

    @abstractmethod
    def get_version(
        self,
        scan_version_id: str,
    ) -> Optional[ScanVersionRecord]:
        """Return one scan version or None."""

    @abstractmethod
    def get_latest_version(
        self,
        scan_id: str,
    ) -> Optional[ScanVersionRecord]:
        """Return the latest version for a scan."""

    @abstractmethod
    def list_versions(
        self,
        scan_id: str,
    ) -> Tuple[ScanVersionRecord, ...]:
        """Return versions in deterministic ascending order."""
