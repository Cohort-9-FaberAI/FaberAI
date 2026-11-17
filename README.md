# FaberAI

FaberAI helps engineers assess whether CAD parts can be manufactured through
injection molding or 3D printing. Upload a STEP/STP or STL file, inspect the 3D
findings, review recommendations, and export a PDF report.

## Run locally

Install and start [Docker Desktop](https://www.docker.com/products/docker-desktop/)
with Linux containers. From the project root, run:

```sh
docker compose up --build
```

Open **http://localhost:5173** once the frontend starts. API documentation is at
http://localhost:8000/docs. The first build downloads dependencies; later starts
reuse the images and package layers.

Docker is the only required local tool. Compose builds the frontend and backend,
starts Redis and Celery, and waits for healthy analysis services before starting
the UI. No host Python, Node.js, Conda, Supabase account, or `.env` file is required.

- **CAD:** STEP/STP and STL support are included through pip-installed build123d
  and its OpenCASCADE bindings. Conda remains optional for notebooks.
- **Storage:** SQLite records, uploads, and generated previews persist in the
  `faberai-data` Docker volume, shared by the API and worker.
- **Report Q&A:** answers use the existing deterministic report-based fallback
  unless you configure an LLM provider key.
- **Reference standards:** ASME retrieval requires optional embedding packages
  and a configured Supabase knowledge base; it is separate from the default run.
- **Sign-in:** the UI currently uses a local demo sign-in; enter a username and
  password to continue. This does not create or authenticate an account.

To run in the background and wait for readiness:

```sh
docker compose up --build --detach --wait --wait-timeout 240
```

To stop, press Ctrl+C for the foreground command, or run:

```sh
docker compose down
```

Stopping preserves your data. `docker compose down --volumes` also **deletes local
analysis records, CAD uploads, and previews**.

## Optional configuration

Copy [`.env.example`](.env.example) to `.env` in the project root and change only
what you need. On PowerShell: `Copy-Item .env.example .env`.

| Setting | Purpose |
| --- | --- |
| `FABERAI_WEB_PORT` | Browser port; default `5173` |
| `FABERAI_API_PORT` | API port; default `8000` |
| `FABERAI_REDIS_PORT` | Local Redis port; default `6379` |
| `ANTHROPIC_API_KEY` | Enable provider-generated report answers |
| `FABERAI_AI_API_KEY`, `FABERAI_AI_BASE_URL`, `FABERAI_AI_MODEL` | Configure an Anthropic-compatible provider |
| `FABERAI_STORAGE_BACKEND` | `local` by default in Compose; set `supabase` for cloud storage |
| `SUPABASE_URL`, `SUPABASE_KEY` | Required only for Supabase storage |

Re-run `docker compose up --build` after configuration changes. API addresses are
compiled into the frontend, so changing the API port requires rebuilding it.
Services bind to localhost; this configuration is for local development.

Supabase mode uses the existing `analysis_jobs` table and `cad-uploads` bucket;
see [`backend/database/`](backend/database/) for database scripts. Switching
backends does not migrate local analyses. Embedding and tracing extras remain in
[`backend/requirements.txt`](backend/requirements.txt).

## Develop the frontend with hot reload

Start the backend services in Docker, then run Vite on your host with Node.js 22+:

```sh
docker compose up --build --detach --wait --wait-timeout 240 api
cd frontend
npm ci
npm run dev
```

If the containerized frontend is running, stop it with
`docker compose stop frontend` first to free port 5173. See
[`frontend/README.md`](frontend/README.md) for frontend commands and API settings.

## Run the backend without Conda

For native backend development, use Python 3.13+ and install
[`backend/requirements-runtime.txt`](backend/requirements-runtime.txt) in a virtual
environment. This includes STEP and STL support. From `backend/`, start the API
and worker in separate terminals using the same environment:

```sh
python -m uvicorn main:app --reload
python -m celery -A core.workers:celery_app worker --pool=solo --loglevel=info
```

Both terminals need `FABERAI_STORAGE_BACKEND=local`; on PowerShell use
`$env:FABERAI_STORAGE_BACKEND = 'local'`. Redis can still be started with
`docker compose up --detach redis` from the project root. Native local data is
stored in `backend/.data/`, ignored by Git. Native runs retain the existing
Supabase default unless local mode is explicitly selected.

## Troubleshooting

- **Cannot connect to Docker:** start Docker Desktop, wait for the engine, and
  check `docker info`. On Windows, use Linux containers.
- **Port already allocated:** stop the process using it or change the relevant
  port in the root `.env`, then run `docker compose up --build` again.
- **Analysis does not start:** run `docker compose ps` and
  `docker compose logs --tail=100 api worker redis`. The API dependency check is
  http://localhost:8000/health/dependencies.
- **Changed backend code:** run `docker compose up --build`. The default stack
  runs built images rather than mounting source files.
- **Check uploads and reports:** with the stack running, execute
  `python scripts/smoke_test.py` (Python standard library only).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for branch naming and PR conventions.
