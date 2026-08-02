# FaberAI — Architecture

## What it is

FaberAI is an **AI-powered Design for Manufacturability (DFM) review tool**. Engineers upload a CAD part (STEP or STL) and get back a manufacturability score, a list of issues, and 3D bounding-box highlights that pinpoint problem areas in a Three.js viewer.

The project ships three user-facing interfaces:

| Interface | Stack | Directory |
|---|---|---|
| Web app (primary) | React 19 + TypeScript + Vite + Three.js/R3F + Zustand | `frontend/` |
| Streamlit app (alternative) | Streamlit + trimesh + plotly | `streamlit-app/` |
| API | FastAPI + Celery + Redis | `backend/` |

---

## Repository Layout

```
FaberAI/
├── ARCHITECTURE.md                     # This document
├── CONTRIBUTING.md                     # Branch naming, PR conventions
├── README.md                           # Top-level project overview
├── docker-compose.yml                  # Redis container (Celery broker/backend)
├── package-lock.json                   # Root lockfile (husky setup)
├── .github/
│   ├── pull_request_template.md
│   └── workflows/
│       ├── ci.yml                      # Backend CI: lint (ruff) + test (pytest)
│       └── frontend-ci.yml             # Frontend CI: lint + format check + build
├── backend/                            # All server-side Python code
│   ├── .gitignore
│   ├── main.py                         # FastAPI app + route definitions
│   ├── requirements.txt                # Pinned pip dependencies
│   ├── ruff.toml                       # Linter configuration
│   ├── environment-ds.yml              # Conda env for OCC / data-science work
│   ├── README-DS.md                    # Conda environment setup guide
│   ├── app/                            # Web layer (schemas, DB access, services)
│   │   ├── README-app.md
│   │   ├── schemas.py                  # Pydantic API contracts
│   │   ├── crud.py                     # Supabase table operations
│   │   ├── database.py                 # Supabase client singleton
│   │   └── services/
│   │       ├── storage.py              # Upload CAD files to Supabase Storage
│   │       └── geometry_engine_adapter.py  # Adapter between worker and geometry engine
│   ├── core/
│   │   └── workers.py                  # Celery task definition
│   ├── database/
│   │   └── migrations/
│   │       └── 01_create_analysis_jobs.sql
│   ├── datasets/                       # Sample CAD files for testing
│   │   ├── STEP/                       # 25 .stp mechanical parts
│   │   ├── STL/                        # 5 .stl meshes
│   │   └── OPTIC/                      # 4 fresnel lens .stl files + 1 .stp
│   ├── geometry/                       # Pure geometry engine (no web dependencies)
│   │   ├── features/                   # DFM feature extractors (holes, bosses, cavities)
│   │   │   ├── __init__.py
│   │   │   ├── bosses.py
│   │   │   ├── cavities.py
│   │   │   ├── holes.py
│   │   │   └── README-features.md
│   │   ├── loaders/                    # File ingestion (STEP via OCC, STL via trimesh)
│   │   │   ├── __init__.py
│   │   │   ├── dispatcher.py
│   │   │   ├── exceptions.py
│   │   │   ├── step_loader.py
│   │   │   ├── step_loader_pythonocc.py
│   │   │   ├── stl_loader.py
│   │   │   └── stl_loader_trimesh.py
│   │   ├── measurements/               # Dual OCC/mesh measurement implementations
│   │   │   ├── __init__.py
│   │   │   ├── area.py
│   │   │   ├── bbox.py
│   │   │   ├── centroid.py
│   │   │   ├── face_extraction.py
│   │   │   ├── face_graph.py
│   │   │   ├── face_measurements.py
│   │   │   ├── faceangles.py
│   │   │   ├── inertia.py
│   │   │   ├── print_orientations.py
│   │   │   ├── reliability.py
│   │   │   ├── surface_classifier.py
│   │   │   ├── volume.py
│   │   │   └── wall_thickness.py
│   │   ├── models/                     # Geometry data model (dataclasses + enums)
│   │   │   ├── __init__.py
│   │   │   ├── boss.py
│   │   │   ├── bounding_box.py
│   │   │   ├── cavity.py
│   │   │   ├── edge.py
│   │   │   ├── enums.py
│   │   │   ├── face_graph_model.py
│   │   │   ├── face.py
│   │   │   ├── geometry_model.py
│   │   │   ├── hole.py
│   │   │   ├── mesh_quality.py
│   │   │   └── wall_sample.py
│   ├── notebooks/
│   │   └── README-ntbk.md
│   └── tests/                          # pytest suite
│       ├── conftest.py
│       ├── test_main.py
│       ├── tests_extended.py
│       └── geometry/
│           ├── readme-tests.md
│           ├── test_features.py
│           ├── test_measurements.py
│           └── test_step_optional.py
├── frontend/                           # React + TypeScript + Vite web client
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
│   │   └── api-contract-analyze-mock.md  # API contract sync notes (Track B)
│   ├── public/
│   │   ├── favicon.svg
│   │   └── icons.svg
│   └── src/
│       ├── App.css
│       ├── App.tsx                     # React Router v7 routes
│       ├── index.css
│       ├── main.tsx                    # React 19 entry point
│       ├── assets/
│       │   ├── hero.png
│       │   ├── react.svg
│       │   └── vite.svg
│       ├── components/
│       │   ├── analysis/
│       │   │   ├── IssueAccordion.tsx
│       │   │   └── SeverityLegend.tsx
│       │   ├── common/
│       │   │   ├── Modal.tsx
│       │   │   └── ModelPreviewPlaceholder.tsx
│       │   ├── extra-info/
│       │   │   └── ProcessToggle.tsx
│       │   ├── home/
│       │   │   ├── FileCard.tsx
│       │   │   └── UploadDropzone.tsx
│       │   ├── layout/
│       │   │   ├── AppShell.tsx
│       │   │   ├── AskFaberAIButton.tsx
│       │   │   ├── Sidebar.tsx
│       │   │   ├── StepIndicator.tsx
│       │   │   └── UsageIndicator.tsx
│       │   └── ModelPreview/
│       │       ├── ModelPreview.module.css
│       │       └── ModelPreview.tsx      # Three.js / R3F 3D viewer
│       ├── lib/
│       │   ├── api.ts                    # fetch-based API client
│       │   ├── supabase.ts               # Supabase JS client (auth placeholder)
│       │   └── useTaskPolling.ts         # React hook for task status polling
│       ├── pages/
│       │   ├── AnalysisPage.tsx
│       │   ├── DebugApiPage.tsx
│       │   ├── ExtraInfoPage.tsx
│       │   ├── UploadPage.tsx
│       │   └── LoginPage.tsx
│       └── store/
│           └── index.ts                  # Zustand store (project, file, analysis, chat)
└── streamlit-app/                      # Alternative frontend (Streamlit)
    ├── app.py                          # Upload + STL preview + task polling
    ├── README.md
    └── requirements.txt
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend framework** | React 19 + TypeScript + Vite 8 |
| **3D rendering** | Three.js + @react-three/fiber + @react-three/drei |
| **State management** | Zustand |
| **Routing** | React Router DOM v7 |
| **Backend API** | FastAPI 0.139 + Uvicorn |
| **Data validation** | Pydantic v2 |
| **Async task queue** | Celery 5.6 |
| **Message broker / result backend** | Redis (Docker) |
| **Database** | Supabase (PostgreSQL) |
| **Object storage** | Supabase Storage (`cad-uploads` bucket) |
| **DB client** | supabase-py / postgrest |
| **STEP geometry kernel** | pythonOCC / OpenCASCADE (optional, Conda) |
| **STL geometry kernel** | trimesh + manifold3d |
| **Graph algorithms** | NetworkX |
| **Numerics** | NumPy, SciPy |
| **Alternative frontend** | Streamlit + trimesh + plotly |
| **Linting** | Ruff (pinned 0.14.3 in CI) / ESLint / Prettier |
| **Testing** | pytest |
| **CI** | GitHub Actions (backend + frontend) |
| **Pre-commit** | Husky + lint-staged |
| **Python version** | 3.13 (CI) / 3.11 (conda DS env) |
| **Node version** | 20 (CI) |

---

## Components

### 1. API — `backend/main.py`

The FastAPI application. All routes are defined here; no routers are used.

| Route | Method | Description |
|---|---|---|
| `/` | GET | Health check — returns `{"status": "ok", ...}` |
| `/upload/` | POST | Accept CAD file → upload to Supabase Storage → create DB record → dispatch Celery task. Returns `task_id` + `analysis_id`. |
| `/tasks/{task_id}` | GET | Poll Celery and Supabase for job status and result. Prefers the DB record so the UI sees `completed`/`failed` immediately. |
| `/analyze-mock` | POST | Hardcoded mock response (thin wall + deep pocket issues) to unblock frontend development. |
| `/analysis/` | POST | Directly insert a validated `AnalysisResult` into Supabase (DB integration test). |
| `/mock-file` | GET | Serves the mock STL file directly to bypass CORS during local development. |

CORS is configured with `allow_origins=["*"]` for development.

All error responses use a standardized envelope:

```json
{
  "error": {
    "code": 422,
    "type": "validation_error",
    "message": "Request validation failed.",
    "details": [...]
  }
}
```

Custom exception handlers cover HTTP errors, Pydantic validation errors, and unhandled exceptions.

---

### 2. Web Layer — `backend/app/`

**`schemas.py`** — Pydantic models (the API contract):

| Model | Purpose |
|---|---|
| `AnalysisResult` | Top-level job result: `analysis_id`, `filename`, `status`, `manufacturability_score`, `summary`, `part_metadata`, `issues[]`, `geometry_data` |
| `Issue` | Single DFM issue: `issue_id`, `type`, `severity` (high/medium/low), `message`, `recommendation`, `three_js_highlight` |
| `ThreeJSHighlight` | AABB bounding box (`min`, `max`, `center`, `color`) for 3D canvas highlighting |
| `AnalysisDBRecord` | Flattened row for Supabase insertion; stores full payload as `results_json` (JSONB) |
| `PartMetadata`, `BoundingBox`, `Vector3` | Supporting sub-models |
| `AnalysisStatus` | Enum: `pending`, `processing`, `completed`, `failed` |
| `IssueSeverity` | Enum: `high`, `medium`, `low` |

**`database.py`** — Supabase client singleton. Reads `SUPABASE_URL` + `SUPABASE_KEY` from `.env`. Raises `EnvironmentError` at import time if either is missing.

**`crud.py`** — Three operations against the `analysis_jobs` table:
- `insert_analysis_result()` — wraps in `AnalysisDBRecord` and inserts
- `get_analysis_by_id()` — single-row fetch by UUID (returns `None` if not found)
- `update_analysis_status()` — partial update (status + optional extra fields)

**`services/storage.py`** — Uploads raw CAD bytes to the `cad-uploads` Supabase Storage bucket. Prefixes filenames with a UUID to prevent collisions. Returns `storage_path`, `public_url`, `original_filename`.

**`services/geometry_engine_adapter.py`** — Adapter (anti-corruption layer) between the Celery worker and the geometry engine:
- Defines `GeometryEngineResponse` — a Pydantic model that mirrors `GeometryModel` but is fully JSON-serializable
- `run_geometry_engine(file_path, original_filename)` — the single function the worker calls; calls `load_geometry()` then maps to the response contract
- Manufacturability score is currently a placeholder: **85** if mesh is reliable, **55** if not

---

### 3. Celery Worker — `backend/core/workers.py`

Single task: `extract_geometry_task`

- **Broker/backend:** Redis at `redis://localhost:6379/0`
- **Retries:** 3 attempts, exponential backoff up to 60 s, auto-retries on `requests` network errors
- **Lifecycle:**
  1. Set Supabase status → `processing`
  2. Download CAD file from Supabase Storage into a named `tempfile`
  3. Call `run_geometry_engine(tmp_path, original_filename)`
  4. Set status → `completed`, store `results_json` + `mock_score`
  5. On exhausted retries: set status → `failed`
  6. `finally` block always deletes the temp file
- **STEP handling:** `StepSupportUnavailableError` (missing optional pythonocc-core/build123d) is caught and marks the analysis `failed` immediately — no retry, since installing dependencies won't happen automatically.

---

### 4. Geometry Engine — `backend/geometry/`

A self-contained pure-Python package. Zero FastAPI or Celery imports — usable standalone, in notebooks, or replaceable without touching the web layer.

#### 4a. Models — `geometry/models/`

| File | Purpose |
|---|---|
| `geometry_model.py` | `GeometryModel` dataclass — the main result object |
| `bounding_box.py` | `BoundingBox` — AABB or OBB; numpy `min_corner`/`max_corner`; `width`/`depth`/`height` properties |
| `face.py` | `Face` — `id`, `area`, `centroid`, `normal`, `surface_type`, `adjacent_faces[]`, `edge_ids[]` |
| `edge.py` | `Edge` — `id`, `length`, `curve_type`, `start_point`, `end_point`, `dihedral_angle`, `convex` |
| `wall_sample.py` | `WallSample` — one local wall thickness measurement |
| `mesh_quality.py` | `MeshQuality` dataclass + `check_mesh_quality()` — watertight, winding, volume flags (STL only) |
| `hole.py` | `Hole` — cylindrical hole (through, blind, counterbore, countersink) |
| `boss.py` | `Boss` — cylindrical protrusion |
| `cavity.py` | `Cavity` — internal pocket/recess |
| `enums.py` | `SourceFormat` (STEP/STL), `SurfaceType` (plane/cylinder/sphere/cone/torus/bspline/unknown), `CurveType` (line/circle/ellipse/spline/unknown) |
| `face_graph_model.py` | `FaceGraphModel` — typed NetworkX graph wrapper with `FaceInfo`/`EdgeInfo`; JSON-serializable |

`GeometryModel` fields:

```
source_format, source_path
bounding_box, oriented_bbox
volume_mm3, surface_area_mm2
center_mass, moment_of_inertia   # 3×3 numpy array about CoM
measurements_reliable            # False when mesh couldn't be repaired
raw                              # Native object (TopoDS_Shape or trimesh.Trimesh)
faces[], edges[], wall_samples[]
nominal_wall, face_graph
wall_thickness_stats             # WallThicknessStats
mesh_quality                     # MeshQuality (STL only; None for STEP)
print_orientations               # PrintOrientationAnalysis
holes[], bosses[], cavities[]    # Cylindrical manufacturing features
```

#### 4b. Loaders — `geometry/loaders/`

Public API: `load_geometry(path: str) -> GeometryModel` (from `__init__.py`).

| File | Purpose |
|---|---|
| `dispatcher.py` | Detects format by extension, dispatches to the right loader, populates a complete `GeometryModel` |
| `step_loader_pythonocc.py` | Primary STEP loader (pythonOCC) |
| `step_loader.py` | Legacy STEP loader (build123d + trimesh) |
| `stl_loader_trimesh.py` | Primary STL loader (trimesh) |
| `stl_loader.py` | Original trimesh wrapper |
| `exceptions.py` | `StepSupportUnavailableError` — raised when STEP deps are missing |

**Dual-path strategy:**
- `.step` / `.stp` → pythonOCC (primary) or build123d (fallback) — exact B-rep math, no mesh reliability concerns, full face/edge topology extraction, cylindrical feature detection
- `.stl` → trimesh — mesh-based, includes repair attempt + `measurements_reliable` flag, mesh quality check, wall thickness sampling

**Feature detection** (holes, bosses, cavities) runs on the STEP path only. The STL path intentionally leaves these empty because mesh faces lack surface-type classification (no cylinder/plane distinction without real curvature analysis on a triangle soup).

#### 4c. Measurements — `geometry/measurements/`

Every measurement has parallel OCC and mesh implementations. OCC functions are imported lazily so the package works without OpenCASCADE.

| Module | Computes |
|---|---|
| `bbox.py` | `compute_bbox_occ`, `compute_bbox_mesh`, `compute_oriented_bbox_mesh` |
| `volume.py` | `compute_volume_occ`, `compute_volume_mesh` (calls repair first) |
| `area.py` | `compute_surface_area_occ`, `compute_surface_area_mesh` |
| `centroid.py` | `compute_center_mass_occ`, `compute_center_mass_mesh` |
| `inertia.py` | `compute_moment_inertia_occ`, `compute_moment_inertia_mesh` |
| `reliability.py` | `is_mesh_reliable` (watertight + winding), `attempt_mesh_repair` (fix normals + fill holes) |
| `face_extraction.py` | `extract_faces_occ`, `extract_faces_mesh` (tessellate → numpy), `graph_to_faces_and_edges` |
| `face_graph.py` | `build_face_graph()` → NetworkX graph with per-node surface type and per-edge dihedral angle + convexity |
| `surface_classifier.py` | `classify_surface_occ(face)` → OCC adaptor-based surface type classification |
| `face_measurements.py` | Triangle-level area, centroid, normal (numpy cross-product math) |
| `faceangles.py` | `compute_face_angles()` — per-face angle analysis |
| `wall_thickness.py` | `compute_wall_thickness_occ`, `compute_wall_thickness_mesh`, `WallThicknessStats` — local wall thickness sampling with median/min/max/mean |
| `print_orientations.py` | `compute_print_orientations()` — analyzes 6 candidate build directions, computes overhang angles, recommends best orientation |

> **Note:** `face_extraction`, `face_graph`, `surface_classifier`, and `face_measurements` are not re-exported from `measurements/__init__.py`. They are imported directly from their submodules in the dispatcher.

#### 4d. Features — `geometry/features/`

DFM feature extractors for cylindrical manufacturing features. These run on the STEP/OCC path only (where surface-type classification is available).

| File | Functions |
|---|---|
| `holes.py` | `detect_holes`, `detect_cylindrical_holes`, `classify_hole`, `measure_hole` |
| `bosses.py` | `detect_bosses`, `detect_bosses_full`, `measure_boss`, `find_attached_face` |
| `cavities.py` | `detect_cavities`, `detect_cavities_full`, `measure_cavity` |

---

### 5. Database — `backend/database/`

Single migration (`01_create_analysis_jobs.sql`) creates the `analysis_jobs` table in Supabase:

```sql
analysis_id             TEXT PRIMARY KEY
filename                TEXT NOT NULL
status                  TEXT NOT NULL   -- pending | processing | completed | failed
manufacturability_score FLOAT
results_json            JSONB           -- full AnalysisResult payload
```

Row-Level Security is enabled with a permissive `FOR ALL TO public` policy (dev mode).

---

### 6. Frontend — `frontend/`

A full React 19 + TypeScript + Vite single-page application with a Three.js 3D viewer.

**Routing** (`src/App.tsx`) — React Router v7:

| Route | Page | Purpose |
|---|---|---|
| `/login` | `LoginPage` | Login form (auth not yet wired to backend) |
| `/upload` | `UploadPage` | Upload dropzone + file list + project modal |
| `/extra-info` | `ExtraInfoPage` | Process, quantity, material, tolerance, notes form |
| `/analysis` | `AnalysisPage` | 3D viewer + issue accordion (uses `/analyze-mock`) |
| `/debug` | `DebugApiPage` | Endpoint testing tool for all 5 backend routes |

**State management** (`src/store/index.ts`) — Zustand store with four slices:
- **ProjectSlice** — process, quantity, material, tolerance, notes
- **FileSlice** — uploaded files with `id`/`name`/`taskId`/`status`
- **AnalysisSlice** — analysis result
- **ChatSlice** — AskFaberAI chat open/close state

**API client** (`src/lib/api.ts`) — fetch-based wrappers for all backend endpoints: `uploadFile`, `getTaskStatus`, `getHealthCheck`, `createAnalysis`, `getMockAnalysis`. Reads `VITE_API_BASE_URL` from env (default: `http://127.0.0.1:8000`).

**Supabase client** (`src/lib/supabase.ts`) — initializes the JS client from `VITE_SUPABASE_URL` / `VITE_SUPABASE_ANON_KEY` (placeholders for future auth).

**Task polling** (`src/lib/useTaskPolling.ts`) — React hook that polls `/tasks/{task_id}` at a configurable interval, stops on terminal statuses (`SUCCESS`, `FAILED`, `FAILURE`), and cleans up on unmount.

**3D viewer** (`src/components/ModelPreview/`) — Three.js + @react-three/fiber + @react-three/drei. Renders a placeholder mesh; full analysis overlay (bounding boxes, highlights) is in progress.

**Components** (`src/components/`):
- `layout/` — `AppShell` (page wrapper), `Sidebar`, `StepIndicator`, `UsageIndicator`, `AskFaberAIButton`
- `home/` — `UploadDropzone` (file picker), `FileCard` (file status card)
- `analysis/` — `IssueAccordion`, `SeverityLegend`
- `extra-info/` — `ProcessToggle` (molding/printing)
- `common/` — `Modal`, `ModelPreviewPlaceholder`
- `ModelPreview/` — `ModelPreview` (3D canvas)

**Build tooling:**
- Vite 8 dev server (default: `http://localhost:5173`)
- ESLint + Prettier for linting/formatting
- Husky + lint-staged for pre-commit hooks
- TypeScript strict mode

**CI** (`.github/workflows/frontend-ci.yml`) — triggers on `frontend/**` changes: lint, format check, build.

---

### 7. Streamlit App — `streamlit-app/`

An alternative lightweight frontend for local development and debugging.

| File | Purpose |
|---|---|
| `app.py` | Upload form, STL preview (trimesh + plotly), task status polling, JSON download |
| `requirements.txt` | streamlit, requests, plotly, trimesh, numpy |
| `README.md` | Setup and run instructions |

**Workflow:** Enter backend URL → upload STEP/STL → preview STL in 3D → click "Launch geometry pipeline" → poll `/tasks/{task_id}` → download result JSON.

---

### 8. CI/CD — `.github/workflows/`

Two independent workflow files:

| Workflow | Trigger | Jobs |
|---|---|---|
| `ci.yml` (Backend) | PR to `main` | **Lint** (Python 3.13, ruff 0.14.3, `ruff check .`) + **Tests** (Python 3.13, pip-cached deps, `python -m pytest`) |
| `frontend-ci.yml` (Frontend) | PR to `main` / push to `main` on `frontend/**` changes | **Lint-and-build** (Node 20, npm ci, `npm run lint`, `npm run format:check`, `npm run build`) |

No deployment step exists yet.

---

## End-to-End Request Flow

```
Client (React / Streamlit)
  │
  │  POST /upload/  (multipart CAD file)
  ▼
main.py (FastAPI)
  ├─ storage.py ──────────────► Supabase Storage (cad-uploads bucket)
  ├─ crud.py ─────────────────► Supabase DB (analysis_jobs, status=pending)
  └─ workers.py ─ ─ ─ ─ ─ ─ ─► Redis (Celery broker)
                                  │
                                  │  extract_geometry_task (async)
                                  │
                                  ├─ crud.py ─ ─ ─ ─ ─ ─ ─ ─► Supabase DB (status=processing)
                                  ├─ requests.get(url) ─ ─ ─ ─► Supabase Storage (download file)
                                  ├─ geometry_engine_adapter.run_geometry_engine()
                                  │     └─ geometry/loaders/dispatcher.load_geometry()
                                  │           ├─ STEP path: step_loader_pythonocc (or step_loader)
                                  │           │              + measurements/*_occ()
                                  │           │              + face_extraction (OCC)
                                  │           │              + face_graph
                                  │           │              + features/ (holes, bosses, cavities)
                                  │           │              + wall_thickness (OCC)
                                  │           │              + print_orientations
                                  │           └─ STL path:  stl_loader_trimesh
                                  │                          + repair + is_mesh_reliable()
                                  │                          + measurements/*_mesh()
                                  │                          + mesh_quality
                                  │                          + wall_thickness (mesh)
                                  │                          + print_orientations
                                  └─ crud.py ─ ─ ─ ─ ─ ─ ─ ─► Supabase DB (status=completed,
                                                                         results_json=AnalysisResult)

Client
  │  GET /tasks/{task_id}?analysis_id=...
  ▼
main.py → crud.get_analysis_by_id() → returns AnalysisResult JSON
```

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| **Geometry engine is fully decoupled** | `geometry/` has zero FastAPI/Celery imports. Usable in notebooks, scripts, or swappable without touching the web layer. |
| **Adapter pattern** | `geometry_engine_adapter.py` owns the ORM-to-JSON translation. The worker never imports geometry internals directly. |
| **Dual-kernel strategy** | STEP uses exact B-rep math (OCC) for precise measurements. STL uses trimesh with auto-repair and a reliability flag because real uploaded STLs are often broken meshes. |
| **Feature detection is STEP-only** | Cylindrical feature detection (holes/bosses/cavities) requires surface-type classification (cylinder/plane distinction) that is only available on the OCC B-rep path, not on mesh triangle soup. |
| **Mock endpoint** | `/analyze-mock` is a deliberate tactical decision to unblock frontend development while the real engine is being built. The mock response shape is documented in `frontend/docs/api-contract-analyze-mock.md`. |
| **Manufacturability score is a placeholder** | Score is `85` if measurements are reliable, `55` if not. Real DFM checks will replace this once the features layer produces issue lists. |
| **Celery + Redis** | Geometry analysis is compute-heavy and should not block the HTTP response. The worker lifecycle also provides status tracking and retry semantics for free. |
| **Graceful STEP degradation** | pythonocc-core is Conda-only and build123d is optional. If neither is installed, STEP uploads fail gracefully with `StepSupportUnavailableError` (marked `failed`, no retry) instead of crashing the API. |
| **DB-first status polling** | `/tasks/{task_id}` prefers the Supabase DB record over the Celery result, so the UI sees `completed`/`failed` immediately even if Celery still reports `PENDING` for a moment. |
| **DB fallback on Celery success** | If the task succeeds in Celery but the DB record is missing or `results_json` is empty, the API returns the Celery payload directly with a warning instead of a misleading 404. |
| **Streamlit as alternative frontend** | Provides a quick local UI for backend debugging without needing the full React dev environment. |
| **Frontend API contract is `geometry_data: Any`** | `AnalysisResult.geometry_data` is `Optional[Any]` by design so the API can round-trip the geometry engine's full output without stripping fields. The mock endpoint currently only includes a subset of fields. |
