# FaberAI — Architecture

## What it is

FaberAI is an **AI-powered Design for Manufacturability (DFM) review tool**. Engineers upload a CAD part (STEP or STL) and get back a manufacturability score, a list of issues, and 3D bounding-box highlights that pinpoint problem areas in a Three.js viewer.

---

## Repository Layout

```
FaberAI/
├── docker-compose.yml              # Redis container (Celery broker/backend)
├── .github/workflows/ci.yml        # CI: lint + test on PRs to main
├── backend/                        # All server-side Python code
│   ├── main.py                     # FastAPI app + route definitions
│   ├── requirements.txt            # Pinned pip dependencies
│   ├── ruff.toml                   # Linter configuration
│   ├── environment-ds.yml          # Conda env for OCC / data-science work
│   ├── app/                        # Web layer (schemas, DB access, services)
│   │   ├── schemas.py              # Pydantic API contracts
│   │   ├── crud.py                 # Supabase table operations
│   │   ├── database.py             # Supabase client singleton
│   │   └── services/
│   │       ├── storage.py          # Upload CAD files to Supabase Storage
│   │       └── geometry_engine_adapter.py  # Adapter between worker and geometry engine
│   ├── core/
│   │   └── workers.py              # Celery task definition
│   ├── geometry/                   # Pure geometry engine (no web dependencies)
│   │   ├── loaders/                # File ingestion (STEP via OCC, STL via trimesh)
│   │   ├── measurements/           # Dual OCC/mesh measurement implementations
│   │   ├── models/                 # Geometry data model (dataclasses + enums)
│   │   └── features/               # Placeholder — future DFM feature extractors
│   ├── database/migrations/        # SQL migration files (Supabase)
│   ├── datasets/                   # Sample CAD files for testing
│   │   ├── STEP/                   # 25 .stp mechanical parts
│   │   ├── STL/                    # 4 .stl meshes
│   │   └── OPTIC/                  # Fresnel lens mold files
│   ├── notebooks/                  # Jupyter notebooks (placeholder)
│   └── tests/                      # pytest suite
│       ├── conftest.py
│       ├── test_main.py
│       └── geometry/
│           └── test_measurements.py
└── frontend/                       # Placeholder — no code yet (README only)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| API framework | FastAPI 0.139 + Uvicorn |
| Data validation | Pydantic v2 |
| Async task queue | Celery 5.6 |
| Message broker / result backend | Redis (Docker) |
| Database | Supabase (PostgreSQL) |
| Object storage | Supabase Storage (`cad-uploads` bucket) |
| DB client | supabase-py / postgrest |
| STEP geometry kernel | pythonOCC / OpenCASCADE |
| STL geometry kernel | trimesh + manifold3d |
| Graph algorithms | NetworkX |
| Numerics | NumPy, SciPy |
| Linting | Ruff (pinned 0.14.3 in CI) |
| Testing | pytest |
| CI | GitHub Actions |
| Python version | 3.13 (CI) / 3.11 (conda DS env) |

---

## Components

### 1. API — `backend/main.py`

The FastAPI application. All routes are defined here; no routers are used.

| Route | Method | Description |
|---|---|---|
| `/` | GET | Health check |
| `/upload/` | POST | Accept CAD file → upload to Supabase Storage → create DB record → dispatch Celery task. Returns `task_id` + `analysis_id`. |
| `/tasks/{task_id}` | GET | Poll Celery and Supabase for job status and result. Prefers the DB record so the UI sees `completed`/`failed` immediately. |
| `/analyze-mock` | POST | Hardcoded mock response (thin wall + deep pocket issues) to unblock frontend development. |
| `/analysis/` | POST | Directly insert a validated `AnalysisResult` into Supabase (DB integration test). |

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
| `AnalysisResult` | Top-level job result: `analysis_id`, `filename`, `status`, `manufacturability_score`, `summary`, `part_metadata`, `issues[]` |
| `Issue` | Single DFM issue: `type`, `severity` (high/medium/low), `message`, `recommendation`, `three_js_highlight` |
| `ThreeJSHighlight` | AABB bounding box (`min`, `max`, `center`, `color`) for 3D canvas highlighting |
| `AnalysisDBRecord` | Flattened row for Supabase insertion; stores full payload as `results_json` (JSONB) |
| `PartMetadata`, `BoundingBox`, `Vector3` | Supporting sub-models |

**`database.py`** — Supabase client singleton. Reads `SUPABASE_URL` + `SUPABASE_KEY` from `.env`. Raises `EnvironmentError` at import time if either is missing.

**`crud.py`** — Three operations against the `analysis_jobs` table:
- `insert_analysis_result()` — wraps in `AnalysisDBRecord` and inserts
- `get_analysis_by_id()` — single-row fetch by UUID
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

**Dual-path strategy:**
- `.step` / `.stp` → pythonOCC — exact B-rep math, no mesh reliability concerns, full face/edge topology extraction
- `.stl` → trimesh — mesh-based, includes repair attempt + `measurements_reliable` flag

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

#### 4d. Features — `geometry/features/` *(placeholder)*

Empty directory, README stub only. Intended for future DFM feature extractors: thin walls, deep pockets, undercuts, etc. The manufacturability score is hardcoded until this layer is built.

---

### 5. Database — `backend/database/`

Single migration (`01_create_analysis_jobs.sql`) creates the `analysis_jobs` table in Supabase:

```sql
analysis_id             TEXT PRIMARY KEY
filename                TEXT NOT NULL
status                  TEXT NOT NULL   -- pending | processing | completed | failed
manufacturability_score FLOAT
results_json            JSONB           -- full GeometryEngineResponse payload
```

Row-Level Security is enabled with a permissive `FOR ALL TO public` policy (dev mode).

---

### 6. Frontend — `frontend/`

**No code exists yet.** The directory contains only a `README.md`. The `/analyze-mock` endpoint was created deliberately to allow frontend development to proceed in parallel.

---

### 7. CI/CD — `.github/workflows/ci.yml`

Triggers on pull requests to `main`. Two parallel jobs:

| Job | Steps |
|---|---|
| **Lint** | Python 3.13, ruff 0.14.3 (pinned), `ruff check .` |
| **Tests** | Python 3.13, pip-cached deps, `python -m pytest` |

No deployment step exists yet.

---

## End-to-End Request Flow

```
Client
  │
  │  POST /upload/  (multipart CAD file)
  ▼
main.py (FastAPI)
  ├─ storage.py ──────────────► Supabase Storage (cad-uploads bucket)
  ├─ crud.py ─────────────────► Supabase DB (analysis_jobs, status=pending)
  └─ workers.py ──────────────► Redis (Celery broker)
                                    │
                                    │  extract_geometry_task (async)
                                    │
                                    ├─ crud.py ──────────────► Supabase DB (status=processing)
                                    ├─ requests.get(url) ────► Supabase Storage (download file)
                                    ├─ geometry_engine_adapter.run_geometry_engine()
                                    │     └─ geometry/loaders/dispatcher.load_geometry()
                                    │           ├─ STEP path: step_loader_pythonocc
                                    │           │              + measurements/*_occ()
                                    │           │              + face_extraction (OCC)
                                    │           └─ STL path:  stl_loader_trimesh
                                    │                          + repair + is_mesh_reliable()
                                    │                          + measurements/*_mesh()
                                    └─ crud.py ──────────────► Supabase DB (status=completed,
                                                                             results_json=...)

Client
  │  GET /tasks/{task_id}?analysis_id=...
  ▼
main.py → crud.get_analysis_by_id() → returns GeometryEngineResponse JSON
```

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| **Geometry engine is fully decoupled** | `geometry/` has zero FastAPI/Celery imports. Usable in notebooks, scripts, or swappable without touching the web layer. |
| **Adapter pattern** | `geometry_engine_adapter.py` owns the ORM-to-JSON translation. The worker never imports geometry internals directly. |
| **Dual-kernel strategy** | STEP uses exact B-rep math (OCC) for precise measurements. STL uses trimesh with auto-repair and a reliability flag because real uploaded STLs are often broken meshes. |
| **Mock endpoint** | `/analyze-mock` is a deliberate tactical decision to unblock frontend development while the real engine is being built. |
| **Manufacturability score is a placeholder** | `geometry/features/` is empty. Real DFM checks (thin walls, deep pockets, undercuts) are the next major development area. |
| **Celery + Redis** | Geometry analysis is compute-heavy and should not block the HTTP response. The worker lifecycle also provides status tracking and retry semantics for free. |
