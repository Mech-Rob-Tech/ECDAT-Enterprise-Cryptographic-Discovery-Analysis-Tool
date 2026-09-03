from dataclasses import asdict

from model.canonical import build_canonical_scan
from model.schema import ECDATScan


def canonical_to_dict(
    scan: ECDATScan,
) -> dict:
    return asdict(scan)


__all__ = [
    "ECDATScan",
    "build_canonical_scan",
    "canonical_to_dict",
]
