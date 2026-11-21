# Backend app layer

This package contains API schemas and application services. Start with the
[backend guide](../README.md) for setup, configuration, API routes, and tests.

- `schemas.py`: analysis, issue, 3D highlight, and persistence payloads.
- `database.py`: selects local or Supabase storage and loads native environment settings.
- `crud.py`: analysis record insertion, lookup, and status updates.
- `local_store.py`: SQLite records and files for local development.
- `services/storage.py`: shared file storage and retrieval for uploads and previews.
- `services/geometry_engine_adapter.py`: converts measured geometry into API JSON.
- `services/report_pdf.py` and `pdf_mesh_renderer.py`: report composition and model snapshots.
- `services/ai/`: report Q&A with deterministic fallback and optional provider calls.
- `services/dfm_knowledge/`: optional reference-document ingestion and retrieval.
- `observability.py`: optional LangTrace initialization.

HTTP routes and application startup remain in `backend/main.py`. Background
analysis orchestration lives in `backend/core/workers.py`. The geometry and DFM
packages are independent of the HTTP layer; see the root
[architecture guide](../../ARCHITECTURE.md) for the complete flow.
