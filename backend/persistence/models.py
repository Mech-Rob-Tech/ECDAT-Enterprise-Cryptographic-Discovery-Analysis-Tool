"""SQLAlchemy persistence models for ECDAT v0.6.

These models represent persisted observations and scan versions.
Derived dependency intelligence is intentionally not stored as facts.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import MetaData


NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Base metadata for ECDAT persistence."""

    metadata = MetaData(
        naming_convention=NAMING_CONVENTION,
    )


class ScanRecord(Base):
    __tablename__ = "scans"

    scan_id: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
    )
    target: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    generated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    record_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    versions: Mapped[list["ScanVersionRecord"]] = relationship(
        back_populates="scan",
        cascade="all, delete-orphan",
    )


class ScanVersionRecord(Base):
    __tablename__ = "scan_versions"

    scan_version_id: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
    )
    scan_id: Mapped[str] = mapped_column(
        ForeignKey("scans.scan_id", ondelete="CASCADE"),
        nullable=False,
    )
    version_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    summary: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )
    metadata_payload: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )
    knowledge_snapshot: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    scan: Mapped["ScanRecord"] = relationship(
        back_populates="versions",
    )

    __table_args__ = (
        UniqueConstraint(
            "scan_id",
            "version_number",
            name="uq_scan_version_number",
        ),
        Index(
            "ix_scan_versions_scan_id",
            "scan_id",
        ),
    )


class NodeRecord(Base):
    __tablename__ = "nodes"

    node_id: Mapped[str] = mapped_column(
        String(512),
        primary_key=True,
    )
    node_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    display_name: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    attributes: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )
    record_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    __table_args__ = (
        Index(
            "ix_nodes_node_type",
            "node_type",
        ),
    )


class EvidenceRecord(Base):
    __tablename__ = "evidence"

    evidence_id: Mapped[str] = mapped_column(
        String(512),
        primary_key=True,
    )
    scan_version_id: Mapped[str] = mapped_column(
        ForeignKey(
            "scan_versions.scan_version_id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    source_file: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    line_number: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    evidence_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    context: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    __table_args__ = (
        Index(
            "ix_evidence_scan_version_id",
            "scan_version_id",
        ),
    )


class DependencyRecord(Base):
    __tablename__ = "dependencies"

    dependency_id: Mapped[str] = mapped_column(
        String(512),
        primary_key=True,
    )
    scan_version_id: Mapped[str] = mapped_column(
        ForeignKey(
            "scan_versions.scan_version_id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    source_node_id: Mapped[str] = mapped_column(
        ForeignKey("nodes.node_id"),
        nullable=False,
    )
    target_node_id: Mapped[str] = mapped_column(
        ForeignKey("nodes.node_id"),
        nullable=False,
    )
    relationship_type: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )
    confidence: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="unknown",
    )
    directness: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="direct",
    )
    protocol: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
    )
    purpose: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
    )
    effective_from: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    effective_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    observed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    source_type: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        default="unknown",
    )
    source_reference: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    record_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    __table_args__ = (
        Index(
            "ix_dependencies_scan_version_id",
            "scan_version_id",
        ),
        Index(
            "ix_dependencies_source_node_id",
            "source_node_id",
        ),
        Index(
            "ix_dependencies_target_node_id",
            "target_node_id",
        ),
        Index(
            "ix_dependencies_relationship_type",
            "relationship_type",
        ),
        Index(
            "ix_dependencies_source_target",
            "source_node_id",
            "target_node_id",
        ),
    )


class DependencyEvidenceRecord(Base):
    __tablename__ = "dependency_evidence"

    dependency_id: Mapped[str] = mapped_column(
        ForeignKey(
            "dependencies.dependency_id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )
    evidence_id: Mapped[str] = mapped_column(
        ForeignKey(
            "evidence.evidence_id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    __table_args__ = (
        Index(
            "ix_dependency_evidence_evidence_id",
            "evidence_id",
        ),
    )
