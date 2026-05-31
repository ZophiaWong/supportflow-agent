import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Generic, TypeVar

from pydantic import ValidationError
import requests

from app.schemas.graph import DraftReply, KBHit, TicketClassification


ENABLED_VALUES = {"1", "true", "yes", "on"}
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_TIMEOUT_SECONDS = 20.0
MAX_LOGGED_DETAIL_LENGTH = 500
ENV_LOADED = False
T = TypeVar("T")
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LLMCallResult(Generic[T]):
    value: T | None = None
    error_reason: str | None = None
    error_detail: str | None = None


def _candidate_env_paths() -> list[Path]:
    paths: list[Path] = []
    for base in [Path.cwd(), *Path.cwd().parents, Path(__file__).resolve(), *Path(__file__).resolve().parents]:
        path = base if base.name == ".env" else base / ".env"
        if path not in paths:
            paths.append(path)
    return paths


def _strip_env_value(value: str) -> str:
    stripped = value.strip()
    if len(stripped) >= 2 and stripped[0] == stripped[-1] and stripped[0] in {"'", '"'}:
        return stripped[1:-1]
    return stripped


def _load_dotenv_once() -> None:
    global ENV_LOADED
    if ENV_LOADED:
        return
    ENV_LOADED = True

    for path in _candidate_env_paths():
        if not path.is_file():
            continue
        for raw_line in path.read_text().splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            if key and key not in os.environ:
                os.environ[key] = _strip_env_value(value)
        return


def llm_enabled() -> bool:
    _load_dotenv_once()
    return os.getenv("SUPPORTFLOW_LLM_ENABLED", "").lower() in ENABLED_VALUES


def _api_key() -> str | None:
    _load_dotenv_once()
    return os.getenv("OPENAI_API_KEY") or os.getenv("SUPPORTFLOW_LLM_API_KEY")


def _model_name() -> str:
    _load_dotenv_once()
    return os.getenv("SUPPORTFLOW_LLM_MODEL", DEFAULT_MODEL)


def _base_url() -> str:
    _load_dotenv_once()
    return os.getenv("SUPPORTFLOW_LLM_BASE_URL", DEFAULT_BASE_URL)


def _chat_completions_url() -> str:
    base_url = _base_url().rstrip("/")
    if base_url.endswith("/chat/completions"):
        return base_url
    return f"{base_url}/chat/completions"


def _timeout_seconds() -> float:
    _load_dotenv_once()
    configured = os.getenv("SUPPORTFLOW_LLM_TIMEOUT_SECONDS")
    if not configured:
        return DEFAULT_TIMEOUT_SECONDS
    try:
        return float(configured)
    except ValueError:
        return DEFAULT_TIMEOUT_SECONDS


def _make_json_schema_strict(schema: dict[str, Any]) -> dict[str, Any]:
    if schema.get("type") == "object":
        schema["additionalProperties"] = False
    for value in schema.get("properties", {}).values():
        if isinstance(value, dict):
            _make_json_schema_strict(value)
    for item in schema.get("$defs", {}).values():
        if isinstance(item, dict):
            _make_json_schema_strict(item)
    if isinstance(schema.get("items"), dict):
        _make_json_schema_strict(schema["items"])
    return schema


def _json_schema_for(model: type[DraftReply] | type[TicketClassification]) -> dict[str, Any]:
    schema = model.model_json_schema()
    _make_json_schema_strict(schema)
    return {
        "type": "json_schema",
        "json_schema": {
            "name": model.__name__,
            "strict": True,
            "schema": schema,
        },
    }


def _truncated_detail(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = " ".join(value.split())
    if len(normalized) <= MAX_LOGGED_DETAIL_LENGTH:
        return normalized
    return f"{normalized[:MAX_LOGGED_DETAIL_LENGTH]}..."


def _schema_validation_detail(payload: dict[str, Any], exc: ValidationError) -> str:
    errors = [
        {
            "loc": ".".join(str(part) for part in error["loc"]),
            "type": error["type"],
            "msg": error["msg"],
        }
        for error in exc.errors()
    ]
    return f"payload_keys={sorted(payload.keys())} validation_errors={errors}"


def _http_error_reason(status_code: int) -> str:
    if status_code == 403:
        return "http_403"
    if 400 <= status_code < 500:
        return "http_4xx"
    if status_code >= 500:
        return "http_5xx"
    return "request_failed"


def _log_failure(
    *,
    task: str,
    reason: str,
    detail: str | None = None,
    status_code: int | None = None,
    exception: BaseException | None = None,
    invalid_citations: list[str] | None = None,
    allowed_citation_count: int | None = None,
) -> None:
    safe_detail = _truncated_detail(detail)
    logger.warning(
        (
            "LLM call fell back to deterministic behavior: "
            "task=%s reason=%s model=%s url=%s status=%s exception=%s "
            "invalid_citations=%s allowed_citation_count=%s detail=%s"
        ),
        task,
        reason,
        _model_name(),
        _chat_completions_url(),
        status_code,
        type(exception).__name__ if exception else None,
        invalid_citations,
        allowed_citation_count,
        safe_detail,
        extra={
            "llm_task": task,
            "llm_model": _model_name(),
            "llm_url": _chat_completions_url(),
            "llm_error_reason": reason,
            "llm_error_detail": safe_detail,
            "llm_status_code": status_code,
            "llm_exception_type": type(exception).__name__ if exception else None,
            "llm_invalid_citations": invalid_citations,
            "llm_allowed_citation_count": allowed_citation_count,
        },
    )


def _chat_completion_json(
    *,
    task: str,
    messages: list[dict[str, str]],
    response_model: type[DraftReply] | type[TicketClassification],
) -> LLMCallResult[dict[str, Any]]:
    key = _api_key()
    if not key:
        reason = "missing_api_key"
        _log_failure(task=task, reason=reason)
        return LLMCallResult(error_reason=reason)

    payload = {
        "model": _model_name(),
        "messages": messages,
        "temperature": 0.2,
        "response_format": _json_schema_for(response_model),
    }
    url = _chat_completions_url()
    headers = {
        "Authorization": f"Bearer {key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=_timeout_seconds(),
        )
    except requests.exceptions.RequestException as exc:
        reason = "request_failed"
        _log_failure(task=task, reason=reason, detail=str(exc), exception=exc)
        return LLMCallResult(error_reason=reason, error_detail=str(exc))

    if response.status_code >= 400:
        reason = _http_error_reason(response.status_code)
        detail = _truncated_detail(response.text)
        _log_failure(
            task=task,
            reason=reason,
            detail=detail,
            status_code=response.status_code,
        )
        return LLMCallResult(error_reason=reason, error_detail=detail)

    try:
        completion = response.json()
    except ValueError as exc:
        reason = "invalid_json"
        _log_failure(task=task, reason=reason, detail=response.text, exception=exc)
        return LLMCallResult(error_reason=reason, error_detail=_truncated_detail(response.text))

    try:
        content = completion["choices"][0]["message"]["content"]
        if isinstance(content, str):
            return LLMCallResult(value=json.loads(content))
        if isinstance(content, dict):
            return LLMCallResult(value=content)
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        reason = (
            "invalid_json"
            if isinstance(exc, json.JSONDecodeError)
            else "invalid_response_shape"
        )
        _log_failure(task=task, reason=reason, exception=exc)
        return LLMCallResult(error_reason=reason, error_detail=str(exc))

    reason = "invalid_response_shape"
    _log_failure(task=task, reason=reason, detail=f"content_type={type(content).__name__}")
    return LLMCallResult(error_reason=reason, error_detail=f"content_type={type(content).__name__}")


def generate_ticket_classification(
    ticket: dict[str, object],
) -> LLMCallResult[TicketClassification]:
    if not llm_enabled():
        return LLMCallResult()

    messages = [
        {
            "role": "system",
            "content": (
                "Classify support tickets for a customer support workflow. "
                "Return only the requested structured JSON. Categories are billing, "
                "account, product, bug, or other. Priorities are P0, P1, P2, or P3. "
                "Include a short reason explaining the classification."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(
                {
                    "subject": ticket.get("subject"),
                    "preview": ticket.get("preview"),
                    "source_priority": ticket.get("priority"),
                },
                sort_keys=True,
            ),
        },
    ]

    payload_result = _chat_completion_json(
        task="classify_ticket",
        messages=messages,
        response_model=TicketClassification,
    )
    if payload_result.value is None:
        return LLMCallResult(
            error_reason=payload_result.error_reason,
            error_detail=payload_result.error_detail,
        )

    try:
        payload = dict(payload_result.value)
        payload.setdefault(
            "reason",
            f"LLM classified ticket as {payload.get('category')} / {payload.get('priority')}.",
        )
        return LLMCallResult(value=TicketClassification.model_validate(payload))
    except ValidationError as exc:
        reason = "schema_validation_failed"
        detail = _schema_validation_detail(payload_result.value, exc)
        _log_failure(task="classify_ticket", reason=reason, detail=detail, exception=exc)
        return LLMCallResult(error_reason=reason, error_detail=detail)


def generate_draft_reply(
    *,
    ticket: dict[str, object],
    classification: TicketClassification,
    retrieved_chunks: list[KBHit],
) -> LLMCallResult[DraftReply]:
    if not llm_enabled():
        return LLMCallResult()

    allowed_citations = {hit.doc_id for hit in retrieved_chunks}
    evidence = [
        {
            "doc_id": hit.doc_id,
            "title": hit.title,
            "snippet": hit.snippet,
            "freshness": hit.freshness,
            "policy_severity": hit.policy_severity,
        }
        for hit in retrieved_chunks
    ]
    messages = [
        {
            "role": "system",
            "content": (
                "Draft a concise customer support reply using only the supplied "
                "ticket, classification, and knowledge evidence. Return only the "
                "requested structured JSON with top-level keys answer, citations, "
                "and confidence. Do not use response, message, text, markdown, or "
                "wrapper objects. Citations must be doc_id values from the supplied "
                "evidence. Do not invent policy, refunds, credits, or completed actions."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(
                {
                    "ticket": {
                        "subject": ticket.get("subject"),
                        "preview": ticket.get("preview"),
                        "customer_name": ticket.get("customer_name"),
                    },
                    "classification": classification.model_dump(mode="json"),
                    "allowed_citations": sorted(allowed_citations),
                    "evidence": evidence,
                },
                sort_keys=True,
            ),
        },
    ]

    payload_result = _chat_completion_json(
        task="draft_reply",
        messages=messages,
        response_model=DraftReply,
    )
    if payload_result.value is None:
        return LLMCallResult(
            error_reason=payload_result.error_reason,
            error_detail=payload_result.error_detail,
        )

    try:
        draft = DraftReply.model_validate(payload_result.value)
    except ValidationError as exc:
        reason = "schema_validation_failed"
        detail = _schema_validation_detail(payload_result.value, exc)
        _log_failure(task="draft_reply", reason=reason, detail=detail, exception=exc)
        return LLMCallResult(error_reason=reason, error_detail=detail)

    if not 0 <= draft.confidence <= 1:
        reason = "invalid_confidence"
        detail = f"confidence={draft.confidence}"
        _log_failure(task="draft_reply", reason=reason, detail=detail)
        return LLMCallResult(error_reason=reason, error_detail=detail)

    invalid_citations = sorted(set(draft.citations) - allowed_citations)
    if invalid_citations:
        reason = "unknown_citations"
        detail = f"invalid_citations={invalid_citations}"
        _log_failure(
            task="draft_reply",
            reason=reason,
            detail=detail,
            invalid_citations=invalid_citations,
            allowed_citation_count=len(allowed_citations),
        )
        return LLMCallResult(error_reason=reason, error_detail=detail)

    return LLMCallResult(value=draft)
