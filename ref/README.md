# FaberAI
Product Realization Tool being built for the AI PM Accerlerator Program. FaberAI looks to help design engineers and manufacturing engineers realize if a part can be manufactured as designed.

## Frontend

The web client lives in [`frontend/`](frontend/) (React + TypeScript + Vite). See
[frontend/README.md](frontend/README.md) for install and run instructions.

## Backend

The API and processing pipeline live in [`backend/`](backend/). An architecture reference doc is
not published yet — check with the backend team for the current design notes.

### Optional STEP support

Analyzing STEP/STP files requires two optional libraries that are deliberately
**not** in `backend/requirements.txt`:

- **pythonocc-core** (OpenCASCADE bindings) — not available on PyPI, so it
  cannot go in `requirements.txt`; it is only distributed via Conda:
  `conda install -c conda-forge pythonocc-core`.
- **build123d** — pip-installable (`pip install build123d`) but optional, so
  non-STEP users don't need it.

The easiest way to get a STEP-capable environment is the Conda spec in
[`backend/environment-ds.yml`](backend/environment-ds.yml):

```bash
conda env create -f backend/environment-ds.yml
conda activate faberai-ds
```

Without these libraries the backend starts and processes mesh formats (STL)
normally. STEP uploads are still accepted but the analysis fails gracefully
with a `StepSupportUnavailableError` explaining how to install the optional
dependencies, and the analysis record is marked `failed`.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for branch naming and PR conventions shared across both teams.
