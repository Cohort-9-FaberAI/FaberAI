# API Contract: `POST /analyze-mock` and `geometry_data`

Purpose: pin down the shape of `geometry_data` before the frontend builds the 3D
viewer against it, and flag where the current mock diverges from what the real
geometry engine produces. For Track B (API Contract Synchronization) — to review
with Daniel Williams' backend team.

## Current state (as of this doc)

Three different shapes exist in the backend today and they don't agree:

1. **`POST /analyze-mock`** (`backend/main.py`) — hardcoded response the frontend
   is currently coding against. `geometry_data` here only contains:
   `source_format`, `bounding_box`, `volume_mm3`, `surface_area_mm2`,
   `measurements_reliable`, `center_mass`.
2. **`GeometryEngineResponse`** (`backend/app/services/geometry_engine_adapter.py`)
   — the fully-typed schema the real geometry engine actually produces. Includes
   everything in the mock, plus `faces`, `edges`, `wall_samples`,
   `wall_thickness_stats`, `mesh_quality`, `print_orientations`, and
   `moment_of_inertia`.
3. **`AnalysisResult.geometry_data`** (`backend/app/schemas.py`) — the field
   returned by the real (non-mock) analysis endpoints. Typed as `Optional[Any]`,
   i.e. not validated against `GeometryEngineResponse` on the way out.

## Open questions for backend

### 1. Is `geometry_data: Any` permanent?

`AnalysisResult.geometry_data` is `Optional[Any]` by design, so the API can
round-trip the geometry engine's output without stripping fields. Once real
workers replace the mock, is this ever going to be tightened to
`GeometryEngineResponse`, or should the frontend treat the shape as
unguaranteed indefinitely?

### 2. Which `GeometryEngineResponse` fields does the frontend actually need, and can the mock include them?

The mock is missing `faces`, `edges`, `wall_samples`, `mesh_quality`,
`print_orientations`, and `moment_of_inertia`. If the 3D viewer needs any of
these beyond the bounding box / center of mass, we need dummy values added to
`/analyze-mock` so frontend work isn't blocked waiting on real workers.

### 3. `moment_of_inertia` — needs a spec

Currently `Optional[List[List[float]]]` — a bare 3×3 nested list with no
documented convention. Need to know:

- Reference frame: about center of mass, or about the origin?
- Units?
- Row/column convention (is it symmetric, does index order matter)?
- When is it `None`? (e.g. STEP-only, mesh-only, or always populated?)

### 4. Coordinate system and units

- Does the geometry engine's axis convention (handedness, up-axis) match what
  Three.js expects, or does the frontend need to convert?
- `part_metadata.units` states `"mm"` explicitly, but `geometry_data` itself has
  no `units` key. Is `mm` guaranteed for every field in `geometry_data`
  (`volume_mm3`, `surface_area_mm2`, `center_mass`, etc.), or could that vary
  by source format (STL vs STEP)?

### 5. STEP handling: what does the backend actually send back for rendering?

Per the latest architecture decision, local frontend STEP conversion (OCT
import-js) is deprioritized — the backend will process raw STEP uploads and
give the frontend "optimized, web-ready geometries." That phrase covers two
very different integration shapes:

- A converted mesh/glTF **file** the frontend fetches as a static asset, or
- **Geometry as JSON** (vertices/faces/normals in `geometry_data`) that the
  frontend builds a `BufferGeometry` from client-side.

Which is it? This determines what the viewer component needs to do with the
response.

### 6. Does `geometry_data` get normalized regardless of source format?

If the backend converts STEP → mesh server-side, does `geometry_data` end up
looking the same shape whether the original upload was `.step` or `.stl`
(i.e. does `source_format` in the response ever say `"step"`, or does the
backend always hand back STL-shaped output)? Affects whether the frontend
needs to branch on `source_format` at all.

### 7. State 1 (raw upload, pre-analysis) — client-only or backend-assisted?

The 3D canvas has two states: State 1 renders the raw uploaded file directly;
State 2 overlays analysis results once the backend resolves. For State 1, is
the raw-file render done entirely client-side from the file the user picked
(no backend round-trip), or does the backend provide something for that
initial render too? This determines whether the frontend needs to retain the
raw `File`/blob client-side — currently `UploadDropzone` only stores
`id`/`name`/`taskId`/`status` in the store, not the file itself.

### 8. What does State 1 show for a STEP upload?

Since STEP isn't parsed client-side, what should State 1 render before the
backend responds if the user uploaded `.step`/`.stp`? A loading/placeholder
state, or does State 1 only apply to STL uploads?

## What "done" looks like for this task

- Agreed field list for `geometry_data` (mock-only vs. guaranteed in production).
- `moment_of_inertia` shape/units/reference-frame documented.
- Coordinate system and units confirmed compatible with Three.js, or a known
  conversion step identified.
- `/analyze-mock` updated (if needed) to include any additional fields the
  viewer depends on, so frontend isn't blocked on real workers.
- STEP-to-viewer integration shape confirmed (file asset vs. JSON geometry).
- State 1 (pre-analysis render) data source confirmed, including the
  STEP-upload case.
