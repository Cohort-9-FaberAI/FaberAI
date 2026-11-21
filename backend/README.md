# FaberAI backend

FastAPI exposes the upload, analysis, report, and question-answering endpoints.
Celery runs CAD geometry extraction and deterministic DFM checks in the background.
See the root [quick start](../README.md#run-locally) to run everything in Docker.

## Native development

Use Python 3.13 or newer. From the repository root, create a virtual environment:

```sh
python -m venv .venv
```

Activate it with `.venv\Scripts\Activate.ps1` in PowerShell, or
`source .venv/bin/activate` on macOS/Linux. Then install development dependencies:

```sh
python -m pip install -r backend/requirements-dev.txt
docker compose up --detach redis
cd backend
```

Set `FABERAI_STORAGE_BACKEND=local` in each backend terminal:

```powershell
$env:FABERAI_STORAGE_BACKEND = 'local'
```

On macOS/Linux, use `export FABERAI_STORAGE_BACKEND=local`. Start the API and
worker in separate terminals, with the virtual environment active and `backend/`
as the working directory:

```sh
python -m uvicorn main:app --reload
python -m celery -A core.workers:celery_app worker --pool=solo --loglevel=info
```

The `solo` pool supports native Windows development. Docker uses Linux worker
processes so health checks remain responsive while CAD jobs run.

## Dependencies

| File | Purpose |
| --- | --- |
| `requirements-runtime.txt` | API, worker, STEP/STL geometry, PDF output, and report Q&A |
| `requirements-dev.txt` | Runtime plus pytest and Ruff; used by backend CI |
| `requirements-knowledge.txt` | Runtime plus optional embedding and tracing packages |
| `requirements.txt` | Combined development and knowledge environment for compatibility |

Direct runtime versions live in one file. Install only the groups you need.
build123d installs OCP bindings through pip; Conda is not required for the API.
The separate [Conda environment](README-DS.md) is for notebook and CAD experiments.

## Storage and configuration

Native runs default to Supabase unless local mode is selected explicitly. Local
mode stores SQLite records and CAD files in `backend/.data/`. Override this with
`FABERAI_DATA_DIR`; `FABERAI_PUBLIC_API_URL` controls the browser-visible file URL
(default `http://127.0.0.1:8000`).

Supabase mode needs `SUPABASE_URL`, `SUPABASE_KEY`, the `analysis_jobs` table, and a
public `cad-uploads` bucket. SQL definitions live in [database/migrations/](database/migrations/).
Native processes load `backend/.env` and accept exported environment variables.
Compose uses the root `.env` as documented in the [root configuration guide](../README.md#optional-configuration).

An LLM provider key is optional for report Q&A. Standards retrieval additionally
needs the knowledge packages, ingested reference documents, and Supabase vector
search. `FABERAI_PRELOAD_EMBEDDINGS=false` disables model loading at API startup.

## API map

Interactive schemas are available at http://localhost:8000/docs while the API runs.

| Route | Purpose |
| --- | --- |
| `GET /` | API liveness |
| `GET /health/dependencies` | Redis and worker readiness |
| `POST /upload/` | Store a STEP/STP or STL upload and queue analysis |
| `GET /tasks/{task_id}` | Poll analysis; accepts `analysis_id` for persisted results |
| `POST /dfm/evaluate` | Evaluate an existing geometry payload with DFM rules |
| `GET /analysis/{analysis_id}/dfm` | Read a completed stored report |
| `POST /analysis/report.pdf` | Generate a PDF from a completed analysis; supports inline preview |
| `POST /ai/ask` | Answer questions about a completed report |
| `POST /analysis/` | Store a validated analysis payload |
| `POST /analyze-mock` | Development fixture for the frontend API contract |
| `GET /mock-file` | Development STL fixture |
| `GET /files/{path}` | Serve uploads and previews in local storage mode |

## Checks

From `backend/`, with development dependencies installed:

```sh
python -m ruff check .
python -m pytest -q
```

Tests use temporary files and mocked cloud/queue transports. Geometry and local
storage tests exercise real CAD processing. Optional dependency cases and live
LLM benchmarks can skip; see the [geometry](tests/geometry/readme-tests.md) and
[AI benchmark](tests/ai_eval/README.md) guides.

To check actual running services from the repository root:

```sh
python scripts/smoke_test.py
python scripts/smoke_test.py --file path/to/part.step
```

See [ARCHITECTURE.md](../ARCHITECTURE.md) for module responsibilities and
[dfm/README-dfm.md](dfm/README-dfm.md) for rule configuration and scoring.
