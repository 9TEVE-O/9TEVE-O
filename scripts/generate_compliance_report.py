#!/usr/bin/env python3
"""Generate Monthly Compliance Report.

Queries the Notion Compliance database for events recorded in the current
month and creates a summary report page in the Compliance Report database.

Environment variables consumed
------------------------------
``NOTION_TOKEN``                Notion integration token (required)
``NOTION_COMPLIANCE_REPORT_DB`` Notion database ID to write the report into (required)
``NOTION_COMPLIANCE_DB``        Notion database ID to read compliance events from (optional;
                                defaults to the same value as NOTION_COMPLIANCE_REPORT_DB)
"""
from __future__ import annotations

import logging
import os
import sys
import urllib.error
import urllib.request
import json
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("generate_compliance_report")
logging.basicConfig(
    level=logging.INFO,
    format="[report] %(levelname)s %(message)s",
)

_NOTION_BASE = "https://api.notion.com/v1"
_NOTION_VERSION = "2022-06-28"


def _require_env(name: str) -> str:
    """Return the value of *name* or exit with a clear error."""
    value = os.environ.get(name, "").strip()
    if not value:
        logger.error("Required environment variable '%s' is not set.", name)
        sys.exit(1)
    return value


# ---------------------------------------------------------------------------
# Minimal HTTP helpers (stdlib only)
# ---------------------------------------------------------------------------


def _json_request(
    method: str,
    url: str,
    headers: dict[str, str],
    body: dict[str, Any] | None = None,
) -> Any:
    """Make a JSON HTTP request and return the parsed response body."""
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:  # noqa: S310
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode(errors="replace")
        raise RuntimeError(
            f"HTTP {exc.code} {method} {url}: {body_text}"
        ) from exc


# ---------------------------------------------------------------------------
# Notion helpers
# ---------------------------------------------------------------------------


def _notion_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": _NOTION_VERSION,
        "Content-Type": "application/json",
        "User-Agent": "able-to-answer-compliance/1.0",
    }


def query_compliance_events(
    notion_token: str,
    database_id: str,
    after: datetime,
    before: datetime,
) -> list[dict[str, Any]]:
    """Return compliance-event pages whose Timestamp falls within [after, before)."""
    url = f"{_NOTION_BASE}/databases/{database_id}/query"
    headers = _notion_headers(notion_token)
    filter_body: dict[str, Any] = {
        "filter": {
            "and": [
                {
                    "property": "Timestamp",
                    "date": {"on_or_after": after.isoformat()},
                },
                {
                    "property": "Timestamp",
                    "date": {"before": before.isoformat()},
                },
            ]
        }
    }
    pages: list[dict[str, Any]] = []
    has_more = True
    start_cursor: str | None = None

    while has_more:
        payload = dict(filter_body)
        if start_cursor:
            payload["start_cursor"] = start_cursor
        data = _json_request("POST", url, headers, body=payload)
        pages.extend(data.get("results", []))
        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor")

    logger.info(
        "Queried %d compliance event(s) from %s to %s.",
        len(pages),
        after.date(),
        before.date(),
    )
    return pages


def _extract_number(page: dict[str, Any], prop: str) -> int:
    """Safely extract a number property value from a Notion page."""
    try:
        return int(page["properties"][prop]["number"] or 0)
    except (KeyError, TypeError, ValueError):
        return 0


def _extract_select(page: dict[str, Any], prop: str) -> str:
    """Safely extract a select property value from a Notion page."""
    try:
        return page["properties"][prop]["select"]["name"]
    except (KeyError, TypeError):
        return "Unknown"


def _extract_rich_text(page: dict[str, Any], prop: str) -> str:
    """Safely extract plain text from a Notion rich_text property."""
    try:
        parts = page["properties"][prop]["rich_text"]
        return "".join(rt.get("plain_text", "") for rt in parts)
    except (KeyError, TypeError):
        return ""


def create_report_page(
    notion_token: str,
    report_database_id: str,
    period_label: str,
    total_events: int,
    total_synced: int,
    total_failed: int,
    success_count: int,
    partial_count: int,
) -> None:
    """Create a summary compliance-report page in the Notion Report database."""
    url = f"{_NOTION_BASE}/pages"
    headers = _notion_headers(notion_token)
    now_iso = datetime.now(tz=timezone.utc).isoformat()
    overall_status = "Pass" if total_failed == 0 else "Review Required"
    page_body: dict[str, Any] = {
        "parent": {"database_id": report_database_id},
        "properties": {
            "Name": {
                "title": [
                    {"text": {"content": f"Compliance Report — {period_label}"}}
                ]
            },
            "Period": {"rich_text": [{"text": {"content": period_label}}]},
            "Overall Status": {"select": {"name": overall_status}},
            "Total Sync Events": {"number": total_events},
            "Total Profiles Synced": {"number": total_synced},
            "Total Profiles Failed": {"number": total_failed},
            "Successful Syncs": {"number": success_count},
            "Partial Failures": {"number": partial_count},
            "Generated At": {"date": {"start": now_iso}},
        },
    }
    _json_request("POST", url, headers, body=page_body)
    logger.info(
        "Compliance report created for period=%s (status=%s).",
        period_label,
        overall_status,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Query this month's compliance events and write a summary report."""
    notion_token = _require_env("NOTION_TOKEN")
    report_db = _require_env("NOTION_COMPLIANCE_REPORT_DB")
    # The source compliance events DB may be separate; fall back to report DB.
    source_db = os.environ.get("NOTION_COMPLIANCE_DB", "").strip() or report_db

    now = datetime.now(tz=timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    # First day of next month as the exclusive upper bound.
    if month_start.month == 12:
        month_end = month_start.replace(year=month_start.year + 1, month=1)
    else:
        month_end = month_start.replace(month=month_start.month + 1)

    period_label = month_start.strftime("%B %Y")
    logger.info("Generating compliance report for %s …", period_label)

    events = query_compliance_events(
        notion_token=notion_token,
        database_id=source_db,
        after=month_start,
        before=month_end,
    )

    total_synced = sum(_extract_number(p, "Synced Count") for p in events)
    total_failed = sum(
        len(
            [
                fid.strip()
                for fid in _extract_rich_text(p, "Failed IDs").split(",")
                if fid.strip() and fid.strip() != "none"
            ]
        )
        for p in events
    )
    success_count = sum(
        1 for p in events if _extract_select(p, "Status") == "Success"
    )
    partial_count = sum(
        1 for p in events if _extract_select(p, "Status") == "Partial failure"
    )

    create_report_page(
        notion_token=notion_token,
        report_database_id=report_db,
        period_label=period_label,
        total_events=len(events),
        total_synced=total_synced,
        total_failed=total_failed,
        success_count=success_count,
        partial_count=partial_count,
    )

    logger.info(
        "Report complete. events=%d synced=%d failed=%d",
        len(events),
        total_synced,
        total_failed,
    )


if __name__ == "__main__":
    main()
