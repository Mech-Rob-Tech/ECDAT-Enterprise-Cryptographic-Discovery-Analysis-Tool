from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from typing import Iterable

from knowledge.schema import KnowledgeProvenance


def canonical_json(value) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


def provenance_hash(provenance: KnowledgeProvenance) -> str:
    payload = {
        "source_id": provenance.source_id,
        "source_type": provenance.source_type,
        "authority": provenance.authority,
        "title": provenance.title,
        "uri": provenance.uri,
        "published_at": provenance.published_at,
        "effective_from": provenance.effective_from,
        "effective_until": provenance.effective_until,
    }
    return hashlib.sha256(
        canonical_json(payload).encode("utf-8")
    ).hexdigest()


def with_hash(
    provenance: KnowledgeProvenance,
) -> KnowledgeProvenance:
    return replace(
        provenance,
        evidence_hash=provenance_hash(provenance),
    )


def validate_provenance(
    records: Iterable[KnowledgeProvenance],
) -> None:
    seen = set()

    for record in records:
        if not record.source_id:
            raise ValueError("Provenance source_id cannot be empty.")

        if record.source_id in seen:
            raise ValueError(
                f"Duplicate provenance source_id: {record.source_id}"
            )

        if not record.authority:
            raise ValueError(
                f"Missing authority for {record.source_id}"
            )

        if not record.uri:
            raise ValueError(
                f"Missing URI for {record.source_id}"
            )

        seen.add(record.source_id)
