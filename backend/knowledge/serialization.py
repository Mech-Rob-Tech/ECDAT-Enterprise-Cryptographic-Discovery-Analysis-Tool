from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from knowledge.schema import KnowledgeRegistry


def registry_to_dict(registry: KnowledgeRegistry) -> dict:
    return asdict(registry)


def registry_to_json(
    registry: KnowledgeRegistry,
    indent: int = 2,
) -> str:
    return json.dumps(
        registry_to_dict(registry),
        indent=indent,
        sort_keys=True,
    )


def write_registry(
    registry: KnowledgeRegistry,
    path: str,
) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(
            registry_to_json(registry)
        )


def read_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)
