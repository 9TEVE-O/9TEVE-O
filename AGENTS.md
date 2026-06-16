# AGENTS.md

## Cursor Cloud specific instructions

`able-to-answer` is a single FastAPI service (ingest → retrieve → answer → audit) backed by
SQLite via the stdlib `sqlite3`. There is no separate frontend, database server, or other
service to start. Standard commands live in `CLAUDE.md` and the `Makefile`; the notes below
only cover non-obvious caveats for this environment.

- **Use `python3`, not `python`.** This VM has no `python`/`python` symlink, so the
  `Makefile` targets (`make run`, `make test`) and the `CLAUDE.md` commands that call `python`
  will fail with "command not found". Run modules directly with `python3` instead.
- **Dependencies are installed into system Python** (the update script runs
  `pip install -e ".[dev]" --break-system-packages`). Console entry points (`uvicorn`,
  `pytest`, `able-to-answer`) are placed in `~/.local/bin`, which is not on `PATH`. Always
  invoke tools as modules: `python3 -m pytest`, `python3 -m able_to_answer`.
- **Run tests:** `python3 -m pytest tests/ -v` (244 tests, all passing). `pyproject.toml`
  already sets `pythonpath = ["src"]`, so no manual `PYTHONPATH` is needed for pytest.
- **Run the API (dev):** `PYTHONPATH=src python3 -m able_to_answer --host 0.0.0.0 --port 8000`
  (add `--reload` for autoreload). Health check: `GET /health` → `{"status":"ok"}`.
- **No lint tooling is configured** (no ruff/flake8/black/pre-commit). CI (`.github/workflows/ci.yml`)
  runs only `python3 -m pytest`.
- **SQLite DB** is created on demand at `ATA_DB_PATH` (default `able_to_answer.sqlite3` in the
  working dir) and is gitignored. Copy `.env.example` to `.env` to override defaults; no real
  secrets are required to run or test the app.
