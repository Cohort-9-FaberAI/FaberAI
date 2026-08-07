"""Grade the benchmark cases against the live assistant.

Deliberately deterministic: every check is a string or numeric-token test over
the answer plus the context it was given. No LLM judge, so re-scoring the same
answers always produces the same verdict and the benchmark can be diffed across
prompt changes.

Run it directly::

    cd backend
    python -m tests.ai_eval.runner              # all families
    python -m tests.ai_eval.runner hallucination contradiction
    python -m tests.ai_eval.runner --json out.json

It needs a real key (``FABERAI_AI_API_KEY`` or ``ANTHROPIC_API_KEY``) and makes
one API call per case.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(BACKEND_DIR / ".env")
load_dotenv()

from app.services.ai.client import LLMClient  # noqa: E402
from app.services.ai.context_builder import build_ai_context  # noqa: E402
from app.services.ai.service import AnswerMode, answer_dfm_question  # noqa: E402
from dfm import DFMInputs, run_dfm_analysis  # noqa: E402
from dfm.models import ProcessType  # noqa: E402

from tests.ai_eval.cases import BLOCKED, CASES, CLEAN, Case  # noqa: E402

_NUMBER = re.compile(r"\d+(?:\.\d+)?")

# A *measurement* is a number carrying a physical unit. Those are the numbers the
# geometry engine owns and the model must never produce on its own, so the
# grounding check is scoped to them. Unitless numbers are deliberately excluded:
# a model that adds up the report's own score impacts and writes "12.5 points
# total" is doing arithmetic on grounded values, not inventing a measurement.
# Where a bare number does matter (a score the question got wrong), the case
# pins it with `forbidden_numbers` instead.
_MEASUREMENT = re.compile(
    r"(\d+(?:\.\d+)?)\s*(?:mm(?:\^?[23]|²|³)?|millimet|cm\b|degrees?\b|deg\b|°|µm|um\b|microns?\b)",
    re.IGNORECASE,
)

# Cues that the model is rejecting a number rather than asserting it: "there is
# no 40 mm bore", "the 5 mm figure doesn't match". Quoting a false premise in
# order to correct it is the behaviour the contradiction family wants.
_NEGATION = re.compile(
    r"(?:\bno\b|\bnot\b|n't|\bnever\b|\bnothing\b|\bnone\b|\bnowhere\b|"
    r"\bincorrect\b|\bwrong\b|\bmistaken\b|\bactually\b|\binstead\b|"
    r"\brather than\b|\bcontrary\b|\bcontradict|\bdisagree|\bpremise\b|"
    r"\bfar from\b|\bfar thinner\b|\bwell below\b|\bwell under\b|\bdoesn.t match\b)",
    re.IGNORECASE,
)


@dataclass
class Result:
    case: Case
    answer: str
    mode: str
    failures: List[str] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def passed(self) -> bool:
        return not self.failures and self.error is None


def _fixtures() -> Dict[str, Any]:
    """The two report fixtures the cases are asked against.

    Reuses the geometry payloads from the DFM test fixtures so the benchmark
    scores the assistant against the same parts the rule-engine tests cover.
    """
    from tests.dfm.conftest import step_geometry, stl_geometry

    step = step_geometry.__wrapped__()
    stl = stl_geometry.__wrapped__()
    return {
        BLOCKED: (
            run_dfm_analysis(stl, DFMInputs(process=ProcessType.printing)),
            stl,
        ),
        CLEAN: (
            run_dfm_analysis(step, DFMInputs(material="ABS")),
            step,
        ),
    }


def _context_values(context: Dict[str, Any]) -> set[float]:
    """Every numeric value the model was actually shown.

    Compared as floats, not strings: the report holding ``4.5`` licenses the
    model writing ``4.50``, and ``100`` licenses ``100.0``.
    """
    blob = json.dumps(context, default=str)
    return {float(token) for token in _NUMBER.findall(blob)}


def _is_negated(text: str, start: int, end: int) -> bool:
    """Does the sentence around [start:end] reject this number rather than assert it?"""
    window = text[max(0, start - 160):min(len(text), end + 80)]
    return bool(_NEGATION.search(window))


def _forbidden_pattern(entry: str) -> tuple[float, re.Pattern[str]]:
    """Compile one ``forbidden_numbers`` entry into (value, whole-token matcher).

    An entry may carry the unit the question asserted (``"5 mm"``), which scopes
    the check to that role. That matters when the forbidden value also exists in
    the report in a *different* role: ``5`` is the invented wall thickness in
    C2, but ``5.0`` is also the genuine score impact of P1 and P4, and a table
    row reading ``| P1 | Major | 5.0 |`` must not be read as accepting a 5 mm
    wall. A bare entry (``"95"`` for a score) matches any whole numeric token.

    Matching is by numeric *value* over whole tokens, so ``5 mm`` is caught when
    written ``5mm`` or ``5.0 mm``, and never by matching the leading digit of an
    unrelated longer number.
    """
    head, _, unit = entry.strip().partition(" ")
    value = float(head)
    token = r"(?<![\d.])(\d+(?:\.\d+)?)"
    unit = unit.strip()
    pattern = rf"{token}\s*{re.escape(unit)}\b" if unit else rf"{token}(?![\d.]*\d)"
    return value, re.compile(pattern, re.IGNORECASE)


def grade(case: Case, answer: str, context: Dict[str, Any]) -> List[str]:
    """Return a list of failure descriptions; empty means the case passed."""
    failures: List[str] = []
    lowered = answer.lower()

    for needle in case.must_contain:
        if needle.lower() not in lowered:
            failures.append(f"missing required text {needle!r}")

    for group in case.must_contain_any:
        if not any(option.lower() in lowered for option in group):
            failures.append(f"none of {group} appear in the answer")

    for needle in case.must_not_contain:
        if needle.lower() in lowered:
            failures.append(f"contains forbidden text {needle!r}")

    for entry in case.forbidden_numbers:
        value, pattern = _forbidden_pattern(entry)
        asserted = [
            m for m in pattern.finditer(answer)
            if float(m.group(1)) == value
            and not _is_negated(answer, m.start(), m.end())
        ]
        if asserted:
            failures.append(
                f"asserts {entry!r}, a value the question invented and the report "
                f"does not hold (repeating it in order to correct it is fine)"
            )

    if case.numbers_must_be_grounded:
        grounded = _context_values(context)
        invented = sorted(
            {
                m.group(1)
                for m in _MEASUREMENT.finditer(answer)
                if float(m.group(1)) not in grounded
                and not _is_negated(answer, m.start(), m.end())
            }
        )
        if invented:
            failures.append(f"states measurements not present in the context: {invented}")

    if case.custom is not None:
        problem = case.custom(answer)
        if problem:
            failures.append(problem)

    return failures


def run(families: Optional[List[str]] = None, client: Optional[LLMClient] = None) -> List[Result]:
    fixtures = _fixtures()
    client = client or LLMClient()
    if not client.is_configured:
        raise RuntimeError(
            "No API key. Set FABERAI_AI_API_KEY (or ANTHROPIC_API_KEY) to run the benchmark."
        )

    results: List[Result] = []
    for case in CASES:
        if families and case.family not in families:
            continue
        report, geometry = fixtures[case.report]
        context = build_ai_context(report, geometry)
        try:
            answer = answer_dfm_question(
                report, case.question, geometry=geometry, client=client
            )
        except Exception as exc:  # noqa: BLE001 - the benchmark reports, never crashes
            results.append(Result(case, "", "error", error=repr(exc)))
            continue

        if answer.mode is not AnswerMode.llm:
            # The deterministic fallback is a correct product behaviour but it is
            # not what this benchmark measures, so flag it rather than score it.
            results.append(
                Result(
                    case,
                    answer.answer,
                    answer.mode.value,
                    error=f"degraded to deterministic: {answer.degraded_reason}",
                )
            )
            continue

        results.append(
            Result(case, answer.answer, answer.mode.value, grade(case, answer.answer, context))
        )
    return results


def summarise(results: List[Result]) -> str:
    lines: List[str] = []
    by_family: Dict[str, List[Result]] = {}
    for result in results:
        by_family.setdefault(result.case.family, []).append(result)

    for family, group in by_family.items():
        passed = sum(1 for r in group if r.passed)
        lines.append(f"\n{family.upper()}  {passed}/{len(group)} passed")
        for result in group:
            mark = "PASS" if result.passed else "FAIL"
            lines.append(f"  [{mark}] {result.case.case_id}: {result.case.question}")
            if result.error:
                lines.append(f"         error: {result.error}")
            for failure in result.failures:
                lines.append(f"         - {failure}")
            if not result.passed:
                lines.append(f"         expected: {result.case.expected}")
                snippet = " ".join(result.answer.split())[:400]
                lines.append(f"         answer: {snippet}")

    total_passed = sum(1 for r in results if r.passed)
    lines.append(f"\nTOTAL {total_passed}/{len(results)} passed")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("families", nargs="*", help="grounded engineering hallucination contradiction missing")
    parser.add_argument("--json", dest="json_path", help="also write full results as JSON")
    args = parser.parse_args()

    results = run(args.families or None)
    print(summarise(results))

    if args.json_path:
        Path(args.json_path).write_text(
            json.dumps(
                [
                    {
                        "case_id": r.case.case_id,
                        "family": r.case.family,
                        "question": r.case.question,
                        "expected": r.case.expected,
                        "passed": r.passed,
                        "failures": r.failures,
                        "error": r.error,
                        "mode": r.mode,
                        "answer": r.answer,
                    }
                    for r in results
                ],
                indent=2,
            ),
            encoding="utf-8",
        )
    return 0 if all(r.passed for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
