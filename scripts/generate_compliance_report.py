"""Generate a monthly compliance report and publish it to Notion.

Queries all audit records from the local SQLite store, aggregates
them into a monthly summary, and creates a new page in the configured
Notion compliance-report database.

Required environment variables
-------------------------------
NOTION_TOKEN                 Notion integration token.
NOTION_COMPLIANCE_REPORT_DB  Notion database ID for compliance reports.

Optional environment variables (override defaults)
---------------------------------------------------
ATA_DB_PATH  Path to the SQLite database (default: able_to_answer.sqlite3).
"""

import logging
import os
import sqlite3
import sys
from datetime import datetime, timezone

logger = logging.getLogger("generate_compliance_report")
logging.basicConfig(level=logging.INFO, format="[report] %(levelname)s %(message)s")

_REPORT_MONTH = datetime.now(tz=timezone.utc).strftime("%Y-%m")


def _env(name: str, required: bool = True) -> str:
    """Read an environment variable; raise clearly if required and missing."""
    value = os.environ.get(name, "")
    if required and not value:
        raise RuntimeError(f"Required environment variable '{name}' is not set.")
    return value


def _collect_audit_summary(db_path: str) -> dict:
    """Return aggregate statistics from the audit table for the current month."""
    con = sqlite3.connect(db_path)
    try:
        cur = con.execute(
            """
            SELECT COUNT(*) AS total_queries,
                   COUNT(DISTINCT document_id) AS unique_documents,
                   AVG(elapsed_ms) AS avg_elapsed_ms
            FROM audit
            WHERE strftime('%Y-%m', created_at) = ?
            """,
            (_REPORT_MONTH,),
        )
        row = cur.fetchone()
        return {
            "total_queries": row[0] or 0,
            "unique_documents": row[1] or 0,
            "avg_elapsed_ms": round(row[2] or 0.0, 2),
        }
    finally:
        con.close()


def _publish_notion_report(notion_token: str, db_id: str, summary: dict) -> str:
    """Create a compliance-report page in Notion and return its URL."""
    import notion_client  # type: ignore[import-untyped]

    client = notion_client.Client(auth=notion_token)
    response = client.pages.create(
        parent={"database_id": db_id},
        properties={
            "Report Month": {"title": [{"text": {"content": _REPORT_MONTH}}]},
            "Total Queries": {"number": summary["total_queries"]},
            "Unique Documents": {"number": summary["unique_documents"]},
            "Avg Elapsed ms": {"number": summary["avg_elapsed_ms"]},
        },
    )
    return response.get("url", "<unknown>")


def main() -> int:
    notion_token = _env("NOTION_TOKEN")
    notion_db = _env("NOTION_COMPLIANCE_REPORT_DB")
    db_path = _env("ATA_DB_PATH", required=False) or "able_to_answer.sqlite3"

    logger.info("Generating compliance report for %s …", _REPORT_MONTH)

    summary = _collect_audit_summary(db_path)
    logger.info(
        "Total queries: %d | Unique documents: %d | Avg elapsed ms: %.2f",
        summary["total_queries"],
        summary["unique_documents"],
        summary["avg_elapsed_ms"],
    )

    url = _publish_notion_report(notion_token, notion_db, summary)
    logger.info("Compliance report published: %s", url)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except RuntimeError as exc:
        logger.error("%s", exc)
        sys.exit(1)
