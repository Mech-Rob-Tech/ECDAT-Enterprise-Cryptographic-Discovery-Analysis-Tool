from typing import Any, Dict, Optional, Tuple

from starlette.concurrency import run_in_threadpool
from starlette.requests import Request
from starlette.responses import JSONResponse

from ai.context_builder import (
    AIContextError,
    build_ai_context,
)
from ai.grounding import GroundingError
from ai.providers.base import (
    AIProviderConfigurationError,
    AIProviderError,
)
from ai.providers.factory import create_ai_provider
from ai.schemas import AIAudience, AIQuery
from ai.service import (
    AIResponseValidationError,
    AIService,
)
from storage.scan_history import load_scan_state


SUMMARY_QUESTION = (
    "Summarize this ECDAT assessment using only "
    "the supplied deterministic evidence."
)


def _error(
    message: str,
    *,
    status_code: int,
    detail: Optional[str] = None,
) -> JSONResponse:
    payload: Dict[str, Any] = {
        "error": message,
    }

    if detail:
        payload["detail"] = detail

    return JSONResponse(
        payload,
        status_code=status_code,
    )


def _resolve_report(
    payload: Dict[str, Any],
) -> Tuple[
    Optional[Dict[str, Any]],
    Optional[str],
    Optional[JSONResponse],
]:
    scan_id = (
        str(
            payload.get(
                "scan_id",
                "",
            )
        ).strip()
        or None
    )

    report = payload.get("report")

    if report is not None:
        if not isinstance(report, dict):
            return (
                None,
                scan_id,
                _error(
                    "report must be an object.",
                    status_code=400,
                ),
            )

        return report, scan_id, None

    if not scan_id:
        return (
            None,
            None,
            _error(
                "Either scan_id or report is required.",
                status_code=400,
            ),
        )

    report = load_scan_state(
        scan_id
    )

    if report is None:
        return (
            None,
            scan_id,
            _error(
                "Scan not found.",
                status_code=404,
                detail=scan_id,
            ),
        )

    return report, scan_id, None


async def _handle_ai_request(
    request: Request,
    *,
    operation: str,
) -> JSONResponse:
    try:
        payload = await request.json()
    except Exception:
        return _error(
            "Request body must be valid JSON.",
            status_code=400,
        )

    if not isinstance(payload, dict):
        return _error(
            "Request body must be a JSON object.",
            status_code=400,
        )

    question = str(
        payload.get(
            "question",
            "",
        )
    ).strip()

    if (
        operation == "summary"
        and not question
    ):
        question = SUMMARY_QUESTION

    if not question:
        return _error(
            "question is required.",
            status_code=400,
        )

    report, scan_id, report_error = (
        _resolve_report(payload)
    )

    if report_error is not None:
        return report_error

    artifact_id = (
        str(
            payload.get(
                "artifact_id",
                "",
            )
        ).strip()
        or None
    )

    audience_value = (
        str(
            payload.get(
                "audience",
                AIAudience.GENERAL.value,
            )
        )
        .strip()
        .lower()
    )

    try:
        audience = AIAudience(
            audience_value
        )
    except ValueError:
        return _error(
            "Unsupported AI audience.",
            status_code=400,
            detail=audience_value,
        )

    include_evidence_text = (
        payload.get(
            "include_evidence_text",
            False,
        )
    )

    if not isinstance(
        include_evidence_text,
        bool,
    ):
        return _error(
            "include_evidence_text must "
            "be a boolean.",
            status_code=400,
        )

    try:
        context = build_ai_context(
            report,
            artifact_id=artifact_id,
            scan_id=scan_id,
            include_evidence_text=(
                include_evidence_text
            ),
        )

    except AIContextError as exc:
        status_code = (
            404
            if "not found" in str(exc).lower()
            else 400
        )

        return _error(
            "Unable to build AI context.",
            status_code=status_code,
            detail=str(exc),
        )

    query = AIQuery(
        question=question,
        scan_id=context.scan_id,
        artifact_id=context.artifact_id,
        audience=audience,
    )

    try:
        provider = create_ai_provider()

        service = AIService(
            provider=provider
        )

        response = await run_in_threadpool(
            service.execute,
            query=query,
            context=context,
            operation=operation,
        )

    except AIProviderConfigurationError as exc:
        return _error(
            "AI provider is not configured.",
            status_code=503,
            detail=str(exc),
        )

    except AIProviderError as exc:
        return _error(
            "AI provider request failed.",
            status_code=502,
            detail=str(exc),
        )

    except (
        AIResponseValidationError,
        GroundingError,
    ) as exc:
        return _error(
            "AI provider returned an unsafe "
            "or invalid response.",
            status_code=502,
            detail=str(exc),
        )

    except ValueError as exc:
        return _error(
            "AI request is invalid.",
            status_code=400,
            detail=str(exc),
        )

    return JSONResponse(
        {
            "projection": (
                f"ai_{operation}"
            ),
            "provider": (
                provider.provider_name
            ),
            "model": (
                provider.model_name
            ),
            "scan_id": context.scan_id,
            "artifact_id": (
                context.artifact_id
            ),
            "response": (
                response.to_dict()
            ),
        }
    )


async def ai_query(
    request: Request,
) -> JSONResponse:
    return await _handle_ai_request(
        request,
        operation="query",
    )


async def ai_explain(
    request: Request,
) -> JSONResponse:
    return await _handle_ai_request(
        request,
        operation="explain",
    )


async def ai_summary(
    request: Request,
) -> JSONResponse:
    return await _handle_ai_request(
        request,
        operation="summary",
    )