"""Fetch Studio AI governance profiles from the Studio Registry.

Reads registered AI profiles from the Studio Registry API and logs
their IDs.  Results are emitted via the module logger so the CI workflow
can capture them in a log artifact.

Required environment variables
-------------------------------
STUDIO_REGISTRY_API_KEY      API key for the Studio Registry.
STUDIO_REGISTRY_BASE         Base URL for the Studio Registry API.
NOTION_TOKEN                 (optional) Notion integration token for status updates.
NOTION_COMPLIANCE_DB         (optional) Notion database ID to record sync outcomes.
"""

import logging
import os
import sys

import requests

logger = logging.getLogger("sync_studio_to_codex")
logging.basicConfig(level=logging.INFO, format="[sync] %(levelname)s %(message)s")


def _env(name: str, required: bool = True) -> str:
    """Read an environment variable; raise clearly if required and missing."""
    value = os.environ.get(name, "")
    if required and not value:
        raise RuntimeError(f"Required environment variable '{name}' is not set.")
    return value


def _fetch_studio_profiles(base: str, api_key: str) -> list[dict]:
    """Return all AI profiles from the Studio Registry."""
    resp = requests.get(
        f"{base}/profiles",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["profiles"]


def _record_notion_outcome(
    notion_token: str, db_id: str, profile_id: str, status: str
) -> None:
    """Append a sync-outcome row to the Notion compliance database."""
    import notion_client  # type: ignore[import-untyped]

    client = notion_client.Client(auth=notion_token)
    client.pages.create(
        parent={"database_id": db_id},
        properties={
            "Profile ID": {"title": [{"text": {"content": profile_id}}]},
            "Status": {"select": {"name": status}},
        },
    )


def main() -> int:
    registry_key = _env("STUDIO_REGISTRY_API_KEY")
    studio_base = _env("STUDIO_REGISTRY_BASE")
    notion_token = _env("NOTION_TOKEN", required=False)
    notion_db = _env("NOTION_COMPLIANCE_DB", required=False)

    profiles = _fetch_studio_profiles(studio_base, registry_key)
    logger.info("Fetched %d profile(s) from Studio Registry.", len(profiles))

    for profile in profiles:
        profile_id = profile.get("id", "<unknown>")
        profile_name = profile.get("name", "<unnamed>")
        profile_version = profile.get("version", "<unknown>")
        logger.info("[OK] id=%s name=%s version=%s", profile_id, profile_name, profile_version)
        if notion_token and notion_db:
            _record_notion_outcome(notion_token, notion_db, profile_id, "fetched")

    logger.info("Governance profile fetch completed successfully.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except RuntimeError as exc:
        logger.error("%s", exc)
        sys.exit(1)
