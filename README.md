<div align="center">

# Subzteveø 🙃

### These pretzels are making me thirsty

<p>
Hi. Someone left the door open. Father of two boys, I wanted to know [WTF] what the future holds for the kids with all the AI bizzo. Ended up here. Broke some shiny stuff. Spoke to a robot (actually spoke to a dozen). Made some plastic stuff for out there. Met some cool people in here.
</p>

</div>

## able-to-answer local setup

This repository contains a single FastAPI service backed by SQLite. It does not require a separate frontend, database server, or Node.js development server.

### 1. Configure environment

Copy the example environment file and adjust values only if needed:

```bash
cp .env.example .env
```

The defaults are safe for local development. Do not commit real secrets or local `.env` files.

### 2. Install dependencies

Install the package and development dependencies into Python 3:

```bash
python3 -m pip install -e ".[dev]" --break-system-packages
```

### 3. Start the API

Run the FastAPI service with Python 3:

```bash
python3 -m able_to_answer --host 0.0.0.0 --port 8000
```

For autoreload during development, add `--reload`.

The health check is available at:

```text
GET http://localhost:8000/health
```

Expected response:

```json
{"status":"ok"}
```

### 4. Run tests

```bash
python3 -m pytest tests/ -v
```

## Deployment notes

Set production environment variables in the target hosting platform rather than committing them to the repository. At minimum, configure `ATA_DB_PATH` to an appropriate persistent SQLite path for the deployment environment.
