"""Command-line entrypoint for running the Able to Answer API server."""
from __future__ import annotations

import argparse
from collections.abc import Sequence

import uvicorn

APP_IMPORT_PATH = "able_to_answer.api.main:app"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Able to Answer API server.")
    parser.add_argument("--host", default="0.0.0.0", help="Interface to bind to.")
    parser.add_argument("--port", default=8000, type=int, help="Port to listen on.")
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Reload the server when source files change.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    uvicorn.run(APP_IMPORT_PATH, host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
