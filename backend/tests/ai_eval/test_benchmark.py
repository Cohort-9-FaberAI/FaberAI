"""Pytest entry point for the live AI benchmark.

Skipped by default: it calls the live Claude API, so it is billable and slower
than the unit suite. Opt in with::

    RUN_AI_BENCHMARK=1 python -m pytest tests/ai_eval -q

The grading logic is unit-tested without a key in ``test_grader.py``, so a
regression in the checks themselves is caught for free in CI.
"""

from __future__ import annotations

import os

import pytest

from tests.ai_eval.runner import run

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_AI_BENCHMARK") != "1",
    reason="set RUN_AI_BENCHMARK=1 to call the live Claude API",
)


@pytest.fixture(scope="module")
def results():
    # The autouse conftest fixture strips the API key to keep the unit suite
    # offline; restore it for the one module that is allowed to call out.
    from app.services.ai.client import LLMClient

    key = os.environ.get("FABERAI_AI_BENCHMARK_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    return run(client=LLMClient(api_key=key))


@pytest.mark.parametrize(
    "family",
    ["grounded", "engineering", "hallucination", "contradiction", "missing"],
)
def test_family_passes(results, family):
    failed = [r for r in results if r.case.family == family and not r.passed]
    assert not failed, "\n".join(
        f"{r.case.case_id}: {r.failures or r.error}\n  expected: {r.case.expected}"
        for r in failed
    )
