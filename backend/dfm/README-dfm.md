# DFM Rule Engine

Turns geometry measurements into a manufacturability verdict. Sits **downstream**
of the geometry engine and **upstream** of the AI layer:

```
CAD upload -> Geometry Engine -> results_json -> DFM Rule Engine
    -> Manufacturability Report -> AI endpoint
```

The engine consumes measurements. It never produces them: no CAD kernel, no ray
casting, no feature detection. If geometry did not measure it, the rule that
needs it reports **Not assessed** and drops out of the score.

## Usage

```python
from dfm import DFMInputs, run_dfm_analysis

report = run_dfm_analysis(
    geometry_results_json,               # GeometryEngineResponse payload or dict
    DFMInputs(material="ABS", printing_process="fdm"),
)

report.manufacturable            # bool
report.manufacturability_score   # 0-100
report.rule("M1").findings       # per-rule detail with geometry references
```

Every field on `DFMInputs` is optional. A blank field never costs the user
points — the rule either runs on a stated default (recorded in
`report.processes[].assumptions`) or reports Not assessed.

## Layout

| Path | What it does |
|---|---|
| `engine.py` | `run_dfm_analysis()` — the only entry point callers need |
| `base.py` | `RuleEvaluator` ABC: degradation, error containment, finding caps |
| `context.py` | Resolves optional inputs against defaults; shared geometry views |
| `geometry_contract.py` | Read-only view of the geometry payload (see below) |
| `scoring.py` | Configurable weights, capping, blocker handling, process choice |
| `models.py` | Report schemas — the contract the API and AI layer read |
| `inputs.py` | Optional user context (material, printer, tolerances...) |
| `config/thresholds.yaml` | Every threshold, material and process table |
| `config/scoring.yaml` | Every scoring weight and verdict band |
| `rules/injection_molding/` | M1–M7, one class per rule |
| `rules/printing/` | P1–P6, one class per rule, all orientation-relative |

## The check-sets

**Injection molding** — M1 wall thickness · M2 wall uniformity · M3 draft angle ·
M4 undercuts · M5 rib ratio · M6 boss design · M7 tolerance feasibility.

**3D printing** — P1 overhang angle · P2 minimum feature size · P3 support volume ·
P4 aspect ratio · P5 trapped volumes · P6 build envelope.

Each rule declares its spec threshold type: Type 1 (material/process lookup),
Type 2 (fixed geometric ratio), Type 3 (topological yes/no). The report states
which type produced each verdict — conflating them is how a DFM tool loses trust.

## Configuration

All thresholds and weights are YAML, loaded once at FastAPI startup
(`main.py` lifespan) and cached for the process. Retuning is a config edit and a
restart, never a code change. `reload_dfm_config()` drops the cache.

Scoring defaults follow the MVP guidance agreed in the team thread — start 100,
Major -5, Minor -2.5, per-rule impact capped at 15 so repeated findings cannot
dominate, Blocker capped to 25 and `manufacturable = false`. The Blocker
behaviour is switchable (`cap` / `zero` / `deduct`) because the team recorded two
readings of it, and the roll-up supports both a deductive and a weighted
sub-score model. Nothing about the final numbers is assumed to be frozen.

## Pending geometry outputs

Feature recognition is still landing upstream. The contract in
`geometry_contract.py` already declares the arrays, so the evaluators work
unchanged the day they arrive:

| Field | Consumed by | Status today |
|---|---|---|
| `ribs[].thickness` | M5 | Populated on the STEP path |
| `bosses[].wall_thickness` | M6 | Populated on the STEP path |
| `ribs[].base_wall_thickness`, `bosses[].base_wall_thickness` | M5, M6 | Not yet — falls back to the part nominal wall and says so |
| `undercuts[]` | M4 | Not yet — falls back to a hole-axis inference capped at Major |
| `trapped_volumes[]` | P5 | Not yet — falls back to `cavities[]` opening data |
| `print_orientations[].support_volume_mm3` | P3 | Not yet — falls back to an estimate, labelled as one |

These default to `None` rather than `[]` on purpose: an absent array means "the
extractor never ran" (→ Not assessed), while an empty array means "it ran and
found nothing" (→ pass). Getting that distinction wrong would silently pass
parts that were never checked.

## Adding a process

1. Add the value to `ProcessType` in `models.py`.
2. Create `rules/<process>/` with one module per rule, each subclassing
   `RuleEvaluator`.
3. Register the list in `rules/__init__.py`.
4. Add the threshold blocks to `thresholds.yaml`.

The engine, scoring and AI layers need no changes.

## Tests

`backend/tests/dfm/` — rules, scoring, engine, AI layer and routes, including
mocked `ribs[]`/`bosses[]` payloads and a degenerate-geometry suite asserting
that no rule ever raises or penalises a part for missing data.

```
python -m pytest tests/dfm/ -q
```
