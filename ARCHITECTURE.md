# FaberAI — Architecture

## What it is

FaberAI is an AI-powered Design for Manufacturability (DFM) review platform for CAD parts. Engineers upload STEP or STL parts, the backend analyzes their geometry and DFM rules, and the UI displays a manufacturability score, issues, and 3D highlights.

The project ships three user-facing interfaces:

| Interface | Stack | Directory |
|---|---|---|
| Web app (primary) | React 19 + TypeScript + Vite + Three.js/R3F + Zustand | `frontend/` |
| Streamlit app (alternative) | Streamlit + trimesh + plotly | `streamlit-app/` |
| API + pipeline | FastAPI + Celery + Redis + Supabase | `backend/` |

---

## Repository Layout

```
FaberAI/
├── ARCHITECTURE.md
├── CONTRIBUTING.md
├── README.md
├── PRODUCT.md
├── docker-compose.yml
├── package-lock.json
├── .github/
│   └── workflows/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── ruff.toml
│   ├── environment-ds.yml
│   ├── README-DS.md
│   ├── app/
│   │   ├── schemas.py
│   │   ├── crud.py
│   │   ├── database.py
│   │   ├── observability.py
│   │   ├── services/
│   │   │   ├── storage.py
│   │   │   ├── geometry_engine_adapter.py
│   │   │   ├── report_pdf.py
│   │   │   ├── pdf_mesh_renderer.py
│   │   │   └── ai/
│   ├── core/
│   │   └── workers.py
│   ├── database/
│   │   └── migrations/01_create_analysis_jobs.sql
│   ├── datasets/
│   ├── dfm/
│   ├── geometry/
│   ├── notebooks/
│   └── tests/
├── frontend/
│   ├── .gitignore
│   ├── .prettierignore
│   ├── .prettierrc.json
│   ├── eslint.config.js
│   ├── index.html
│   ├── package.json
│   ├── package-lock.json
│   ├── README.md
│   ├── tsconfig.app.json
│   ├── tsconfig.json
│   ├── tsconfig.node.json
│   ├── vite.config.ts
│   ├── docs/
│   ├── public/
│   └── src/
├── streamlit-app/
│   ├── app.py
│   ├── README.md
│   └── requirements.txt
└── ref/
    └── ... (reference snapshot of the same project structure)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 19 + TypeScript + Vite 8 |
| 3D rendering | Three.js + @react-three/fiber + @react-three/drei |
| State | Zustand |
| Routing | React Router DOM v7 |
| Backend | FastAPI |
| Task queue | Celery |
| Broker / result backend | Redis |
| Database / storage | Supabase (PostgreSQL + Storage) |
| Validation | Pydantic v2 |
| STEP geometry | pythonOCC / OpenCASCADE (optional, Conda) |
| STL geometry | trimesh |
| DFM rules | Custom `backend/dfm/` rule engine |
| AI assistant | Deterministic assistant wrapper + optional LLM client |
| PDF export | FPDF + custom renderer |
| Linting | Ruff / ESLint / Prettier |
| Testing | pytest |
| CI | GitHub Actions |
| Python | 3.13 (backend CI), 3.11 (optional Conda DS env) |
| Node | 20 |

---

## Components

### 1. API — `backend/main.py`

The FastAPI application is the main HTTP entry point. It:
- loads DFM config once at startup
- configures CORS for development
- wraps errors into a standardized JSON envelope
- routes uploads, polling, mock analysis, report export, and AI Q&A

| Route | Method | Purpose |
|---|---|---|
| `/` | GET | Health check |
| `/health/dependencies` | GET | Verify Celery/Redis availability |
| `/upload/` | POST | Upload a CAD file, save to Supabase, create pending analysis, dispatch Celery task |
| `/tasks/{task_id}` | GET | Poll background task status; optional `analysis_id` query uses DB record for terminal state |
| `/analyze-mock` | POST | Return a hardcoded mock analysis for frontend development |
| `/analysis/` | POST | Persist a validated `AnalysisResult` payload in Supabase |
| `/dfm/evaluate` | POST | Run the DFM rule engine on supplied geometry |
| `/analysis/{analysis_id}/dfm` | GET | Fetch stored DFM report for a completed analysis |
| `/analysis/{analysis_id}/report.pdf` | GET | Download a PDF report for stored analysis |
| `/analysis/report.pdf` | POST | Download a PDF from an inline completed analysis payload |
| `/ai/ask` | POST | Answer a question from an existing DFM report or supplied report payload |
| `/mock-file` | GET | Serve a local mock STL file for development |

The API also includes STEP preview backfill logic for older stored analyses.

---

### 2. Web Layer — `backend/app/`

**`schemas.py`** defines the API contract:
- `AnalysisResult` stores analysis metadata, scores, issue list, geometry payload, DFM report, and preview URLs
- `Issue`, `ThreeJSHighlight`, `PartMetadata`, `BoundingBox`, `Vector3` support analysis and highlight geometry
- `AnalysisDBRecord` serializes Supabase rows
- `AnalysisStatus`, `IssueSeverity` enums

**`crud.py`** handles Supabase operations for `analysis_jobs`.

**`database.py`** initializes the Supabase client from env vars.

**`services/storage.py`** uploads CAD files to the `cad-uploads` bucket, validates formats and size limits, and returns public URLs.

**`services/geometry_engine_adapter.py`** converts raw geometry output into a JSON-friendly response contract.

**`services/ai/`** provides report-based question answering without rerunning geometry.

**`services/report_pdf.py`** generates PDF reports from completed analyses and DFM results.

---

### 3. Celery Worker — `backend/core/workers.py`

The worker manages the asynchronous CAD analysis lifecycle:
- Redis broker/backend from `REDIS_URL` (default `redis://localhost:6379/0`)
- `extract_geometry_task` with retries on network errors and exponential backoff

Task flow:
1. update status to `processing`
2. download CAD from Supabase Storage
3. save a temp file
4. run `run_geometry_engine()`
5. generate STEP preview STL for STEP uploads
6. run the DFM rule engine
7. flatten findings into issues
8. persist `results_json` and status in Supabase
9. set `completed` or `failed`

STEP dependency errors are treated as terminal failures instead of retried.

---

### 4. Geometry Engine — `backend/geometry/`

A standalone pure-Python geometry analysis package.

**Loaders** (`geometry/loaders/`):
- STEP via pythonOCC/OpenCASCADE (primary)
- STEP fallback path with build123d
- STL via trimesh

**Measurements** (`geometry/measurements/`):
- bbox, volume, surface area, centroid, inertia
- face extraction and graph building
- wall thickness sampling
- print orientations
- mesh reliability / repair
- surface classification

**Features** (`geometry/features/`):
- cylindrical hole detection
- boss detection
- cavity detection

**Models** (`geometry/models/`) define the internal geometry data shape.

Key points:
- STEP uses exact topology and surface classification for richer feature detection
- STL is mesh-based, with repair and mesh quality checks
- the geometry package is reusable without web dependencies

---

### 5. DFM Rule Engine — `backend/dfm/`

The DFM package provides deterministic manufacturability scoring and findings.
- `engine.py`
- `inputs.py`
- `models.py`
- `rules/`
- `scoring.py`
- `config/`

It is used by `/dfm/evaluate`, post-geometry scoring, and AI answer generation.

---

### 6. Database — `backend/database/`

The Supabase migration creates the `analysis_jobs` table:
- `analysis_id TEXT PRIMARY KEY`
- `filename TEXT NOT NULL`
- `status TEXT NOT NULL`
- `manufacturability_score FLOAT`
- `results_json JSONB`

RLS is enabled with a permissive dev policy.

---

### 7. Frontend — `frontend/`

A React + TypeScript + Vite single-page application.

Routes in `src/App.tsx`:
- `/landing`
- `/login`
- `/home`
- `/upload`
- `/analysis`
- `/projects`
- `/projects/:id`
- `/library`
- `/history`
- `/debug`
- `/extra-info`, `/conclusion`, `/download` redirect to `/analysis`

Key client modules:
- `src/lib/api.ts` — backend API wrappers
- `src/lib/useTaskPolling.ts` — task polling hook
- `src/lib/supabase.ts` — Supabase client init
- `src/store/index.ts` — Zustand state
- `src/components/ModelPreview/ModelPreview.tsx` — 3D viewer

Build tooling:
- Vite
- ESLint + Prettier
- Husky + lint-staged
- TypeScript strict mode

---

### 8. Streamlit App — `streamlit-app/`

Alternative local frontend for experimentation.
- `app.py` uploads STEP/STL files
- previews STL with trimesh + plotly
- polls backend task status
- downloads JSON results

---

### 9. CI/CD — `.github/workflows/`

| Workflow | Trigger | Jobs |
|---|---|---|
| `ci.yml` | backend changes / PRs | Python lint + pytest |
| `frontend-ci.yml` | frontend changes / PRs | npm lint + format check + build |

No deployment pipeline is configured yet.

---

## End-to-End Request Flow

```
Client (React / Streamlit)
  │
  │ POST /upload/
  ▼
FastAPI (`backend/main.py`)
  ├─ storage.py ──────────► Supabase Storage (`cad-uploads`)
  ├─ crud.py ─────────────► Supabase DB (`analysis_jobs`, status=pending)
  └─ workers.py ─ ─ ─ ─ ─► Redis (Celery broker/backend)
                                  │
                                  │ extract_geometry_task
                                  │
                                  ├─ download CAD file from Supabase Storage
                                  ├─ run_geometry_engine(tmp_path)
                                  │     └─ geometry/loaders/dispatcher.py
                                  │           ├─ STEP path: pythonOCC + build123d preview
                                  │           └─ STL path: trimesh + repair/reliability checks
                                  ├─ run_dfm_analysis()
                                  ├─ flatten findings into issues
                                  └─ crud.py ─ ─ ─ ─ ─ ─► Supabase DB (completed, results_json)
Client polls `/tasks/{task_id}` for status and final result
```
