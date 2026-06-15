"""Tests for the package command-line entrypoint."""
from __future__ import annotations

from able_to_answer.__main__ import APP_IMPORT_PATH, build_parser


def test_cli_defaults_match_api_app():
    args = build_parser().parse_args([])

    assert APP_IMPORT_PATH == "able_to_answer.api.main:app"
    assert args.host == "0.0.0.0"
    assert args.port == 8000
    assert args.reload is False


def test_cli_accepts_server_options():
    args = build_parser().parse_args(["--host", "127.0.0.1", "--port", "9000", "--reload"])

    assert args.host == "127.0.0.1"
    assert args.port == 9000
    assert args.reload is True
