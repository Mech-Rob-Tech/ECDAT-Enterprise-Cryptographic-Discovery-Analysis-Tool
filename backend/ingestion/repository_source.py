import io
import json
import re
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import urlparse

import requests
from starlette.datastructures import UploadFile

from scanner.crypto_scanner import scan_repository


MAX_UPLOAD_BYTES = 4_000_000
MAX_ARCHIVE_FILES = 10_000
MAX_EXTRACTED_BYTES = 50_000_000
GITHUB_HOSTS = {"github.com", "www.github.com"}


class RepositorySourceError(ValueError):
    """Raised when a repository source cannot be accepted safely."""


def _safe_relative_path(value: str) -> Path:
    raw = str(value or "").replace("\\", "/").strip()
    if not raw:
        raise RepositorySourceError("A repository file path is required.")

    path = Path(raw)
    if path.is_absolute() or ".." in path.parts:
        raise RepositorySourceError("Repository contains an unsafe file path.")

    return Path(*[part for part in path.parts if part not in {"", "."}])


def _write_limited(target: Path, chunks, limit: int) -> int:
    total = 0
    target.parent.mkdir(parents=True, exist_ok=True)

    with target.open("wb") as handle:
        for chunk in chunks:
            if not chunk:
                continue

            total += len(chunk)
            if total > limit:
                raise RepositorySourceError(
                    f"Repository source exceeds the {limit // 1_000_000} MB limit."
                )

            handle.write(chunk)

    return total


def _extract_zip(data: bytes, root: Path) -> None:
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile as exc:
        raise RepositorySourceError("The selected ZIP archive is invalid.") from exc

    infos = archive.infolist()

    if len(infos) > MAX_ARCHIVE_FILES:
        raise RepositorySourceError(
            f"ZIP contains too many entries (maximum {MAX_ARCHIVE_FILES})."
        )

    extracted = 0

    try:
        for info in infos:
            relative = _safe_relative_path(info.filename)

            if info.is_dir():
                continue

            extracted += info.file_size
            if extracted > MAX_EXTRACTED_BYTES:
                raise RepositorySourceError(
                    "The extracted repository exceeds the 50 MB analysis limit."
                )

            destination = root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)

            with archive.open(info, "r") as source, destination.open("wb") as target:
                while True:
                    chunk = source.read(1024 * 1024)
                    if not chunk:
                        break
                    target.write(chunk)
    except RepositorySourceError:
        raise
    except (OSError, zipfile.BadZipFile) as exc:
        raise RepositorySourceError(
            "The repository archive could not be extracted safely."
        ) from exc
    finally:
        archive.close()


def _normalise_github_url(repository_url: str, ref: str | None) -> str:
    parsed = urlparse(repository_url.strip())

    if parsed.scheme != "https" or parsed.hostname not in GITHUB_HOSTS:
        raise RepositorySourceError(
            "Only HTTPS GitHub repository URLs are supported."
        )

    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 2:
        raise RepositorySourceError(
            "Use a GitHub repository URL such as https://github.com/owner/repository."
        )

    owner = parts[0]
    repository = re.sub(r"\.git$", "", parts[1])

    if not re.fullmatch(r"[A-Za-z0-9_.-]+", owner):
        raise RepositorySourceError("Invalid GitHub owner.")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", repository):
        raise RepositorySourceError("Invalid GitHub repository name.")

    if ref:
        clean_ref = str(ref).strip()
        if len(clean_ref) > 200 or clean_ref.startswith("-") or ".." in clean_ref:
            raise RepositorySourceError("Invalid GitHub branch or tag.")
        return (
            f"https://api.github.com/repos/{owner}/{repository}/zipball/"
            f"{clean_ref}"
        )

    return f"https://api.github.com/repos/{owner}/{repository}/zipball/HEAD"


def _download_github_archive(repository_url: str, ref: str | None, root: Path) -> str:
    archive_url = _normalise_github_url(repository_url, ref)

    try:
        response = requests.get(
            archive_url,
            headers={
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2026-03-10",
            },
            timeout=20,
            stream=True,
        )
        response.raise_for_status()

        data = bytearray()
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if not chunk:
                continue
            data.extend(chunk)
            if len(data) > MAX_UPLOAD_BYTES:
                raise RepositorySourceError(
                    "The GitHub repository archive exceeds the 4 MB serverless limit."
                )
    except RepositorySourceError:
        raise
    except requests.RequestException as exc:
        raise RepositorySourceError(
            "ECDAT could not download the GitHub repository. Check that it is public and the URL is correct."
        ) from exc
    finally:
        if "response" in locals():
            response.close()

    _extract_zip(bytes(data), root)

    parsed = urlparse(repository_url)
    parts = [part for part in parsed.path.split("/") if part]
    label = "/".join(parts[:2]) if len(parts) >= 2 else repository_url
    return f"{label}@{ref}" if ref else label


def _normalise_scan_result(scan_results: dict, root: Path, label: str) -> dict:
    for artifact in scan_results.get("artifacts", []):
        file_value = artifact.get("file")
        if file_value:
            try:
                relative = Path(file_value).resolve().relative_to(root.resolve())
                relative_string = relative.as_posix()
                artifact["file"] = relative_string
                artifact["artifact_id"] = (
                    f"{relative_string}:{artifact.get('line', '')}:"
                    f"{artifact.get('algorithm', '')}"
                )
            except ValueError:
                pass

    scan_results["target"] = label
    return scan_results


async def scan_uploaded_files(files: list[UploadFile], relative_paths: list[str]) -> dict:
    if not files:
        raise RepositorySourceError("Choose at least one repository file.")

    if len(files) != len(relative_paths):
        raise RepositorySourceError("Repository file metadata is incomplete.")

    total_bytes = 0

    with tempfile.TemporaryDirectory(prefix="ecdat-") as temp_dir:
        root = Path(temp_dir)

        for upload, relative_value in zip(files, relative_paths):
            relative = _safe_relative_path(relative_value)
            destination = root / relative

            content = await upload.read(MAX_UPLOAD_BYTES + 1)
            total_bytes += len(content)

            if total_bytes > MAX_UPLOAD_BYTES:
                raise RepositorySourceError(
                    "The selected repository exceeds the 4 MB serverless upload limit."
                )

            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)

        return _normalise_scan_result(
            scan_repository(root),
            root,
            relative_paths[0].split("/")[0] if relative_paths else "Local repository",
        )


async def scan_uploaded_zip(archive: UploadFile) -> dict:
    if archive is None:
        raise RepositorySourceError("Choose a repository ZIP archive.")

    data = await archive.read(MAX_UPLOAD_BYTES + 1)

    if len(data) > MAX_UPLOAD_BYTES:
        raise RepositorySourceError(
            "The selected ZIP exceeds the 4 MB serverless upload limit."
        )

    with tempfile.TemporaryDirectory(prefix="ecdat-") as temp_dir:
        root = Path(temp_dir)
        _extract_zip(data, root)

        label = Path(archive.filename or "repository.zip").stem

        return _normalise_scan_result(
            scan_repository(root),
            root,
            label,
        )


def scan_github_repository(repository_url: str, ref: str | None = None) -> dict:
    with tempfile.TemporaryDirectory(prefix="ecdat-") as temp_dir:
        root = Path(temp_dir)
        label = _download_github_archive(repository_url, ref, root)

        return _normalise_scan_result(
            scan_repository(root),
            root,
            label,
        )


def parse_relative_paths(value: str | None) -> list[str]:
    if not value:
        return []

    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise RepositorySourceError(
            "Repository file metadata is invalid."
        ) from exc

    if not isinstance(parsed, list) or not all(
        isinstance(item, str) for item in parsed
    ):
        raise RepositorySourceError(
            "Repository file metadata must be a list of paths."
        )

    return parsed
