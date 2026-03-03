Hi there. I am Subzteveø

### Focus areas
- **AI-assisted music production** (Ableton Live, offline / local-first)
- **Agentic AI systems** (tool-enabled, multi-agent workflows)
- **Document intelligence & NLP** (structured extraction, RAG, evidence-first summaries)
- **AI safety, governance, and licensing-aware deployment**
- **Open-source AI tooling and ML pipelines**

### Document-to-Decision Intelligence
Agent-driven NLP for policy and compliance work.
- Structured extraction (entities, obligations, risks)
- Evidence-linked summaries
- Knowledge-base and RAG architecture

---

## able-to-answer

Governance-grade AI document intelligence: ingest text documents, retrieve relevant
chunks via lexical overlap, construct extractive answers, and produce a full audit
trail — all without an external LLM dependency in the MVP.

### Prerequisites

- Python ≥ 3.11 (CI tests on 3.12)
- pip

### Install

```bash
pip install -e ".[dev]"
```

### Run locally

```bash
make run
# or directly:
uvicorn able_to_answer.api.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### Run tests

```bash
python -m pytest tests/ -v
```

### Environment variables

Copy `.env.example` to `.env` and adjust values as needed.

| Variable | Default | Description |
|---|---|---|
| `ATA_DB_PATH` | `able_to_answer.sqlite3` | Path to the SQLite database file |
| `ATA_CHUNK_SIZE_CHARS` | `1200` | Maximum characters per ingestion chunk |
| `ATA_CHUNK_OVERLAP_CHARS` | `200` | Overlap in characters between consecutive chunks |
| `ATA_MAX_CONTEXT_CHUNKS` | `6` | Maximum chunks retrieved per query |
| `ATA_MAX_ANSWER_CHARS` | `1800` | Maximum characters in the extractive answer |

### GitHub Copilot CLI

[GitHub Copilot CLI](https://github.com/github/copilot-cli) brings AI-powered coding assistance directly to your terminal, making it easy to explore, edit, and debug this codebase without leaving the command line.

#### Install

```bash
# macOS / Linux (review the script at https://gh.io/copilot-install before running)
curl -fsSL https://gh.io/copilot-install | bash

# macOS (Homebrew)
brew install copilot-cli

# Windows (WinGet)
winget install GitHub.Copilot

# npm (all platforms)
npm install -g @github/copilot
```

#### Launch

```bash
copilot
```

On first launch you will be prompted to authenticate with your GitHub account (requires an active Copilot subscription). You can also authenticate with a fine-grained Personal Access Token that has the **Copilot Requests** permission set via the `GH_TOKEN` or `GITHUB_TOKEN` environment variable.

#### Useful workflows for this project

| Goal | Example prompt |
|---|---|
| Understand the ingestion pipeline | `Explain how text is chunked and stored in able_to_answer/ingestion/` |
| Add a new API route | `Add a DELETE /documents/{id} route following the existing patterns in api/main.py` |
| Run and interpret tests | `Run the test suite and explain any failures` |
| Explore retrieval scoring | `How does the lexical overlap scorer in retrieval/ rank chunks?` |
| Debug a failing audit | `Why might build_audit_pack return an empty citations list?` |

Launch `copilot` from the repository root so the agent has full access to the source tree. Use `/model` to switch between available models and `/feedback` to submit feedback to the Copilot CLI team.

### How to contribute

1. Fork the repo and create a branch: `git checkout -b your-feature`
2. Make changes, write tests, ensure `python -m pytest tests/ -v` passes
3. Open a PR using the template in `.github/PULL_REQUEST_TEMPLATE.md`
4. Commit messages follow `[scope] verb: description` (see `.github/copilot-instructions.md`)

### Licence

No licence has been specified for this repository. All rights reserved by the author unless otherwise stated.

---

## Performance Optimization Resources

High-quality code requires high performance. These guides help identify and fix slow or inefficient code:

📘 **[Performance Optimization Guide](PERFORMANCE_OPTIMIZATION_GUIDE.md)** - Comprehensive guide covering:
- Profiling and benchmarking techniques
- Algorithm and data structure optimization
- Python-specific best practices
- ML/AI performance optimization
- Database and I/O improvements
- NLP and document processing efficiency

✅ **[Code Performance Checklist](CODE_PERFORMANCE_CHECKLIST.md)** - Quick reference for code reviews:

🧪 **[Performance Review Report](PERFORMANCE_REVIEW_REPORT.md)** - Prioritized bottlenecks and refactor proposals with before/after examples.

- Common performance anti-patterns to avoid
- Language-specific issues to catch
- Database and query optimization
- Memory management best practices
- Concurrency and parallelism guidelines
