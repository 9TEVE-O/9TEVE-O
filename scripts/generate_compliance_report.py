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

When required variables are absent the script logs a warning and exits
with code 0 so that the CI workflow is not marked as failing just because
the integration secrets have not been configured yet.
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
    """Return aggregate statistics from the audits table for the current month.

    ``created_at`` is stored as an INTEGER unix timestamp, so we convert it
    with ``datetime(created_at, 'unixepoch')`` before formatting.
    """
    con = sqlite3.connect(db_path)
    try:
        cur = con.execute(
            """
            SELECT COUNT(*) AS total_queries,
                   COUNT(DISTINCT document_id) AS unique_documents
            FROM audits
            WHERE strftime('%Y-%m', datetime(created_at, 'unixepoch')) = ?
            """,
            (_REPORT_MONTH,),
        )
        row = cur.fetchone()
        return {
            "total_queries": row[0] or 0,
            "unique_documents": row[1] or 0,
        }
    finally:
        con.close()


def _publish_notion_report(notion_token: str, db_id: str, summary: dict) -> str:
    """Create a compliance-report page in Notion and return its URL."""
    # Imported locally so that the module loads successfully even when
    # notion-client is not installed (it is only required for Notion integration).
    import notion_client  # type: ignore[import-untyped]

    client = notion_client.Client(auth=notion_token)
    response = client.pages.create(
        parent={"database_id": db_id},
        properties={
            "Report Month": {"title": [{"text": {"content": _REPORT_MONTH}}]},
            "Total Queries": {"number": summary["total_queries"]},
            "Unique Documents": {"number": summary["unique_documents"]},
        },
    )
    return response.get("url", "<unknown>")


def main() -> int:
    try:
        notion_token = _env("NOTION_TOKEN")
        notion_db = _env("NOTION_COMPLIANCE_REPORT_DB")
    except RuntimeError as exc:
        logger.warning(
            "%s — compliance report skipped (configure secrets to enable).", exc
        )
        return 0

    db_path = _env("ATA_DB_PATH", required=False) or "able_to_answer.sqlite3"

    logger.info("Generating compliance report for %s …", _REPORT_MONTH)

    summary = _collect_audit_summary(db_path)
    logger.info(
        "Total queries: %d | Unique documents: %d",
        summary["total_queries"],
        summary["unique_documents"],
    )

    url = _publish_notion_report(notion_token, notion_db, summary)
    logger.info("Compliance report published: %s", url)
    return 0


if __name__ == "__main__":
    sys.exit(main())
