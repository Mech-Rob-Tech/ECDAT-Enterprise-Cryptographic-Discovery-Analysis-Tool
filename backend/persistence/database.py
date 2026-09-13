"""Database infrastructure for ECDAT persistence."""

from __future__ import annotations

import os
from typing import Optional

from sqlalchemy import Engine, create_engine


def get_database_url(
    value: Optional[str] = None,
) -> str:
    """Resolve the PostgreSQL URL from explicit input or environment."""

    database_url = (
        value
        or os.getenv("ECDAT_DATABASE_URL")
    )

    if not database_url:
        raise RuntimeError(
            "ECDAT_DATABASE_URL is not configured."
        )

    return database_url.strip()


def create_database_engine(
    database_url: Optional[str] = None,
) -> Engine:
    """Create the production-compatible SQLAlchemy engine."""

    return create_engine(
        get_database_url(database_url),
        future=True,
        pool_pre_ping=True,
    )
