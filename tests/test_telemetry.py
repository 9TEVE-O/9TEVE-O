from __future__ import annotations

import json
import logging
from io import StringIO
from pathlib import Path

from able_to_answer.core.logging import (
    JsonFormatter,
    logger,
    parse_or_generate_traceparent,
    redact,
    reset_log_context,
    set_log_context,
    trace_headers,
)

MANDATORY_FIELDS = {
    "timestamp",
    "level",
    "service",
    "trace_id",
    "span_id",
    "tenant_id",
    "run_id",
    "task_id",
    "message",
    "data",
}


def test_json_logs_emit_required_telemetry_fields():
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    base_logger = logger.logger
    base_logger.addHandler(handler)
    tokens = set_log_context(
        trace_id="4bf92f3577b34da6a3ce929d0e0e4736",
        span_id="00f067aa0ba902b7",
        tenant_id="tenant_1",
        run_id="run_1",
        task_id="task_1",
    )
    try:
        logger.info("task_dispatched", data={"policy_decision": "allow"})
    finally:
        reset_log_context(tokens)
        base_logger.removeHandler(handler)

    payload = json.loads(stream.getvalue())
    assert MANDATORY_FIELDS <= payload.keys()
    assert payload["message"] == "task_dispatched"
    assert payload["trace_id"] == "4bf92f3577b34da6a3ce929d0e0e4736"
    assert payload["span_id"] == "00f067aa0ba902b7"
    assert payload["tenant_id"] == "tenant_1"
    assert payload["run_id"] == "run_1"
    assert payload["task_id"] == "task_1"
    assert payload["data"] == {"policy_decision": "allow"}


def test_traceparent_parsing_and_generation():
    inbound = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
    parsed = parse_or_generate_traceparent(inbound)
    assert parsed["trace_id"] == "4bf92f3577b34da6a3ce929d0e0e4736"
    assert parsed["span_id"] == "00f067aa0ba902b7"
    assert parsed.traceparent == inbound

    generated = parse_or_generate_traceparent(None)
    assert len(generated["trace_id"]) == 32
    assert len(generated["span_id"]) == 16
    assert generated.traceparent.startswith("00-")
    assert generated["trace_id"] != "0" * 32
    assert generated["span_id"] != "0" * 16


def test_fastapi_middleware_sets_traceparent_response_header_static():
    source = Path("src/able_to_answer/api/main.py").read_text()

    assert '@app.middleware("http")' in source
    assert 'parse_or_generate_traceparent(request.headers.get("traceparent"))' in source
    assert 'response.headers["traceparent"] = trace_context.traceparent' in source


def test_trace_headers_propagate_request_scoped_context():
    inbound = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
    parsed = parse_or_generate_traceparent(inbound)
    tokens = set_log_context(trace_id=parsed["trace_id"], span_id=parsed["span_id"])
    try:
        assert trace_headers() == {
            "traceparent": inbound,
            "X-Trace-ID": "4bf92f3577b34da6a3ce929d0e0e4736",
        }
    finally:
        reset_log_context(tokens)


def test_control_plane_dispatch_returns_trace_context_for_downstream_static():
    source = Path("src/able_to_answer/control_plane/router.py").read_text()

    assert '"trace_context": trace_headers()' in source
    assert '"task_dispatched"' in source
    assert '"policy_decision"' in source


def test_redaction_rules_remove_secrets_sensitive_prompts_and_raw_tool_outputs():
    payload = redact(
        {
            "api_token": "tok_live_secret",
            "nested": {"password": "p@ssw0rd"},
            "data_tags": ["sensitive"],
            "prompt": "user private prompt",
            "raw_tool_output": {"stdout": "contains secrets"},
            "safe": "visible",
        }
    )

    assert payload["api_token"] == "[REDACTED]"
    assert payload["nested"]["password"] == "[REDACTED]"
    assert payload["prompt"] == "[REDACTED]"
    assert payload["raw_tool_output"] == "[REDACTED]"
    assert payload["safe"] == "visible"
