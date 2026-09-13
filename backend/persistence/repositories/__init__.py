"""Repository contracts and persistence implementations for ECDAT."""

from persistence.repositories.dependency_contract import (
    DependencyRepository,
)

__all__ = [
    "DependencyRepository",
]
from persistence.repositories.scan_version_contract import ScanVersionRepository
from persistence.repositories.scan_version import PostgreSQLScanVersionRepository
