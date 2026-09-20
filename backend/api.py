import io
import json
from pathlib import Path

from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.datastructures import UploadFile
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from scanner.crypto_scanner import scan_repository
from analysis.report_builder import build_report
from analysis.risk_landscape import build_risk_landscape
from model.scan_state_builder import build_scan_state
from analysis.scan_diff import build_scan_diff
from analysis.dependency_service import (
    DependencyNotFoundError,
    DependencyService,
)
from analysis.verification import (
    build_verification,
    verification_to_dict,
)
from knowledge.service import KnowledgeService
from storage.scan_history import (
    list_scan_states,
    load_scan_state,
    save_scan_state,
)
from storage.verification_history import (
    list_verifications,
    load_verification,
    save_verification,
)

from ingestion.repository_source import (
    RepositorySourceError,
    parse_relative_paths,
    scan_github_repository,
    scan_uploaded_files,
    scan_uploaded_zip,
)


BASE_DIR = Path(__file__).resolve().parent

KNOWLEDGE = KnowledgeService()


def build_mosca_inputs(
    data_lifetime: int = 12,
    migration_time: int = 4,
    quantum_horizon: int = 10,
    business_criticality: str = "Critical",
):
    return {
        "data_lifetime": data_lifetime,
        "migration_time": migration_time,
        "quantum_horizon": quantum_horizon,
        "business_criticality": businasync def scan(request: Request):
    try:
        content_type = request.headers.get("content-type", "")
        
        if content_type.startswith("multipart/form-data"):
            form = await request.form()
            source_type = str(form.get("source_type", "")).strip().lower()

            if source_type == "zip":
                upload = form.get("file")
                if not isinstance(upload, UploadFile):
                    return JSONResponse(
                        {"error": "A repository ZIP file is required."},
                        status_code=400,
                    )
                scan_results = await scan_uploaded_zip(upload)

            elif source_type == "folder":
                uploads = [
                    value for key, value in form.multi_items()
                    if key == "files" and isinstance(value, UploadFile)
                ]
                relative_paths = parse_relative_paths(
                    str(form.get("paths", "[]"))
                )
                scan_results = await scan_uploaded_files(
                    uploads,
                    relative_paths,
                )

            else:
                return JSONResponse(
                    {"error": "Unsupported repository source."},
                    status_code=400,
                )

        else:
            body = await request.json()
            source_type = str(body.get("source_type", "path")).strip().lower()

            if source_type == "github":
                repository_url = str(body.get("repository_url", "")).strip()
                ref = str(body.get("ref", "")).strip() or None

                if not repository_url:
                    return JSONResponse(
                        {"error": "GitHub repository URL is required."},
                        status_code=400,
                    )

                scan_results = scan_github_repository(
                    repository_url,
                    ref=ref,
                )
            else:
                repository = body.get("repository")

                if not repository:
                    return JSONResponse(
                        {"error": "Repository path is required."},
                        status_code=400,
                    )

                repository_path = (
                    Path(repository)
                    .expanduser()
                    .resolve()
                )

                if not repository_path.exists():
                    return JSONResponse(
                        {
                            "error": (
                                "Repository does not exist: "
                                f"{repository_path}"
                            )
                        },
                        status_code=404,
                    )

                if not repository_path.is_dir():
                    return JSONResponse(
                        {
                            "error": (
                                "Repository path must be "
                                "a directory."
                            )
                        },
                        status_code=400,
                    )

                scan_results = scan_repository(repository_path)

        mosca_inputs = build_mosca_inputs()

        report = build_report(
            scan_results,
            mosca_inputs,
        )

        scan_state = build_scan_state(
            report
        )

        save_scan_state(
            {
                "scan_id": scan_state.scan_id,
                "application_ids": scan_state.application_ids,
                "generated_at": scan_state.generated_at,
                "target": scan_state.target,
                "artifact_ids": scan_state.artifact_ids,
                "canonical_artifacts": scan_state.canonical_artifacts,
                "evidence": scan_state.evidence,
                "business_contexts": scan_state.business_contexts,
                "relationships": scan_state.relationships,
                "dependencies": scan_state.dependencies,
                "risk_landscape": scan_state.risk_landscape,
                "summary": scan_state.summary,
                "metadata": scan_state.metadata,
            }
        )

        return JSONResponse(report)

    except RepositorySourceError as exc:
        return JSONResponse(
            {
                "error": "Repository source rejected.",
                "detail": str(exc),
            },
            status_code=400,
        )
    except Exception as exc:
        return JSONResponse(
            {
                "error": "ECDAT scan failed.",
                "detail": str(exc),
            },
            status_code=500,
        )

async def risk_landscape(request: Request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            {
                "error": "Request body must be valid JSON."
            },
            status_code=400,
        )

    repository = body.get("repository")

    if not repository:
        return JSONResponse(
            {
                "error": "Repository path is required."
            },
            status_code=400,
        )

    repository_path = (
        Path(repository)
        .expanduser()
        .resolve()
    )

    if not repository_path.exists():
        return JSONResponse(
            {
                "error": (
                    "Repository does not exist: "
                    f"{repository_path}"
                )
            },
            status_code=404,
        )

    if not repository_path.is_dir():
        return JSONResponse(
            {
                "error": (
                    "Repository path must be "
                    "a directory."
                )
            },
            status_code=400,
        )

    try:
        scan_results = scan_repository(
            repository_path
        )

        mosca_inputs = build_mosca_inputs()

        report = build_report(
            scan_results,
            mosca_inputs,
        )

        return JSONResponse(
            {
                "projection": "risk_landscape",
                "risk_landscape": report.get(
                    "risk_landscape",
                    {},
                ),
            }
        )

    except Exception as exc:
        return JSONResponse(
            {
                "error": "Risk Landscape analysis failed.",
                "detail": str(exc),
            },
            status_code=500,
        )

def _load_dependency_service(scan_id: str):
    """Build a dependency service from one immutable historical scan."""

    scan_state = load_scan_state(scan_id)

    if scan_state is None:
        return None, None

    dependencies = scan_state.get(
        "dependencies",
        [],
    ) or []

    service = DependencyService.from_dicts(dependencies)

    return scan_state, service


async def dependencies(request: Request):
    """Return observed dependency facts for one historical scan."""

    scan_id = str(
        request.query_params.get(
            "scan_id",
            "",
        )
    ).strip()

    if not scan_id:
        return JSONResponse(
            {
                "error": "scan_id is required.",
            },
            status_code=400,
        )

    scan_state, service = _load_dependency_service(
        scan_id
    )

    if scan_state is None:
        return JSONResponse(
            {
                "error": "Scan not found.",
                "scan_id": scan_id,
            },
            status_code=404,
        )

    source_node_id = (
        request.query_params.get("source_node_id")
        or None
    )
    target_node_id = (
        request.query_params.get("target_node_id")
        or None
    )
    relationship_type = (
        request.query_params.get("relationship_type")
        or None
    )

    records = service.list_dependencies(
        source_node_id=source_node_id,
        target_node_id=target_node_id,
        relationship_type=relationship_type,
    )

    return JSONResponse(
        {
            "scan_id": scan_id,
            "dependencies": [
                item.__dict__
                for item in records
            ],
            "total": len(records),
        }
    )


async def dependency_detail(request: Request):
    """Return one observed dependency from one historical scan."""

    scan_id = str(
        request.query_params.get(
            "scan_id",
            "",
        )
    ).strip()

    dependency_id = str(
        request.path_params.get(
            "dependency_id",
            "",
        )
    ).strip()

    if not scan_id:
        return JSONResponse(
            {
                "error": "scan_id is required.",
            },
            status_code=400,
        )

    if not dependency_id:
        return JSONResponse(
            {
                "error": "dependency_id is required.",
            },
            status_code=400,
        )

    scan_state, service = _load_dependency_service(
        scan_id
    )

    if scan_state is None:
        return JSONResponse(
            {
                "error": "Scan not found.",
                "scan_id": scan_id,
            },
            status_code=404,
        )

    try:
        dependency = service.get_dependency(
            dependency_id
        )
    except DependencyNotFoundError:
        return JSONResponse(
            {
                "error": "Dependency not found.",
                "dependency_id": dependency_id,
                "scan_id": scan_id,
            },
            status_code=404,
        )

    return JSONResponse(
        {
            "scan_id": scan_id,
            "dependency": dependency.__dict__,
        }
    )


async def dependency_closure(request: Request):
    """Return deterministic dependency closure for one node."""

    scan_id = str(
        request.query_params.get(
            "scan_id",
            "",
        )
    ).strip()

    node_id = str(
        request.path_params.get(
            "node_id",
            "",
        )
    ).strip()

    if not scan_id:
        return JSONResponse(
            {
                "error": "scan_id is required.",
            },
            status_code=400,
        )

    if not node_id:
        return JSONResponse(
            {
                "error": "node_id is required.",
            },
            status_code=400,
        )

    scan_state, service = _load_dependency_service(
        scan_id
    )

    if scan_state is None:
        return JSONResponse(
            {
                "error": "Scan not found.",
                "scan_id": scan_id,
            },
            status_code=404,
        )

    external_node_ids = tuple(
        value.strip()
        for value in request.query_params.getlist(
            "external_node_id"
        )
        if value.strip()
    )

    closure = service.closure(
        node_id,
        external_node_ids=external_node_ids,
    )

    return JSONResponse(
        {
            "scan_id": scan_id,
            "closure": closure.__dict__,
        }
    )


async def dependency_paths(request: Request):
    """Return deterministic paths between two nodes."""

    scan_id = str(
        request.query_params.get(
            "scan_id",
            "",
        )
    ).strip()

    source_node_id = str(
        request.path_params.get(
            "source_node_id",
            "",
        )
    ).strip()

    target_node_id = str(
        request.path_params.get(
            "target_node_id",
            "",
        )
    ).strip()

    if not scan_id:
        return JSONResponse(
            {
                "error": "scan_id is required.",
            },
            status_code=400,
        )

    if not source_node_id or not target_node_id:
        return JSONResponse(
            {
                "error": (
                    "source_node_id and "
                    "target_node_id are required."
                ),
            },
            status_code=400,
        )

    scan_state, service = _load_dependency_service(
        scan_id
    )

    if scan_state is None:
        return JSONResponse(
            {
                "error": "Scan not found.",
                "scan_id": scan_id,
            },
            status_code=404,
        )

    max_depth_value = request.query_params.get(
        "max_depth"
    )

    max_depth = None

    if max_depth_value is not None:
        try:
            max_depth = int(max_depth_value)
        except ValueError:
            return JSONResponse(
                {
                    "error": "max_depth must be an integer.",
                },
                status_code=400,
            )

        if max_depth < 1:
            return JSONResponse(
                {
                    "error": "max_depth must be greater than zero.",
                },
                status_code=400,
            )

    paths = service.paths(
        source_node_id,
        target_node_id,
        max_depth=max_depth,
    )

    return JSONResponse(
        {
            "scan_id": scan_id,
            "source_node_id": source_node_id,
            "target_node_id": target_node_id,
            "paths": [
                path.__dict__
                for path in paths
            ],
            "total": len(paths),
        }
    )


async def dependency_migration_order(request: Request):
    """Return technical migration precedence for one node."""

    scan_id = str(
        request.query_params.get(
            "scan_id",
            "",
        )
    ).strip()

    node_id = str(
        request.path_params.get(
            "node_id",
            "",
        )
    ).strip()

    if not scan_id:
        return JSONResponse(
            {
                "error": "scan_id is required.",
            },
            status_code=400,
        )

    if not node_id:
        return JSONResponse(
            {
                "error": "node_id is required.",
            },
            status_code=400,
        )

    scan_state, service = _load_dependency_service(
        scan_id
    )

    if scan_state is None:
        return JSONResponse(
            {
                "error": "Scan not found.",
                "scan_id": scan_id,
            },
            status_code=404,
        )

    layers = service.migration_precedence(
        node_id
    )

    return JSONResponse(
        {
            "scan_id": scan_id,
            "root_node_id": node_id,
            "migration_order": [
                list(layer)
                for layer in layers
            ],
        }
    )


async def history(request: Request):
    try:
        scans = list_scan_states()

        return JSONResponse(
            {
                "scans": scans,
                "total": len(scans),
            }
        )

    except Exception as exc:
        return JSONResponse(
            {
                "error": "Failed to load scan history.",
                "detail": str(exc),
            },
            status_code=500,
        )

async def diff(request):
    try:
        payload = await request.json()

        from_scan_id = str(payload.get("from_scan_id", "")).strip()
        to_scan_id = str(payload.get("to_scan_id", "")).strip()

        if not from_scan_id:
            return JSONResponse(
                {"error": "from_scan_id is required."},
                status_code=400,
            )

        if not to_scan_id:
            return JSONResponse(
                {"error": "to_scan_id is required."},
                status_code=400,
            )

        from_scan = load_scan_state(from_scan_id)
        to_scan = load_scan_state(to_scan_id)

        if from_scan is None:
            return JSONResponse(
                {
                    "error": "Source scan not found.",
                    "scan_id": from_scan_id,
                },
                status_code=404,
            )

        if to_scan is None:
            return JSONResponse(
                {
                    "error": "Target scan not found.",
                    "scan_id": to_scan_id,
                },
                status_code=404,
            )

        return JSONResponse(
            build_scan_diff(from_scan, to_scan)
        )

    except Exception as exc:
        return JSONResponse(
            {
                "error": "ECDAT scan diff failed.",
                "detail": str(exc),
            },
            status_code=500,
        )


async def verify(request: Request):
    """
    Verify a migration/remediation using two persisted scan states.

    No repository is rescanned. Verification is derived exclusively
    from historical canonical scan states and their semantic diff.
    """
    try:
        payload = await request.json()

        from_scan_id = str(
            payload.get("from_scan_id", "")
        ).strip()

        to_scan_id = str(
            payload.get("to_scan_id", "")
        ).strip()

        artifact_id = str(
            payload.get("artifact_id", "")
        ).strip()

        migration_option_id = (
            str(payload.get("migration_option_id", "")).strip()
            or None
        )

        replacement_artifact_id = (
            str(
                payload.get(
                    "replacement_artifact_id",
                    "",
                )
            ).strip()
            or None
        )

        if not from_scan_id:
            return JSONResponse(
                {
                    "error": "from_scan_id is required."
                },
                status_code=400,
            )

        if not to_scan_id:
            return JSONResponse(
                {
                    "error": "to_scan_id is required."
                },
                status_code=400,
            )

        if not artifact_id:
            return JSONResponse(
                {
                    "error": "artifact_id is required."
                },
                status_code=400,
            )

        from_scan = load_scan_state(
            from_scan_id
        )

        to_scan = load_scan_state(
            to_scan_id
        )

        if from_scan is None:
            return JSONResponse(
                {
                    "error": "Source scan not found.",
                    "scan_id": from_scan_id,
                },
                status_code=404,
            )

        if to_scan is None:
            return JSONResponse(
                {
                    "error": "Target scan not found.",
                    "scan_id": to_scan_id,
                },
                status_code=404,
            )

        diff = build_scan_diff(
            from_scan,
            to_scan,
        )

        verification = build_verification(
            from_scan=from_scan,
            to_scan=to_scan,
            diff=diff,
            artifact_id=artifact_id,
            migration_option_id=migration_option_id,
            replacement_artifact_id=replacement_artifact_id,
        )

        verification_payload = verification_to_dict(
            verification
        )

        save_verification(
            verification_payload
        )

        return JSONResponse(
            {
                "projection": "verification",
                "verification": verification_payload,
                "diff_summary": diff.get(
                    "summary",
                    {},
                ),
                "persisted": True,
            }
        )

    except Exception as exc:
        return JSONResponse(
            {
                "error": "ECDAT verification failed.",
                "detail": str(exc),
            },
            status_code=500,
        )


async def verifications(request: Request):
    """
    Return persisted verification summaries.
    """
    try:
        records = list_verifications()

        return JSONResponse(
            {
                "verifications": records,
                "total": len(records),
            }
        )

    except Exception as exc:
        return JSONResponse(
            {
                "error": "Failed to load verification history.",
                "detail": str(exc),
            },
            status_code=500,
        )


async def verification_detail(request: Request):
    """
    Return one persisted verification record.
    """
    verification_id = str(
        request.path_params.get(
            "verification_id",
            "",
        )
    ).strip()

    if not verification_id:
        return JSONResponse(
            {
                "error": "verification_id is required."
            },
            status_code=400,
        )

    verification = load_verification(
        verification_id
    )

    if verification is None:
        return JSONResponse(
            {
                "error": "Verification not found.",
                "verification_id": verification_id,
            },
            status_code=404,
        )

    return JSONResponse(
        {
            "verification": verification,
        }
    )

async def export_json(request: Request):
    try:
        body = await request.json()

        if not body:
            return JSONResponse(
                {
                    "error": (
                        "Scan result is required."
                    )
                },
                status_code=400,
            )

        payload = json.dumps(
            body,
            indent=2,
            ensure_ascii=False,
        )

        return Response(
            content=payload,
            media_type="application/json",
            headers={
                "Content-Disposition": (
                    'attachment; '
                    'filename="ecdat-assessment.json"'
                )
            },
        )

    except Exception as exc:
        return JSONResponse(
            {
                "error": "JSON export failed.",
                "detail": str(exc),
            },
            status_code=500,
        )


def get_risk_summary(report):
    """
    Use the canonical security-risk summary first.

    Fall back to the legacy summary so older imported
    reports remain exportable.
    """
    canonical_summary = (
        report.get("summary", {})
        .get("security_risk_summary")
    )

    if canonical_summary:
        return canonical_summary

    return report.get(
        "risk_summary",
        {},
    )


def get_report_value(
    report,
    key,
    default=0,
):
    value = report.get(key)

    if value is not None:
        return value

    metadata = report.get(
        "metadata",
        {},
    )

    if key in metadata:
        return metadata[key]

    return default


def build_pdf(report):
    buffer = io.BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )

    styles = getSampleStyleSheet()

    title_style = styles["Title"]
    heading_style = styles["Heading2"]
    body_style = styles["BodyText"]

    story = []

    target = (
        report.get("target")
        or report.get("metadata", {}).get(
            "target",
            "Unknown",
        )
    )

    generated_at = (
        report.get("generated_at")
        or report.get("metadata", {}).get(
            "generated_at",
            "Current scan",
        )
    )

    prototype_scope = (
        report.get("prototype_scope")
        or report.get("metadata", {}).get(
            "prototype_scope",
            "Source-code cryptographic discovery",
        )
    )

    total_artifacts = (
        report.get("total_artifacts")
        or report.get("summary", {}).get(
            "total_artifacts",
            0,
        )
    )

    total_files = (
        report.get("total_files_scanned")
        or report.get("summary", {}).get(
            "total_files_scanned",
            0,
        )
    )

    quantum_vulnerable = report.get(
        "quantum_vulnerable_assets",
        report.get(
            "summary", {}
        ).get(
            "quantum_relevant_assets",
            0,
        ),
    )

    story.append(
        Paragraph(
            "ECDAT — Security Assessment Report",
            title_style,
        )
    )

    story.append(
        Spacer(1, 8)
    )

    story.append(
        Paragraph(
            f"<b>Target:</b> {target}",
            body_style,
        )
    )

    story.append(
        Paragraph(
            f"<b>Generated:</b> {generated_at}",
            body_style,
        )
    )

    story.append(
        Paragraph(
            f"<b>Scope:</b> {prototype_scope}",
            body_style,
        )
    )

    story.append(
        Spacer(1, 14)
    )

    story.append(
        Paragraph(
            "Executive Summary",
            heading_style,
        )
    )

    story.append(
        Paragraph(
            (
                "The scan identified "
                f"<b>{total_artifacts}</b> "
                "cryptographic artifacts across "
                f"<b>{total_files}</b> "
                "source files. "
                f"<b>{quantum_vulnerable}</b> "
                "assets are classified as "
                "quantum-vulnerable by the current "
                "analysis engine."
            ),
            body_style,
        )
    )

    story.append(
        Spacer(1, 12)
    )

    story.append(
        Paragraph(
            "Risk Distribution",
            heading_style,
        )
    )

    risk = get_risk_summary(
        report
    )

    def risk_value(level):
        return risk.get(
            level,
            risk.get(
                level.lower(),
                0,
            ),
        )

    risk_data = [
        ["Risk Level", "Findings"],
        [
            "Critical",
            str(risk_value("CRITICAL")),
        ],
        [
            "High",
            str(risk_value("HIGH")),
        ],
        [
            "Medium",
            str(risk_value("MEDIUM")),
        ],
        [
            "Low",
            str(risk_value("LOW")),
        ],
    ]

    risk_table = Table(
        risk_data,
        colWidths=[
            80 * mm,
            40 * mm,
        ],
    )

    risk_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor(
                        "#0E1522"
                    ),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "ALIGN",
                    (1, 1),
                    (1, -1),
                    "CENTER",
                ),
            ]
        )
    )

    story.append(
        risk_table
    )

    story.append(
        Spacer(1, 14)
    )

    mosca = report.get(
        "mosca_inputs",
        {},
    )

    story.append(
        Paragraph(
            "MOSCA Assessment Inputs",
            heading_style,
        )
    )

    story.append(
        Paragraph(
            (
                f"Data lifetime: "
                f"<b>{mosca.get('data_lifetime', 0)} years</b><br/>"
                f"Migration time: "
                f"<b>{mosca.get('migration_time', 0)} years</b><br/>"
                f"Quantum horizon: "
                f"<b>{mosca.get('quantum_horizon', 0)} years</b><br/>"
                f"Business criticality: "
                f"<b>{mosca.get('business_criticality', 'Unknown')}</b>"
            ),
            body_style,
        )
    )

    story.append(
        Spacer(1, 14)
    )

    story.append(
        Paragraph(
            "Cryptographic Findings",
            heading_style,
        )
    )

    artifact_data = [
        [
            "Algorithm",
            "Risk",
            "Purpose",
            "File",
            "Line",
        ]
    ]

    artifacts = report.get(
        "artifacts",
        [],
    )

    if not artifacts:
        artifacts = report.get(
            "canonical_artifacts",
            [],
        )

    for artifact in artifacts:
        risk_value_for_artifact = artifact.get(
            "quantum_risk"
        )

        if not risk_value_for_artifact:
            artifact_risk = artifact.get(
                "risk",
                {},
            )

            security_risk = artifact_risk.get(
                "security",
                {},
            )

            risk_value_for_artifact = (
                security_risk.get(
                    "level",
                    "",
                )
            )

        purpose = artifact.get(
            "purpose",
            "unknown",
        )

        file_name = artifact.get(
            "file",
            "",
        )

        line = artifact.get(
            "line",
            "",
        )

        if not file_name:
            details = artifact.get(
                "details",
                {},
            )

            file_name = details.get(
                "file",
                "",
            )

        if not line:
            details = artifact.get(
                "details",
                {},
            )

            line = details.get(
                "line",
                "",
            )

        artifact_data.append(
            [
                str(
                    artifact.get(
                        "algorithm",
                        "",
                    )
                ),
                str(
                    risk_value_for_artifact
                ),
                str(
                    purpose
                ),
                str(
                    file_name
                ),
                str(
                    line
                ),
            ]
        )

    if len(artifact_data) > 1:
        artifact_table = Table(
            artifact_data,
            repeatRows=1,
        )

        artifact_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor(
                            "#0E1522"
                        ),
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.white,
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.4,
                        colors.grey,
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold",
                    ),
                    (
                        "FONTSIZE",
                        (0, 0),
                        (-1, -1),
                        7,
                    ),
                ]
            )
        )

        story.append(
            artifact_table
        )

    document.build(
        story
    )

    buffer.seek(0)

    return buffer.getvalue()


async def export_pdf(request: Request):
    try:
        body = await request.json()

        if not body:
            return JSONResponse(
                {
                    "error": (
                        "Scan result is required."
                    )
                },
                status_code=400,
            )

        pdf = build_pdf(
            body
        )

        return Response(
            content=pdf,
            media_type="application/pdf",
            headers={
                "Content-Disposition": (
                    'attachment; '
                    'filename="ecdat-assessment.pdf"'
                )
            },
        )

    except Exception as exc:
        return JSONResponse(
            {
                "error": "PDF export failed.",
                "detail": str(exc),
            },
            status_code=500,
        )



def _knowledge_algorithm_dict(item):
    return {
        "knowledge_id": item.knowledge_id,
        "name": item.name,
        "aliases": list(item.aliases),
        "family": item.family,
        "primitive": item.primitive,
        "purposes": list(item.purposes),
        "lifecycle_status": item.lifecycle_status,
        "quantum_posture": item.quantum_posture,
        "security_strength": {
            "classical_bits": item.security_strength.classical_bits,
            "quantum_bits": item.security_strength.quantum_bits,
            "basis": item.security_strength.basis,
        },
        "key_sizes": list(item.key_sizes),
        "standards": list(item.standards),
        "description": item.description,
        "notes": item.notes,
        "effective_from": item.effective_from,
        "effective_until": item.effective_until,
        "source_ids": list(item.source_ids),
        "confidence": item.confidence,
        "record_version": item.record_version,
    }


def _knowledge_standard_dict(item):
    return {
        "standard_id": item.standard_id,
        "authority": item.authority,
        "identifier": item.identifier,
        "title": item.title,
        "status": item.status,
        "published_at": item.published_at,
        "effective_from": item.effective_from,
        "effective_until": item.effective_until,
        "related_algorithms": list(item.related_algorithms),
        "supersedes": list(item.supersedes),
        "source_ids": list(item.source_ids),
        "confidence": item.confidence,
        "record_version": item.record_version,
    }


def _knowledge_migration_dict(item):
    return {
        "relationship_id": item.relationship_id,
        "source_algorithm": item.source_algorithm,
        "target_algorithm": item.target_algorithm,
        "relationship_type": item.relationship_type,
        "applicable_purposes": list(item.applicable_purposes),
        "hybrid": item.hybrid,
        "prerequisites": list(item.prerequisites),
        "constraints": list(item.constraints),
        "source_ids": list(item.source_ids),
        "effective_from": item.effective_from,
        "effective_until": item.effective_until,
        "confidence": item.confidence,
        "record_version": item.record_version,
    }


def _knowledge_compatibility_dict(item):
    return {
        "compatibility_id": item.compatibility_id,
        "algorithm": item.algorithm,
        "target_type": item.target_type,
        "target_name": item.target_name,
        "version_min": item.version_min,
        "version_max": item.version_max,
        "status": item.status,
        "constraints": list(item.constraints),
        "source_ids": list(item.source_ids),
        "effective_from": item.effective_from,
        "effective_until": item.effective_until,
        "confidence": item.confidence,
        "record_version": item.record_version,
    }


def _knowledge_conflict_dict(item):
    return {
        "conflict_id": item.conflict_id,
        "subject_type": item.subject_type,
        "subject_id": item.subject_id,
        "field": item.field,
        "values": list(item.values),
        "source_ids": list(item.source_ids),
        "resolution": item.resolution,
        "severity": item.severity,
    }


async def knowledge(request: Request):
    params = request.query_params

    query = params.get("q", "").strip().lower()
    primitive = params.get("primitive", "").strip().lower()
    lifecycle = params.get("lifecycle", "").strip().lower()
    quantum = params.get("quantum_posture", "").strip().lower()

    records = []

    for item in KNOWLEDGE.algorithms():
        searchable = " ".join(
            [
                item.name,
                item.family,
                item.description,
                *item.aliases,
            ]
        ).lower()

        if query and query not in searchable:
            continue

        if primitive and item.primitive.lower() != primitive:
            continue

        if lifecycle and item.lifecycle_status.lower() != lifecycle:
            continue

        if quantum and item.quantum_posture.lower() != quantum:
            continue

        records.append(
            _knowledge_algorithm_dict(item)
        )

    return JSONResponse(
        {
            "projection": "knowledge",
            "knowledge_snapshot": KNOWLEDGE.snapshot(),
            "records": records,
            "total": len(records),
        }
    )


async def knowledge_snapshot(request: Request):
    return JSONResponse(
        {
            "projection": "knowledge_snapshot",
            "snapshot": KNOWLEDGE.snapshot(),
        }
    )


async def knowledge_freshness(request: Request):
    raw_max_age = request.query_params.get(
        "max_age_days",
        "180",
    )

    try:
        max_age = int(raw_max_age)
    except ValueError:
        return JSONResponse(
            {
                "error": "max_age_days must be an integer."
            },
            status_code=400,
        )

    return JSONResponse(
        {
            "projection": "knowledge_freshness",
            "knowledge_snapshot": KNOWLEDGE.snapshot(),
            "freshness": KNOWLEDGE.freshness(
                max_age_days=max_age,
                as_of=request.query_params.get("as_of"),
            ),
        }
    )


async def knowledge_standards(request: Request):
    records = [
        _knowledge_standard_dict(item)
        for item in KNOWLEDGE.standards()
    ]

    return JSONResponse(
        {
            "projection": "knowledge_standards",
            "knowledge_snapshot": KNOWLEDGE.snapshot(),
            "standards": records,
            "total": len(records),
        }
    )


async def knowledge_migrations(request: Request):
    source = request.query_params.get("source")
    purpose = request.query_params.get("purpose")

    records = []

    for item in KNOWLEDGE.migrations():

        if source and item.source_algorithm.lower() != source.lower():
            continue

        if purpose and purpose.lower() not in {
            value.lower()
            for value in item.applicable_purposes
        }:
            continue

        records.append(
            _knowledge_migration_dict(item)
        )

    return JSONResponse(
        {
            "projection": "knowledge_migrations",
            "knowledge_snapshot": KNOWLEDGE.snapshot(),
            "migrations": records,
            "total": len(records),
        }
    )


async def knowledge_compatibility(request: Request):
    algorithm = request.query_params.get("algorithm")
    target_type = request.query_params.get("target_type")
    target_name = request.query_params.get("target_name")

    records = []

    for item in KNOWLEDGE.compatibility():

        if algorithm and item.algorithm.lower() != algorithm.lower():
            continue

        if target_type and item.target_type.lower() != target_type.lower():
            continue

        if target_name and item.target_name.lower() != target_name.lower():
            continue

        records.append(
            _knowledge_compatibility_dict(item)
        )

    return JSONResponse(
        {
            "projection": "knowledge_compatibility",
            "knowledge_snapshot": KNOWLEDGE.snapshot(),
            "compatibility": records,
            "total": len(records),
        }
    )


async def knowledge_detail(request: Request):
    name = request.path_params.get("name", "").strip()

    if not name:
        return JSONResponse(
            {
                "error": "Algorithm name is required."
            },
            status_code=400,
        )

    result = KNOWLEDGE.resolve(
        name,
        purpose=request.query_params.get("purpose"),
        as_of=request.query_params.get("as_of"),
        target_type=request.query_params.get("target_type"),
        target_name=request.query_params.get("target_name"),
        target_version=request.query_params.get("target_version"),
    )

    if result.algorithm is None:
        return JSONResponse(
            {
                "error": "Cryptographic knowledge not found.",
                "query": name,
                "explainability": result.explainability,
            },
            status_code=404,
        )

    return JSONResponse(
        {
            "projection": "knowledge_detail",
            "knowledge_snapshot": KNOWLEDGE.snapshot(),
            "resolution": {
                "query": result.query,
                "normalized_query": result.normalized_query,
                "matched_by": result.matched_by,
                "current": result.current,
                "algorithm": _knowledge_algorithm_dict(
                    result.algorithm
                ),
                "standards": [
                    _knowledge_standard_dict(item)
                    for item in result.standards
                ],
                "compatibility": [
                    _knowledge_compatibility_dict(item)
                    for item in result.compatibility
                ],
                "migrations": [
                    _knowledge_migration_dict(item)
                    for item in result.migrations
                ],
                "conflicts": [
                    _knowledge_conflict_dict(item)
                    for item in result.conflicts
                ],
                "explainability": result.explainability,
            },
        }
    )


async def knowledge_resolve(request: Request):
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse(
            {
                "error": "Request body must be valid JSON."
            },
            status_code=400,
        )

    query = str(
        payload.get("query", "")
    ).strip()

    if not query:
        return JSONResponse(
            {
                "error": "query is required."
            },
            status_code=400,
        )

    result = KNOWLEDGE.resolve(
        query,
        purpose=payload.get("purpose"),
        as_of=payload.get("as_of"),
        target_type=payload.get("target_type"),
        target_name=payload.get("target_name"),
        target_version=payload.get("target_version"),
    )

    return JSONResponse(
        {
            "projection": "knowledge_resolution",
            "knowledge_snapshot": KNOWLEDGE.snapshot(),
            "resolution": {
                "status": (
                    "UNRESOLVED"
                    if result.algorithm is None
                    else (
                        "CONFLICT"
                        if result.conflicts
                        else "RESOLVED"
                    )
                ),
                "query": result.query,
                "normalized_query": result.normalized_query,
                "matched_by": result.matched_by,
                "current": result.current,
                "algorithm": (
                    None
                    if result.algorithm is None
                    else _knowledge_algorithm_dict(
                        result.algorithm
                    )
                ),
                "standards": [
                    _knowledge_standard_dict(item)
                    for item in result.standards
                ],
                "compatibility": [
                    _knowledge_compatibility_dict(item)
                    for item in result.compatibility
                ],
                "migrations": [
                    _knowledge_migration_dict(item)
                    for item in result.migrations
                ],
                "conflicts": [
                    _knowledge_conflict_dict(item)
                    for item in result.conflicts
                ],
                "explainability": result.explainability,
            },
        }
    )

routes = [
    Route(
        "/api/health",
        health,
        methods=["GET"],
    ),
    Route(
        "/api/scan",
        scan,
        methods=["POST"],
    ),
    Route(
        "/api/risk-landscape",
        risk_landscape,
        methods=["POST"],
    ),
    Route(
        "/api/history",
        history,
        methods=["GET"],
    ),
    Route(
        "/api/dependencies",
        dependencies,
        methods=["GET"],
    ),
    Route(
        "/api/dependencies/{node_id:path}/closure",
        dependency_closure,
        methods=["GET"],
    ),
    Route(
        "/api/dependencies/{source_node_id:path}/paths/{target_node_id:path}",
        dependency_paths,
        methods=["GET"],
    ),
    Route(
        "/api/dependencies/{node_id:path}/migration-order",
        dependency_migration_order,
        methods=["GET"],
    ),
    Route(
        "/api/dependencies/{dependency_id:path}",
        dependency_detail,
        methods=["GET"],
    ),
    Route("/api/diff", diff, methods=["POST"]),
    Route("/api/verify", verify, methods=["POST"]),
    Route("/api/verifications", verifications, methods=["GET"]),
    Route(
        "/api/verifications/{verification_id:path}",
        verification_detail,
        methods=["GET"],
    ),
    Route(
        "/api/knowledge",
        knowledge,
        methods=["GET"],
    ),
    Route(
        "/api/knowledge/snapshot",
        knowledge_snapshot,
        methods=["GET"],
    ),
    Route(
        "/api/knowledge/freshness",
        knowledge_freshness,
        methods=["GET"],
    ),
    Route(
        "/api/knowledge/standards",
        knowledge_standards,
        methods=["GET"],
    ),
    Route(
        "/api/knowledge/migrations",
        knowledge_migrations,
        methods=["GET"],
    ),
    Route(
        "/api/knowledge/compatibility",
        knowledge_compatibility,
        methods=["GET"],
    ),
    Route(
        "/api/knowledge/resolve",
        knowledge_resolve,
        methods=["POST"],
    ),
    Route(
        "/api/knowledge/{name:path}",
        knowledge_detail,
        methods=["GET"],
    ),
    Route(
        "/api/export/json",
        export_json,
        methods=["POST"],
    ),
    Route(
        "/api/export/pdf",
        export_pdf,
        methods=["POST"],
    ),
]


app = Starlette(
    routes=routes
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)
