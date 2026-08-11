# FaberAI — Architecture

## What it is

FaberAI is an AI-assisted Design for Manufacturability (DFM) review platform for CAD parts. Engineers upload STEP or STL files, the backend analyzes geometry and DFM rules, and the web UI displays manufacturability scores, issues, and 3D highlights.

The project ships three user-facing interfaces:

| Interface | Stack | Directory |
|---|---|---|
| Web app (primary) | React 19 + TypeScript + Vite + Three.js / R3F + Zustand | `frontend/` |
| Streamlit app (development/test) | Streamlit + trimesh + Plotly | `streamlit-app/` |
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
├── frontend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── src/
│   ├── public/
│   ├── docs/
│   └── ...(React app)
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
│   │   │   ├── ai/
│   │   │   │   ├── client.py
│   │   │   │   ├── context_builder.py
│   │   │   │   ├── deterministic.py
│   │   │   │   ├── prompts.py
│   │   │   │   ├── service.py
│   │   │   │   └── __init__.py
│   │   │   ├── dfm_knowledge/
│   │   │   │   ├── agent.py
│   │   │   │   ├── chunker.py
│   │   │   │   ├── embeddings.py
│   │   │   │   ├── ingest.py
│   │   │   │   ├── retrieval.py
│   │   │   │   ├── docling_parser.py
│   │   │   │   └── __init__.py
│   ├── core/
│   │   └── workers.py
│   ├── database/
│   │   └── migrations/
│   ├── datasets/
│   ├── dfm/
│   ├── geometry/
│   ├── notebooks/
│   └── tests/
├── streamlit-app/
│   ├── app.py
│   ├── requirements.txt
│   └── README.md
└── ref/
    └── ...(reference snapshot of the same project structure)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 19 + TypeScript + Vite 8 |
| 3D rendering | Three.js + @react-three/fiber + @react-three/drei |
| State | Zustand |
| Routing | React Router DOM v7 |
| API client | Fetch + Supabase JS |
| Backend | FastAPI |
| Async pipeline | Celery |
| Broker / result backend | Redis |
| Database / storage | Supabase (PostgreSQL + Storage) |
| Validation | Pydantic v2 |
| Geometry | trimesh + optional pythonOCC / OpenCASCADE + build123d |
| DFM rules | Custom backend rule engine in `backend/dfm/` |
| AI assistant | deterministic fallback + optional Anthropic Claude LLM |
| PDF export | FPDF2 + custom renderer |
| Embeddings | sentence-transformers + local BGE model |
| Linting | Ruff / ESLint / Prettier |
| Testing | pytest |
| Python | 3.13 |
| Node | 20 |

---

## Core Architecture

### 1. Web API — `backend/main.py`

This FastAPI app is the main HTTP entry point for uploads, status polling, analysis persistence, DFM evaluation, PDF export, and AI Q&A.

It:
- loads DFM config and scoring thresholds on startup
- configures CORS for development
- wraps errors into a standardized JSON envelope
- validates and routes upload requests
- exposes report and task status endpoints
- supports inline PDF generation and stored-report downloads
- serves a mock analysis for frontend development

### 2. Backend App Layer — `backend/app/`

`backend/app/` contains the HTTP contract and service orchestration code.

- `schemas.py`: Pydantic models for API payloads, issues, 3D highlights, and database records.
- `crud.py`: Supabase CRUD operations for analysis jobs.
- `database.py`: Supabase client initialization.
- `observability.py`: logging, error translation, and telemetry helpers.
- `services/storage.py`: CAD upload and storage management.
- `services/geometry_engine_adapter.py`: converts raw geometry output into API-friendly JSON.
- `services/report_pdf.py`: PDF generation for completed analyses.
- `services/ai/`: report-question answering.
- `services/dfm_knowledge/`: standards-based retrieval and knowledge answering.

### 3. Celery Worker — `backend/core/workers.py`

The worker manages asynchronous CAD analysis and persistency.

Task flow:
1. download the uploaded file from Supabase Storage
2. save it locally
3. run the geometry engine
4. generate a STEP preview STL when needed
5. execute the DFM rule engine
6. map findings into issues and report payloads
7. persist results to Supabase
8. mark the analysis as completed or failed

### 4. Geometry Engine — `backend/geometry/`

This package handles CAD ingestion and feature extraction.

- loaders: STEP and STL ingestion
- measurements: bbox, volume, surface area, wall thickness, orientations, mesh quality
- features: hole detection, boss detection, cavity detection, topology analysis
- models: internal geometry schema

It is intentionally separate from the web API so it can be reused by workers and tests.

### 5. DFM Rule Engine — `backend/dfm/`

This package encapsulates manufacturability checks, thresholds, and scoring.

- `config/`: YAML-driven thresholds and scoring configuration
- `engine.py`: rule execution and report construction
- `inputs.py`: normalized manufacturing inputs
- `models.py`: DFM report and finding schema
- `rules/`: individual rule implementations
- `scoring.py`: severity weights and verdict aggregation

The DFM engine is deterministic and shared by the worker pipeline and AI services.

### 6. Database — `backend/database/`

Supabase stores analysis jobs and report payloads.

The migrations create tables like `analysis_jobs` and enable vector-search support for `dfm_reference_docs`.

---

## `backend/app/services/ai` Architecture

This layer answers questions about an already-computed DFM report.

Responsibilities:
- accept only completed report data, never rerun geometry or DFM evaluation
- compute a deterministic answer from the report as a fallback
- optionally call an LLM when provider credentials are configured
- ground answers with referenced rule IDs and optional standards excerpts

Key modules:
- `client.py`: Anthropic Claude Messages API client wrapper and provider detection.
- `context_builder.py`: constructs report and geometry context for prompt building.
- `deterministic.py`: templates deterministic answers from report facts.
- `prompts.py`: builds system/user messages for the LLM.
- `service.py`: orchestrates deterministic fallback, LLM calls, and final response assembly.

Process flow:
1. `answer_dfm_question()` receives a finished `DFMReport` and question.
2. a deterministic answer is generated immediately.
3. if the LLM client is configured, optional standards excerpts are retrieved.
4. the model is called with report context and grounding.
5. failures or empty responses degrade gracefully to the deterministic answer.

This service always returns factual, report-based responses even when the LLM path is unavailable.

---

## `backend/app/services/dfm_knowledge` Architecture

This module provides retrieval-augmented answers from reference standards.

Responsibilities:
- ingest Docling-exported standards into Supabase
- chunk documents by clause and table for accurate citation
- embed content with a local sentence-transformer model
- perform vector retrieval over `dfm_reference_docs`
- answer questions from retrieved excerpts with citations
- degrade to deterministic excerpt responses when no LLM is configured

Key modules:
- `chunker.py`: turns parsed Docling docs into clause-aware chunks.
- `docling_parser.py`: parses the Docling export structure.
- `embeddings.py`: local embedding wrapper for passages and queries.
- `ingest.py`: one-off CLI ingestion workflow.
- `retrieval.py`: query embedding and Supabase vector-search RPC.
- `agent.py`: answer questions from retrieved chunks.

Process flow:
1. ingestion parses a Docling JSON export into chunk rows.
2. chunk text is embedded and stored in Supabase.
3. retrieval embeds the user query and calls the `match_dfm_reference_docs` RPC.
4. the best-matching chunks are returned as source excerpts.
5. the agent either summarizes them with the LLM or returns them directly.

This service is intentionally separate from `services/ai`: it is a standards reference layer, while `services/ai` is a report-specific Q&A layer.
'''
with open('/tmp/ARCHITECTURE_update.md', 'w', encoding='utf-8') as f:
    f.write(content)
PY