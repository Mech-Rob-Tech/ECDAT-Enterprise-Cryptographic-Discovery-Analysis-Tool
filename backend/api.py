import io
import json
from pathlib import Path

from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib import colors

from scanner.crypto_scanner import scan_repository
from analysis.report_builder import build_dashboard_report


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

    repository_path = Path(repository).expanduser().resolve()

    if not repository_path.exists():
        return JSONResponse(
            {
                "error": f"Repository does not exist: {repository_path}"
            },
            status_code=404,
        )

    if not repository_path.is_dir():
        return JSONResponse(
            {
                "error": "Repository path must be a directory."
            },
            status_code=400,
        )

    try:
        scan_results = scan_repository(
            repository_path
        )

        mosca_inputs = build_mosca_inputs()

        report = build_dashboard_report(
            scan_results,
            mosca_inputs,
        )

        return JSONResponse(report)

    except Exception as exc:
        return JSONResponse(
            {
                "error": "ECDAT scan failed.",
                "detail": str(exc),
            },
            status_code=500,
        )


async def export_json(request: Request):
    try:
        body = await request.json()

        if not body:
            return JSONResponse(
                {"error": "Scan result is required."},
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
                    'attachment; filename="ecdat-assessment.json"'
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
            f"<b>Target:</b> {report.get('target', 'Unknown')}",
            body_style,
        )
    )

    story.append(
        Paragraph(
            f"<b>Generated:</b> "
            f"{report.get('generated_at', 'Current scan')}",
            body_style,
        )
    )

    story.append(
        Paragraph(
            f"<b>Scope:</b> "
            f"{report.get('prototype_scope', 'Source-code cryptographic discovery')}",
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
            f"The scan identified "
            f"<b>{report.get('total_artifacts', 0)}</b> "
            f"cryptographic artifacts across "
            f"<b>{report.get('total_files_scanned', 0)}</b> "
            f"source files. "
            f"<b>{report.get('quantum_vulnerable_assets', 0)}</b> "
            f"assets are classified as quantum-vulnerable "
            f"by the current analysis engine.",
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

    risk = report.get(
        "risk_summary",
        {},
    )

    risk_data = [
        ["Risk Level", "Findings"],
        ["Critical", str(risk.get("critical", 0))],
        ["High", str(risk.get("high", 0))],
        ["Medium", str(risk.get("medium", 0))],
        ["Low", str(risk.get("low", 0))],
    ]

    risk_table = Table(
        risk_data,
        colWidths=[80 * mm, 40 * mm],
    )

    risk_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#0E1522"),
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

    story.append(risk_table)

    story.append(
        Spacer(1, 14)
    )

    mosca = report.get(
        "mosca_inputs",
        {},
    )

    story.append(
        Paragraph(
            "MOSCA Assessment",
            heading_style,
        )
    )

    story.append(
        Paragraph(
            f"Data lifetime: "
            f"<b>{mosca.get('data_lifetime', 0)} years</b><br/>"
            f"Migration time: "
            f"<b>{mosca.get('migration_time', 0)} years</b><br/>"
            f"Quantum horizon: "
            f"<b>{mosca.get('quantum_horizon', 0)} years</b><br/>"
            f"Business criticality: "
            f"<b>{mosca.get('business_criticality', 'Unknown')}</b>",
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
            "Type",
            "Risk",
            "Location",
        ]
    ]

    for artifact in report.get(
        "artifacts",
        [],
    ):
        location = (
            f"{artifact.get('file', '')}:"
            f"{artifact.get('line', '')}"
        )

        artifact_data.append(
            [
                artifact.get("algorithm", ""),
                artifact.get("type", ""),
                artifact.get("quantum_risk", ""),
                location,
            ]
        )

    artifact_table = Table(
        artifact_data,
        repeatRows=1,
        colWidths=[
            30 * mm,
            30 * mm,
            25 * mm,
            75 * mm,
        ],
    )

    artifact_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#0E1522"),
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
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
            ]
        )
    )

    story.append(artifact_table)

    story.append(
        Spacer(1, 14)
    )

    story.append(
        Paragraph(
            "Assessment Scope",
            heading_style,
        )
    )

    story.append(
        Paragraph(
            f"{report.get('prototype_scope', 'Source-code cryptographic discovery')}. "
            "This report reflects the findings returned by the "
            "current ECDAT analysis pipeline and should not be "
            "interpreted as a complete enterprise-wide "
            "cryptographic inventory.",
            body_style,
        )
    )

    document.build(story)

    buffer.seek(0)

    return buffer.getvalue()


async def export_pdf(request: Request):
    try:
        body = await request.json()

        if not body:
            return JSONResponse(
                {"error": "Scan result is required."},
                status_code=400,
            )

        pdf_bytes = build_pdf(body)

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": (
                    'attachment; filename="ecdat-assessment.pdf"'
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
    debug=True,
    routes=routes,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
