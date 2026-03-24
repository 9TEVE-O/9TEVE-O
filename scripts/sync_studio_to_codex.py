#!/usr/bin/env python3
"""Governance Sync: Studio AI Registry → Codex Profiles.

Reads governance profiles from the Studio AI Registry API and upserts them
into the Codex API, then writes a compliance-event record to the Notion
Compliance database.

Environment variables consumed
------------------------------
``CODEX_API_TOKEN``          Codex API bearer token (required)
``STUDIO_REGISTRY_API_KEY``  Studio Registry API key (required)
``NOTION_TOKEN``             Notion integration token (required)
``NOTION_COMPLIANCE_DB``     Notion database ID for compliance events (required)
``STUDIO_REGISTRY_BASE_URL`` Base URL for Studio Registry API (optional; defaults to ``https://registry.studio.ai``)
``CODEX_BASE_URL``           Base URL for Codex API (optional; defaults to ``https://api.codex.ai``)
"""
from __future__ import annotations

import logging
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import json
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("sync_studio_to_codex")
logging.basicConfig(
    level=logging.INFO,
    format="[sync] %(levelname)s %(message)s",
)

# ---------------------------------------------------------------------------
# Configuration helpers
# ---------------------------------------------------------------------------

_STUDIO_REGISTRY_BASE = os.environ.get(
    "STUDIO_REGISTRY_BASE_URL", "https://registry.studio.ai"
)
_CODEX_BASE = os.environ.get("CODEX_BASE_URL", "https://api.codex.ai")
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
# Minimal HTTP helpers (stdlib only — no third-party required at import time)
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
# Studio Registry client
# ---------------------------------------------------------------------------


def fetch_studio_profiles(api_key: str) -> list[dict[str, Any]]:
    """Retrieve all governance profiles from the Studio AI Registry."""
    url = f"{_STUDIO_REGISTRY_BASE}/v1/governance-profiles"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "User-Agent": "able-to-answer-sync/1.0",
    }
    logger.info("Fetching governance profiles from Studio Registry …")
    data = _json_request("GET", url, headers)
    profiles: list[dict[str, Any]] = data if isinstance(data, list) else data.get("profiles", [])
    logger.info("Fetched %d profile(s) from Studio Registry.", len(profiles))
    return profiles


# ---------------------------------------------------------------------------
# Codex API client
# ---------------------------------------------------------------------------


def upsert_codex_profile(profile: dict[str, Any], api_token: str) -> None:
    """Upsert a single governance profile into Codex."""
    profile_id = profile.get("id", "unknown")
    url = f"{_CODEX_BASE}/v1/profiles/{urllib.parse.quote(str(profile_id), safe='')}"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "able-to-answer-sync/1.0",
    }
    _json_request("PUT", url, headers, body=profile)
    logger.info("Upserted Codex profile id=%s.", profile_id)


# ---------------------------------------------------------------------------
# Notion compliance-event logging
# ---------------------------------------------------------------------------


def log_compliance_event(
    notion_token: str,
    database_id: str,
    synced_count: int,
    failed_ids: list[str],
) -> None:
    """Write a compliance-event page to the Notion Compliance database."""
    url = f"{_NOTION_BASE}/pages"
    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Notion-Version": _NOTION_VERSION,
        "Content-Type": "application/json",
        "User-Agent": "able-to-answer-sync/1.0",
    }
    status = "Success" if not failed_ids else "Partial failure"
    now_iso = datetime.now(tz=timezone.utc).isoformat()
    page_body: dict[str, Any] = {
        "parent": {"database_id": database_id},
        "properties": {
            "Name": {
                "title": [{"text": {"content": f"Governance Sync — {now_iso}"}}]
            },
            "Status": {"select": {"name": status}},
            "Synced Count": {"number": synced_count},
            "Failed IDs": {
                "rich_text": [
                    {"text": {"content": ", ".join(failed_ids) or "none"}}
                ]
            },
            "Timestamp": {"date": {"start": now_iso}},
        },
    }
    _json_request("POST", url, headers, body=page_body)
    logger.info("Compliance event logged to Notion (status=%s).", status)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Orchestrate the Studio AI → Codex governance profile sync."""
    codex_token = _require_env("CODEX_API_TOKEN")
    studio_key = _require_env("STUDIO_REGISTRY_API_KEY")
    notion_token = _require_env("NOTION_TOKEN")
    notion_db = _require_env("NOTION_COMPLIANCE_DB")

    profiles = fetch_studio_profiles(studio_key)

    synced: list[str] = []
    failed: list[str] = []

    for profile in profiles:
        profile_id = str(profile.get("id", "unknown"))
        try:
            upsert_codex_profile(profile, codex_token)
            synced.append(profile_id)
        except RuntimeError as exc:
            logger.error("Failed to upsert profile id=%s: %s", profile_id, exc)
            failed.append(profile_id)

    logger.info(
        "Sync complete. synced=%d failed=%d", len(synced), len(failed)
    )

    log_compliance_event(
        notion_token=notion_token,
        database_id=notion_db,
        synced_count=len(synced),
        failed_ids=failed,
    )

    if failed:
        logger.error("One or more profiles failed to sync: %s", failed)
        sys.exit(1)


if __name__ == "__main__":
    main()
