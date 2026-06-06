"""Structured logging and W3C trace-context helpers."""
from __future__ import annotations

import contextlib
import contextvars
import json
import logging
import re
import secrets
import sys
from collections.abc import Iterator, Mapping
from datetime import UTC, datetime
from typing import Any

SERVICE_NAME = "control-plane"
DEFAULT_TRACE_ID = "0" * 32
DEFAULT_SPAN_ID = "0" * 16
TRACEPARENT_HEADER = "traceparent"
_TRACEPARENT_RE = re.compile(
    r"^(?P<version>[0-9a-f]{2})-(?P<trace_id>[0-9a-f]{32})-"
    r"(?P<span_id>[0-9a-f]{16})-(?P<trace_flags>[0-9a-f]{2})$"
)
_SENSITIVE_KEY_RE = re.compile(
    r"(authorization|credential|password|passwd|secret|token|api[_-]?key|access[_-]?key|private[_-]?key)",
    re.IGNORECASE,
)
_PROMPT_KEY_RE = re.compile(r"(^|_)(prompt|messages?)(_|$)", re.IGNORECASE)
_TOOL_OUTPUT_KEY_RE = re.compile(
    r"(raw[_-]?tool[_-]?outputs?|tool[_-]?outputs?|raw[_-]?outputs?)",
    re.IGNORECASE,
)
_SENSITIVE_TAGS = {"sensitive", "confidential", "restricted", "pii", "phi", "secret"}
_REDACTED = "[REDACTED]"

_trace_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("trace_id", default=DEFAULT_TRACE_ID)
_span_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("span_id", default=DEFAULT_SPAN_ID)
_tenant_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("tenant_id", default="")
_run_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("run_id", default="")
_task_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("task_id", default="")


class TraceContext(dict[str, str]):
    """Dictionary-like trace context with canonical W3C fields."""

    @property
    def traceparent(self) -> str:
        return build_traceparent(self["trace_id"], self["span_id"], self.get("trace_flags", "01"))


def _new_trace_id() -> str:
    trace_id = secrets.token_hex(16)
    while trace_id == DEFAULT_TRACE_ID:
        trace_id = secrets.token_hex(16)
    return trace_id


def _new_span_id() -> str:
    span_id = secrets.token_hex(8)
    while span_id == DEFAULT_SPAN_ID:
        span_id = secrets.token_hex(8)
    return span_id


def parse_traceparent(value: str | None) -> TraceContext | None:
    """Parse a W3C traceparent header, rejecting malformed or all-zero IDs."""
    if not value:
        return None
    match = _TRACEPARENT_RE.match(value.strip().lower())
    if not match:
        return None
    parts = match.groupdict()
    if parts["trace_id"] == DEFAULT_TRACE_ID or parts["span_id"] == DEFAULT_SPAN_ID:
        return None
    return TraceContext(parts)


def build_traceparent(trace_id: str, span_id: str, trace_flags: str = "01") -> str:
    return f"00-{trace_id}-{span_id}-{trace_flags}"


def parse_or_generate_traceparent(value: str | None) -> TraceContext:
    parsed = parse_traceparent(value)
    if parsed is not None:
        return parsed
    return TraceContext(
        version="00",
        trace_id=_new_trace_id(),
        span_id=_new_span_id(),
        trace_flags="01",
    )


def get_trace_context() -> TraceContext:
    return TraceContext(
        version="00",
        trace_id=_trace_id_var.get(),
        span_id=_span_id_var.get(),
        trace_flags="01",
    )


def get_traceparent() -> str:
    return get_trace_context().traceparent


def trace_headers() -> dict[str, str]:
    """Headers to propagate to downstream agent, secret, model, and tool calls."""
    ctx = get_trace_context()
    return {
        TRACEPARENT_HEADER: ctx.traceparent,
        "X-Trace-ID": ctx["trace_id"],
    }


def set_log_context(
    *,
    trace_id: str | None = None,
    span_id: str | None = None,
    tenant_id: str | None = None,
    run_id: str | None = None,
    task_id: str | None = None,
) -> list[tuple[contextvars.ContextVar[str], contextvars.Token[str]]]:
    tokens: list[tuple[contextvars.ContextVar[str], contextvars.Token[str]]] = []
    values = (
        (_trace_id_var, trace_id),
        (_span_id_var, span_id),
        (_tenant_id_var, tenant_id),
        (_run_id_var, run_id),
        (_task_id_var, task_id),
    )
    for var, value in values:
        if value is not None:
            tokens.append((var, var.set(value)))
    return tokens


def reset_log_context(
    tokens: list[tuple[contextvars.ContextVar[str], contextvars.Token[str]]],
) -> None:
    for var, token in reversed(tokens):
        var.reset(token)


@contextlib.contextmanager
def log_context(**kwargs: str | None) -> Iterator[None]:
    tokens = set_log_context(**kwargs)
    try:
        yield
    finally:
        reset_log_context(tokens)


def _has_sensitive_tags(value: Mapping[str, Any]) -> bool:
    tags = value.get("data_tags") or value.get("classifications") or value.get("classification")
    if isinstance(tags, str):
        tags = [tags]
    if not isinstance(tags, list):
        return False
    normalized = {str(tag).lower().split(":", 1)[0] for tag in tags}
    return bool(normalized & _SENSITIVE_TAGS)


def redact(value: Any, *, sensitive_prompt_context: bool = False) -> Any:
    """Recursively redact credentials, sensitive prompt content, and raw tool outputs."""
    if isinstance(value, Mapping):
        redacted: dict[str, Any] = {}
        child_prompt_context = sensitive_prompt_context or _has_sensitive_tags(value)
        for key, item in value.items():
            key_str = str(key)
            if _SENSITIVE_KEY_RE.search(key_str) or _TOOL_OUTPUT_KEY_RE.search(key_str):
                redacted[key_str] = _REDACTED
            elif child_prompt_context and _PROMPT_KEY_RE.search(key_str):
                redacted[key_str] = _REDACTED
            else:
                redacted[key_str] = redact(item, sensitive_prompt_context=child_prompt_context)
        return redacted
    if isinstance(value, list):
        return [redact(item, sensitive_prompt_context=sensitive_prompt_context) for item in value]
    if isinstance(value, tuple):
        return [redact(item, sensitive_prompt_context=sensitive_prompt_context) for item in value]
    return value


def _redact_message(message: str) -> str:
    message = re.sub(
        r"(?i)\b(password|passwd|secret|token|api[_-]?key|authorization)=\S+",
        lambda m: f"{m.group(1)}={_REDACTED}",
        message,
    )
    return message


class JsonFormatter(logging.Formatter):
    """Formatter that emits one JSON object per log record."""

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401 - inherited contract
        if record.exc_info:
            exc_text = super().formatException(record.exc_info)
        else:
            exc_text = None

        data = getattr(record, "structured_data", {}) or {}
        if not isinstance(data, Mapping):
            data = {"value": data}
        if exc_text:
            data = {**data, "exception": exc_text}

        payload = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(timespec="milliseconds").replace(
                "+00:00", "Z"
            ),
            "level": record.levelname,
            "service": getattr(record, "service", SERVICE_NAME),
            "trace_id": getattr(record, "trace_id", _trace_id_var.get()),
            "span_id": getattr(record, "span_id", _span_id_var.get()),
            "tenant_id": getattr(record, "tenant_id", _tenant_id_var.get()),
            "run_id": getattr(record, "run_id", _run_id_var.get()),
            "task_id": getattr(record, "task_id", _task_id_var.get()),
            "message": _redact_message(record.getMessage()),
            "data": redact(data),
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


class StructuredLoggerAdapter(logging.LoggerAdapter):
    """Logger adapter accepting ``data=`` and context kwargs on standard log methods."""

    def process(self, msg: Any, kwargs: dict[str, Any]) -> tuple[Any, dict[str, Any]]:
        data = kwargs.pop("data", None) or {}
        context = kwargs.pop("context", None) or {}
        extra = dict(kwargs.pop("extra", {}) or {})
        extra.setdefault("service", SERVICE_NAME)
        extra.setdefault("trace_id", context.get("trace_id") or _trace_id_var.get())
        extra.setdefault("span_id", context.get("span_id") or _span_id_var.get())
        extra.setdefault("tenant_id", context.get("tenant_id") or _tenant_id_var.get())
        extra.setdefault("run_id", context.get("run_id") or _run_id_var.get())
        extra.setdefault("task_id", context.get("task_id") or _task_id_var.get())
        extra["structured_data"] = redact(data)
        kwargs["extra"] = extra
        return msg, kwargs


def _configure_logger() -> StructuredLoggerAdapter:
    base_logger = logging.getLogger("able_to_answer")
    base_logger.setLevel(logging.INFO)
    base_logger.propagate = True
    if not any(getattr(handler, "_able_to_answer_json", False) for handler in base_logger.handlers):
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(JsonFormatter())
        handler._able_to_answer_json = True  # type: ignore[attr-defined]
        base_logger.addHandler(handler)
    return StructuredLoggerAdapter(base_logger, {})


logger = _configure_logger()
