"""Conservative dependency discovery from repository source and manifests.

This module produces observed dependency facts only. It does not infer
transitive dependencies, invent business relationships, or inspect secrets.
Those concerns belong to later stages of ECDAT's evidence and decision model.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

from model.dependency import Dependency


_MANIFEST_PARSERS = {
    "requirements.txt": "python_requirements",
    "requirements-dev.txt": "python_requirements",
    "package.json": "node_package_json",
    "go.mod": "go_mod",
    "pom.xml": "maven_pom",
}

_IGNORED_DIRECTORIES = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    "vendor",
    "dist",
    "build",
    "__pycache__",
    ".venv",
    "venv",
}

_PYTHON_IMPORT_TO_PACKAGE = {
    "cryptography": "cryptography",
    "Crypto": "pycryptodome",
    "OpenSSL": "pyopenssl",
    "nacl": "pynacl",
    "ssl": "python-stdlib",
}

_CRYPTO_PACKAGE_NAMES = {
    "cryptography",
    "pycryptodome",
    "pyopenssl",
    "pynacl",
    "libsodium",
    "boringssl",
    "openssl",
    "wolfssl",
    "mbedtls",
    "bcprov",
    "bouncycastle",
    "netty-tcnative",
}


def _normalize_package_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name.strip().lower())


def _node_id(kind: str, value: str) -> str:
    return f"{kind}:{_normalize_package_name(value)}"


def _dependency_id(
    source: str,
    target: str,
    relationship_type: str,
    source_reference: str,
) -> str:
    material = "|".join((source, target, relationship_type, source_reference))
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:20]
    return f"dependency:{digest}"


def _make_dependency(
    *,
    source_node_id: str,
    target_node_id: str,
    relationship_type: str,
    confidence: str,
    source_reference: str,
    scan_id: Optional[str],
) -> Dependency:
    return Dependency(
        dependency_id=_dependency_id(
            source_node_id,
            target_node_id,
            relationship_type,
            source_reference,
        ),
        source_node_id=source_node_id,
        target_node_id=target_node_id,
        relationship_type=relationship_type,
        confidence=confidence,
        directness="direct",
        source_type="repository_dependency_discovery",
        source_reference=source_reference,
        scan_id=scan_id,
    )


def _parse_requirements(path: Path) -> Iterable[Tuple[str, str]]:
    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8", errors="replace").splitlines(),
        start=1,
    ):
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        match = re.match(r"^([A-Za-z0-9_.-]+)", line)
        if match:
            yield match.group(1), f"{path.as_posix()}:{line_number}"


def _parse_package_json(path: Path) -> Iterable[Tuple[str, str]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return

    for section in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
        values = data.get(section, {})
        if not isinstance(values, dict):
            continue
        for name in sorted(values):
            yield str(name), f"{path.as_posix()}:{section}"


def _parse_go_mod(path: Path) -> Iterable[Tuple[str, str]]:
    in_require_block = False
    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8", errors="replace").splitlines(),
        start=1,
    ):
        line = raw_line.strip()
        if line.startswith("require ("):
            in_require_block = True
            continue
        if in_require_block and line == ")":
            in_require_block = False
            continue
        if in_require_block or line.startswith("require "):
            value = line.removeprefix("require ").strip()
            if value and not value.startswith("//"):
                parts = value.split()
                if parts:
                    yield parts[0], f"{path.as_posix()}:{line_number}"


def _parse_maven_pom(path: Path) -> Iterable[Tuple[str, str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    for match in re.finditer(
        r"<groupId>\s*([^<]+)\s*</groupId>\s*<artifactId>\s*([^<]+)\s*</artifactId>",
        text,
    ):
        group_id, artifact_id = match.groups()
        if group_id == "" or artifact_id == "":
            continue
        yield f"{group_id.strip()}:{artifact_id.strip()}", path.as_posix()


def _manifest_dependencies(path: Path) -> Iterable[Tuple[str, str]]:
    parser = _MANIFEST_PARSERS.get(path.name.lower())
    if parser == "python_requirements":
        return _parse_requirements(path)
    if parser == "node_package_json":
        return _parse_package_json(path)
    if parser == "go_mod":
        return _parse_go_mod(path)
    if parser == "maven_pom":
        return _parse_maven_pom(path)
    return ()


def _python_imports(path: Path) -> Iterable[Tuple[str, str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    for line_number, line in enumerate(text.splitlines(), start=1):
        match = re.match(r"^\s*(?:from|import)\s+([A-Za-z_][\w.]*)", line)
        if not match:
            continue
        root = match.group(1).split(".")[0]
        package = _PYTHON_IMPORT_TO_PACKAGE.get(root)
        if package:
            yield package, f"{path.as_posix()}:{line_number}"


def _iter_source_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in _IGNORED_DIRECTORIES for part in path.parts):
            continue
        if path.suffix.lower() in {".py", ".pyi"}:
            yield path


def discover_repository_dependencies(
    root_path: str | Path,
    *,
    application_id: str,
    scan_id: Optional[str] = None,
) -> Tuple[Dependency, ...]:
    """Discover conservative direct dependency observations from a repository.

    Manifest declarations are high-confidence observations. Python crypto
    imports are medium-confidence observations because an import establishes
    source-level usage but does not by itself prove deployment/runtime usage.
    Only crypto-relevant packages are promoted into this first slice.
    """
    root = Path(root_path).resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError(f"Repository root is not a directory: {root_path}")

    discovered: List[Dependency] = []
    component_cache: dict[str, str] = {}

    def component_id(path: str) -> str:
        if path not in component_cache:
            component_cache[path] = f"{application_id}:component:{path}"
        return component_cache[path]

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in _IGNORED_DIRECTORIES for part in path.parts):
            continue
        parser = _MANIFEST_PARSERS.get(path.name.lower())
        if parser is None:
            continue

        try:
            observations = _manifest_dependencies(path)
            for package, reference in observations:
                try:
                    relative_reference = (
                        f"{path.relative_to(root).as_posix()}:"
                        f"{reference.rsplit(':', 1)[1]}"
                    )
                except (ValueError, IndexError):
                    relative_reference = reference

                normalized = _normalize_package_name(package)
                if not any(
                    crypto_name in normalized
                    for crypto_name in _CRYPTO_PACKAGE_NAMES
                ):
                    continue
                relative = path.relative_to(root).as_posix()
                discovered.append(
                    _make_dependency(
                        source_node_id=component_id(relative),
                        target_node_id=_node_id("library", package),
                        relationship_type="COMPONENT_USES_LIBRARY",
                        confidence="high",
                        source_reference=relative_reference,
                        scan_id=scan_id,
                    )
                )
        except OSError:
            continue

    for path in _iter_source_files(root):
        try:
            for package, reference in _python_imports(path):
                relative = path.relative_to(root).as_posix()

                try:
                    relative_reference = (
                        f"{relative}:"
                        f"{reference.rsplit(':', 1)[1]}"
                    )
                except (ValueError, IndexError):
                    relative_reference = relative

                discovered.append(
                    _make_dependency(
                        source_node_id=component_id(relative),
                        target_node_id=_node_id("library", package),
                        relationship_type="COMPONENT_USES_LIBRARY",
                        confidence="medium",
                        source_reference=relative_reference,
                        scan_id=scan_id,
                    )
                )
        except OSError:
            continue

    unique = {
        dependency.dependency_id: dependency
        for dependency in discovered
    }
    return tuple(
        sorted(
            unique.values(),
            key=lambda item: (
                item.source_node_id,
                item.target_node_id,
                item.relationship_type,
                item.source_reference or "",
                item.dependency_id,
            ),
        )
    )
