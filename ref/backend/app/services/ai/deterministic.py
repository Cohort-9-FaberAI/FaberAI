"""Deterministic answers built straight from the DFM report — no LLM.

Two jobs:

* **Fallback.** When no LLM provider is configured, or the call fails, the AI
  endpoint still answers instead of erroring. Every fact comes from the report,
  so the answer is reproducible and cannot hallucinate.
* **Floor on quality.** These templates cover the four questions the product
  promises to answer. When the LLM is enabled it answers the same questions with
  better prose, but never with different facts.

Nothing here evaluates a rule or touches geometry: it reads a finished report.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import List, Optional

from dfm.models import DFMReport, ProcessReport, ProcessType, RuleStatus, Severity


class QuestionIntent(str, Enum):
    not_manufacturable = "not_manufacturable"
    failed_rules = "failed_rules"
    improve = "improve"
    process_choice = "process_choice"
    score = "score"
    not_assessed = "not_assessed"
    overview = "overview"


_INTENT_PATTERNS: list[tuple[QuestionIntent, str]] = [
    (QuestionIntent.not_manufacturable,
     r"not\s+manufactur|un\s?manufactur|can'?t\s+(be\s+)?(made|manufactur|mould|mold|print)"
     r"|why.*(blocked|blocker|not viable|fail\b)"),
    (QuestionIntent.process_choice,
     r"which\s+process|best\s+process|prefer|recommend.*(process|method)"
     r"|(mould|mold|moulding|molding).*(vs|versus|or)\s*(3d\s*)?print"
     r"|print.*(vs|versus|or).*(mould|mold)"),
    (QuestionIntent.improve,
     r"improve|how\s+(can|do|should)\s+i|fix|redesign|what\s+should\s+i\s+change|make\s+it\s+better"),
    (QuestionIntent.not_assessed,
     r"not\s+assessed|missing\s+data|why\s+(wasn'?t|was\s+not|isn'?t).*(check|assess|run)"
     r"|skipped|unknown"),
    (QuestionIntent.failed_rules,
     r"which\s+rules?|what\s+(rules?|checks?|issues?|problems?)\s+(failed|fired)"
     r"|list.*(issues?|failures?|problems?)|what.*wrong"),
    (QuestionIntent.score,
     r"\bscore\b|\brating\b|how\s+(good|bad|close)"),
]


def classify_intent(question: str) -> QuestionIntent:
    text = (question or "").strip().lower()
    if not text:
        return QuestionIntent.overview
    for intent, pattern in _INTENT_PATTERNS:
        if re.search(pattern, text):
            return intent
    return QuestionIntent.overview


def answer_from_report(report: DFMReport, question: str) -> tuple[str, List[str]]:
    """(answer_text, referenced_rule_ids) for a question about the report."""
    intent = classify_intent(question)
    handler = {
        QuestionIntent.not_manufacturable: _answer_not_manufacturable,
        QuestionIntent.failed_rules: _answer_failed_rules,
        QuestionIntent.improve: _answer_improve,
        QuestionIntent.process_choice: _answer_process_choice,
        QuestionIntent.score: _answer_score,
        QuestionIntent.not_assessed: _answer_not_assessed,
        QuestionIntent.overview: _answer_overview,
    }[intent]
    return handler(report)


# ---------------------------------------------------------------------------
# Answers
# ---------------------------------------------------------------------------

def _answer_not_manufacturable(report: DFMReport) -> tuple[str, List[str]]:
    blocked = [p for p in report.processes if not p.manufacturable]
    if not blocked:
        viable = ", ".join(
            f"{_label(p.process)} ({p.score:.0f}/100)" for p in report.processes
        )
        return (
            f"This part **is** manufacturable as designed: {viable}. "
            "No rule returned a Blocker.",
            [],
        )

    lines: List[str] = []
    rule_ids: List[str] = []
    for process in blocked:
        lines.append(f"**{_label(process.process)} — {process.verdict_label}**")
        for rule in process.rule_results:
            blockers = [f for f in rule.findings if f.severity == Severity.blocker]
            if not blockers:
                continue
            rule_ids.append(rule.rule_id)
            lines.append(f"- `{rule.rule_id}` {rule.name}: {rule.summary}")
            for finding in blockers[:3]:
                lines.append(f"    - {finding.message}")
                lines.append(f"      Fix: {finding.recommendation}")
        if process.assumptions:
            lines.append(f"  _Assumed:_ {process.assumptions[0]}")
        lines.append("")

    viable = [p for p in report.processes if p.manufacturable]
    if viable:
        best = max(viable, key=lambda p: p.score)
        lines.append(
            f"{_label(best.process)} **can** make this part as designed "
            f"({best.score:.0f}/100) — {report.recommendation.reason}"
        )

    header = (
        "A Blocker means the process cannot make the part as designed; only Blockers do "
        "this, Major and Minor findings only reduce the score.\n\n"
    )
    return header + "\n".join(lines).strip(), _dedupe(rule_ids)


def _answer_failed_rules(report: DFMReport) -> tuple[str, List[str]]:
    lines: List[str] = []
    rule_ids: List[str] = []

    for process in report.processes:
        failed = [r for r in process.rule_results if r.status == RuleStatus.failed]
        lines.append(
            f"**{_label(process.process)}** — {process.verdict_label}, "
            f"score {process.score:.0f}/100 ({len(failed)} rule(s) failed)"
        )
        if not failed:
            lines.append("- No rules failed.")
        for rule in sorted(failed, key=lambda r: -r.score_impact):
            rule_ids.append(rule.rule_id)
            severity = rule.severity.value if rule.severity else "issue"
            lines.append(
                f"- `{rule.rule_id}` {rule.name} — **{severity}**, "
                f"-{rule.score_impact:.1f} pts, {len(rule.findings)} finding(s): {rule.summary}"
            )
        not_assessed = process.not_assessed_rule_ids
        if not_assessed:
            lines.append(
                f"- _Not assessed (excluded from the score, no penalty):_ "
                f"{', '.join(not_assessed)}"
            )
        lines.append("")

    return "\n".join(lines).strip(), _dedupe(rule_ids)


def _answer_improve(report: DFMReport) -> tuple[str, List[str]]:
    lines: List[str] = []
    rule_ids: List[str] = []

    for process in report.processes:
        failed = [r for r in process.rule_results if r.status == RuleStatus.failed]
        if not failed:
            continue
        lines.append(
            f"**{_label(process.process)}** (currently {process.score:.0f}/100, "
            f"{process.verdict_label})"
        )
        # Highest score impact first: fixing these moves the score most.
        for rule in sorted(failed, key=lambda r: -r.score_impact):
            rule_ids.append(rule.rule_id)
            lines.append(f"\n_{rule.rule_id} {rule.name} (-{rule.score_impact:.1f} pts)_")
            for recommendation in rule.recommendations[:2]:
                lines.append(f"- {recommendation}")
            if not rule.recommendations and rule.findings:
                lines.append(f"- {rule.findings[0].recommendation}")
        lines.append("")

    if not lines:
        return (
            "No rule failed on this part, so there is nothing to fix — "
            f"the headline score is {report.manufacturability_score:.0f}/100.",
            [],
        )

    lines.append(
        "Fixes are ordered by score impact: the rules at the top of each list move the "
        "score most."
    )
    return "\n".join(lines).strip(), _dedupe(rule_ids)


def _answer_process_choice(report: DFMReport) -> tuple[str, List[str]]:
    recommendation = report.recommendation
    lines: List[str] = []

    if recommendation.recommended_process is not None:
        lines.append(f"**Recommended: {_label(recommendation.recommended_process)}**")
    else:
        lines.append("**No process is recommended as the part currently stands.**")
    lines.append("")
    lines.append(recommendation.reason)
    lines.append("")

    rule_ids: List[str] = []
    for process in report.processes:
        lines.append(
            f"- **{_label(process.process)}**: {process.verdict_label}, "
            f"score {process.score:.0f}/100"
            + (
                f", blocked by {', '.join(process.blocking_rule_ids)}"
                if process.blocking_rule_ids else ""
            )
            + f" (confidence {process.confidence:.0%})"
        )
        rule_ids.extend(process.blocking_rule_ids)
        if process.orientation_assumed:
            lines.append(
                f"    Measured in the {process.orientation_assumed} build orientation."
            )

    return "\n".join(lines).strip(), _dedupe(rule_ids)


def _answer_score(report: DFMReport) -> tuple[str, List[str]]:
    lines = [
        f"Headline score: **{report.manufacturability_score:.0f}/100** — "
        f"manufacturable: **{'yes' if report.manufacturable else 'no'}**.",
        "",
    ]
    rule_ids: List[str] = []

    for process in report.processes:
        lines.append(
            f"**{_label(process.process)}: {process.score:.0f}/100** "
            f"({process.verdict_label}, confidence {process.confidence:.0%})"
        )
        for sub in process.sub_scores:
            score_text = (
                f"{sub.score:.0f}/100" if sub.score is not None else "not assessed"
            )
            lines.append(
                f"- {sub.sub_score.value.replace('_', '/')}: {score_text} "
                f"({sub.assessed_rules}/{sub.total_rules} rules assessed)"
            )
        deductions = [
            r for r in process.rule_results if r.score_impact > 0
        ]
        for rule in sorted(deductions, key=lambda r: -r.score_impact):
            rule_ids.append(rule.rule_id)
            lines.append(f"- `{rule.rule_id}` cost {rule.score_impact:.1f} points")
        if not process.manufacturable:
            lines.append(
                f"- A Blocker in {', '.join(process.blocking_rule_ids)} capped this score."
            )
        lines.append("")

    lines.append(
        "Rules reported as Not assessed are excluded from the score entirely — missing "
        "optional input never lowers the result."
    )
    return "\n".join(lines).strip(), _dedupe(rule_ids)


def _answer_not_assessed(report: DFMReport) -> tuple[str, List[str]]:
    lines: List[str] = []
    rule_ids: List[str] = []

    for process in report.processes:
        skipped = [
            r for r in process.rule_results
            if r.status in (RuleStatus.not_assessed, RuleStatus.suppressed, RuleStatus.error)
        ]
        if not skipped:
            continue
        lines.append(f"**{_label(process.process)}**")
        for rule in skipped:
            rule_ids.append(rule.rule_id)
            lines.append(
                f"- `{rule.rule_id}` {rule.name} ({rule.status.value}): "
                f"{rule.not_assessed_reason}"
            )
            if rule.missing_inputs:
                lines.append(f"    Needs: {', '.join(rule.missing_inputs)}")
        lines.append("")

    if not lines:
        return ("Every rule ran on real data for this part — nothing was skipped.", [])

    lines.append(
        "None of these lowered the score: unassessed rules are excluded from the roll-up "
        "denominator entirely."
    )
    if report.warnings:
        lines.append("")
        lines.append("Input warnings: " + " ".join(report.warnings))
    return "\n".join(lines).strip(), _dedupe(rule_ids)


def _answer_overview(report: DFMReport) -> tuple[str, List[str]]:
    part = report.part
    lines = [
        f"**{part.filename or 'This part'}** — "
        f"{'manufacturable' if report.manufacturable else 'not manufacturable as designed'}, "
        f"score {report.manufacturability_score:.0f}/100.",
        "",
    ]
    if part.bounding_box_mm:
        lines.append(
            f"- Size: {part.bounding_box_mm[0]:.0f} x {part.bounding_box_mm[1]:.0f} x "
            f"{part.bounding_box_mm[2]:.0f} mm"
            + (f", nominal wall {part.nominal_wall_mm:.2f} mm" if part.nominal_wall_mm else "")
        )

    rule_ids: List[str] = []
    for process in report.processes:
        failed = [r for r in process.rule_results if r.status == RuleStatus.failed]
        rule_ids.extend(r.rule_id for r in failed)
        lines.append(
            f"- **{_label(process.process)}**: {process.verdict_label}, "
            f"{process.score:.0f}/100, {len(failed)} failed rule(s)"
            + (
                f", blocked by {', '.join(process.blocking_rule_ids)}"
                if process.blocking_rule_ids else ""
            )
        )

    lines.append("")
    lines.append(report.recommendation.reason)
    lines.append("")
    lines.append(
        "Ask about a specific rule, why the part is not manufacturable, how to improve it, "
        "or why one process is preferred."
    )
    return "\n".join(lines).strip(), _dedupe(rule_ids)


# ---------------------------------------------------------------------------

def _label(process: ProcessType) -> str:
    return {
        ProcessType.injection_molding: "Injection moulding",
        ProcessType.printing: "3D printing",
    }.get(process, process.value.replace("_", " ").title())


def _dedupe(values: List[str]) -> List[str]:
    seen: set[str] = set()
    result: List[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def process_by_name(report: DFMReport, name: Optional[str]) -> Optional[ProcessReport]:
    if not name:
        return None
    try:
        return report.process_report(ProcessType(name))
    except ValueError:
        return None
