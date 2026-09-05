import io
import json
from pathlib import Path

from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
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
from analysis.verification import (
    build_verification,
    verification_to_dict,
)
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


BASE_DIR = Path(__file__).resolve().parent


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
        "business_criticality": business_criticality,
    }


async def health(request: Request):
    return JSONResponse(
        {
            "status": "ok",
            "service": "ECDAT",
        }
    )


async def scan(request: Request):
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
                "risk_landscape": scan_state.risk_landscape,
                "summary": scan_state.summary,
                "metadata": scan_state.metadata,
            }
        )

        return JSONResponse(
            report
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


routes = [
    Route(
        "/health",
        health,
        methods=["GET"],
    ),
    Route(
        "/scan",
        scan,
        methods=["POST"],
    ),
    Route(
        "/risk-landscape",
        risk_landscape,
        methods=["POST"],
    ),
    Route(
        "/history",
        history,
        methods=["GET"],
    ),
    Route("/diff", diff, methods=["POST"]),
    Route("/verify", verify, methods=["POST"]),
    Route("/verifications", verifications, methods=["GET"]),
    Route(
        "/verifications/{verification_id:path}",
        verification_detail,
        methods=["GET"],
    ),
    Route(
        "/export/json",
        export_json,
        methods=["POST"],
    ),
    Route(
        "/export/pdf",
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
