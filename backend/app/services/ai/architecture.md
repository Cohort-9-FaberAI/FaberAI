# AI Agent Architecture — `backend/app/services/ai`

This package implements the AI assistant layer for DFM reports. It is designed as a deterministic, explainable wrapper around a report-driven prompt pipeline, with a fallback answerer when no LLM is configured.

## Goals

- Answer engineer questions about a completed DFM report.
- Never rerun geometry analysis or DFM rule evaluation.
- Always ground answers in existing report facts.
- Degrade to deterministic text when the LLM provider is unavailable.
- Keep model behavior safe by enforcing explicit guardrails.

## Components

### `service.py`

Top-level AI service logic.

Responsibilities:

- Accept a finished `DFMReport` and an engineer question.
- Generate a deterministic fallback answer from the report.
- If an LLM is configured, assemble context and messages, then call the provider.
- If the LLM call fails or is not configured, return the deterministic fallback.
- Return `AIAnswer` with:
  - `question`
  - `answer`
  - `mode` (`llm` or `deterministic`)
  - `model`
  - `referenced_rules`
  - `analysis_id`
  - `degraded_reason`

### `client.py`

Provider integration for the Claude Messages API via the `anthropic` SDK.

Responsibilities:

- Read configuration from environment variables:
  - `FABERAI_AI_API_KEY` / `ANTHROPIC_API_KEY`
  - `FABERAI_AI_MODEL`
  - `FABERAI_AI_BASE_URL`
  - `FABERAI_AI_TIMEOUT`
  - `FABERAI_AI_MAX_TOKENS`
  - `FABERAI_AI_EFFORT`
- Initialize a cached Claude client.
- Translate OpenAI-style messages into Claude Messages API parameters:
  - top-level `system` prompt
  - `messages` turn list
- Call `messages.create(...)` with `output_config={"effort": ...}`.
- Detect refusal, empty text, and API errors, then surface them as `LLMRequestError`.
- Provide `is_configured` and `LLMNotConfigured` handling.

### `context_builder.py`

Builds the curated model context from a completed DFM report.

Responsibilities:

- Flatten a `DFMReport` into a concise JSON-ready dictionary.
- Include:
  - report metadata
  - part details
  - user inputs
  - headline manufacturability data
  - per-process verdicts and scores
  - per-rule summaries, explanations, thresholds, findings, recommendations
  - assumptions and not-assessed/suppressed details
- Optionally include safe aggregate geometry facts if geometry payload is provided.
- Enforce prompt limits by truncating long lists and aggregating counts.
- Ensure the model can only cite facts that already exist in the report.

### `prompts.py`

Prompt assembly and the safety guardrail for the assistant.

Responsibilities:

- Define `SYSTEM_PROMPT` that:
  - declares the assistant is a DFM report explainer
  - forbids measuring geometry or re-deciding verdicts
  - requires citations from the report
  - distinguishes general engineering knowledge from report facts
- Build the user prompt with the serialized curated context and the engineer question.
- Return the final message list sent to the model.

### `deterministic.py`

Deterministic fallback answer generation.

Responsibilities:

- Classify question intent, e.g. `overview`, `failed_rules`, `improve`, `process_choice`, `score`, `not_manufactured`, `not_assessed`, `small_talk`.
- Build templated answers from `DFMReport` content.
- Return both answer text and referenced rule IDs.
- Ensure fallback output is stable, factual, and report-driven.

## Data Flow

1. A request arrives with a question and an already-computed `DFMReport`.
2. `answer_dfm_question()` computes a deterministic fallback answer first.
3. If an LLM client is configured, it builds the model context with `build_ai_context()`.
4. `build_messages()` constructs the system and user message payload.
5. `LLMClient.complete()` sends the prompt to the Claude API.
6. If the provider returns text, the service returns an `llm` answer.
7. If the provider is unavailable or returns an error, the service returns the deterministic answer instead.

## Safety and Boundaries

- The LLM never determines manufacturability. The DFM engine does.
- The model never recomputes geometry or re-evaluates rules.
- Raw geometry arrays are excluded from the prompt.
- Answers must cite rule IDs and report-derived values when referring to the specific part.
- If the report does not contain a requested fact, the assistant must say so.
- General manufacturing knowledge may be used only as contextual explanation, never as a claimed part fact.

## Export Surface

The package exports the core service and helper functions through `__init__.py`:

- `answer_dfm_question`
- `AIAnswer`
- `AnswerMode`
- `LLMClient`, `get_llm_client`, `reset_llm_client`
- `build_ai_context`
- `build_messages`
- `answer_from_report`
- `classify_intent`
- `summarise_failures`

## Configuration

The AI client is configured by environment variables so deployment can swap providers or proxies without code changes.

- `FABERAI_AI_API_KEY` / `ANTHROPIC_API_KEY`
- `FABERAI_AI_MODEL`
- `FABERAI_AI_BASE_URL`
- `FABERAI_AI_TIMEOUT`
- `FABERAI_AI_MAX_TOKENS`
- `FABERAI_AI_EFFORT`
