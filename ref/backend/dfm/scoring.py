"""Configurable scoring engine.

The final weights are not frozen, so nothing here hardcodes a number: every
value comes from ``scoring.yaml``. The engine implements the MVP guidance
agreed in the team thread while leaving each decision switchable.

Rules applied, in order:

1. Each finding deducts ``severity_weights[severity]`` from the start score.
2. The total deduction from any one rule is clamped to
   ``per_rule_impact_cap`` — repeated instances of the same problem cannot
   dominate the score. Each finding's ``score_impact`` is scaled so the parts
   still sum to the capped whole.
3. ``not_assessed`` / ``suppressed`` / ``error`` rules deduct nothing and leave
   the roll-up denominator entirely — a blank optional field never costs points.
4. A Blocker sets ``manufacturable = False`` and applies ``blocker.mode``:
   ``cap`` (default) clamps the score below the redesign threshold, ``zero``
   sends it to 0, ``deduct`` lets the Blocker weight deduct like any other tier.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from .config import DFMConfig
from .models import (
    ProcessReport,
    ProcessRecommendation,
    ProcessType,
    RuleResult,
    RuleStatus,
    Severity,
    SubScore,
    SubScoreResult,
)


class ScoringEngine:
    """Turns a list of rule results into scores and a verdict."""

    def __init__(self, config: DFMConfig):
        self.config = config

    # ------------------------------------------------------------------
    # Per-process scoring
    # ------------------------------------------------------------------

    def score_process(
        self,
        process: ProcessType,
        rule_results: List[RuleResult],
        assumptions: List[str],
        orientation_assumed: Optional[str] = None,
    ) -> ProcessReport:
        deduct_blockers = self.config.blocker_mode == "deduct"
        has_blocker = False

        # -- 1 & 2: deductions, capped per rule --------------------------
        for result in rule_results:
            impact = self._apply_rule_deductions(result, deduct_blockers)
            result.score_impact = impact
            if any(f.severity == Severity.blocker for f in result.findings):
                has_blocker = True

        total_deduction = sum(result.score_impact for result in rule_results)
        start = self.config.start_score
        score = max(0.0, min(start, start - total_deduction))

        sub_scores = self._sub_scores(rule_results, start)

        if self.config.rollup_mode == "weighted":
            weighted = self._weighted_rollup(sub_scores)
            if weighted is not None:
                score = weighted

        # -- 4: blocker handling -----------------------------------------
        manufacturable = not has_blocker
        if has_blocker:
            mode = self.config.blocker_mode
            if mode == "zero":
                score = 0.0
            elif mode == "cap":
                score = min(score, self.config.blocker_cap_value)
            # mode == "deduct": the deduction above already did the work.

        blocking_rule_ids = [
            result.rule_id
            for result in rule_results
            if any(f.severity == Severity.blocker for f in result.findings)
        ]
        not_assessed_rule_ids = [
            result.rule_id
            for result in rule_results
            if result.status in (RuleStatus.not_assessed, RuleStatus.error)
        ]

        label, redesign = self._verdict(score, manufacturable)

        return ProcessReport(
            process=process,
            manufacturable=manufacturable,
            score=round(score, 1),
            verdict_label=label,
            redesign_recommended=redesign,
            confidence=self._confidence(rule_results, assumptions),
            sub_scores=sub_scores,
            rule_results=rule_results,
            blocking_rule_ids=blocking_rule_ids,
            not_assessed_rule_ids=not_assessed_rule_ids,
            assumptions=_dedupe(assumptions),
            orientation_assumed=orientation_assumed,
        )

    # ------------------------------------------------------------------

    def _apply_rule_deductions(self, result: RuleResult, deduct_blockers: bool) -> float:
        """Deduct for each finding, then clamp the rule's total impact."""
        if result.status != RuleStatus.failed or not result.findings:
            for finding in result.findings:
                finding.score_impact = 0.0
            return 0.0

        raw: List[float] = []
        for finding in result.findings:
            if finding.severity == Severity.blocker and not deduct_blockers:
                # Blockers are handled by blocker.mode, not by deduction.
                raw.append(0.0)
            else:
                raw.append(self.config.severity_weight(finding.severity.value))

        raw_total = sum(raw)
        cap = self.config.rule_impact_cap(result.rule_id)
        capped_total = min(raw_total, cap)

        # Scale each finding's share so the reported impacts sum to the capped
        # total — the user sees where the points actually went.
        scale = (capped_total / raw_total) if raw_total > 0 else 0.0
        for finding, value in zip(result.findings, raw):
            finding.score_impact = round(value * scale, 3)

        return capped_total

    def _sub_scores(
        self, rule_results: List[RuleResult], start: float
    ) -> List[SubScoreResult]:
        """One score per PRD bucket. A bucket where every rule was
        ``not_assessed`` reports ``None`` rather than a misleading 100."""
        buckets: Dict[SubScore, List[RuleResult]] = {bucket: [] for bucket in SubScore}
        for result in rule_results:
            buckets[result.sub_score].append(result)

        sub_scores: List[SubScoreResult] = []
        for bucket, results in buckets.items():
            if not results:
                continue
            assessed = [r for r in results if r.counts_toward_score]
            deductions = sum(r.score_impact for r in results)
            score = None
            if assessed:
                score = round(max(0.0, min(start, start - deductions)), 1)
            sub_scores.append(SubScoreResult(
                sub_score=bucket,
                score=score,
                assessed_rules=len(assessed),
                total_rules=len(results),
                deductions=round(deductions, 3),
            ))
        return sub_scores

    def _weighted_rollup(self, sub_scores: List[SubScoreResult]) -> Optional[float]:
        """Weighted sum of the assessed buckets, weights renormalised so a
        not-assessed bucket shrinks the denominator instead of scoring zero."""
        weights = self.config.rollup_weights
        usable = [s for s in sub_scores if s.score is not None and weights.get(s.sub_score.value)]
        if not usable:
            return None
        total_weight = sum(weights[s.sub_score.value] for s in usable)
        if total_weight <= 0:
            return None
        return sum(
            weights[s.sub_score.value] * (s.score or 0.0) for s in usable
        ) / total_weight

    def _verdict(self, score: float, manufacturable: bool) -> Tuple[str, bool]:
        if not manufacturable:
            return self.config.verdict_label("not_viable"), True
        if score < self.config.redesign_below:
            return self.config.verdict_label("redesign"), True
        if score < self.config.review_below:
            return self.config.verdict_label("review"), False
        return self.config.verdict_label("manufacturable"), False

    def _confidence(self, rule_results: List[RuleResult], assumptions: List[str]) -> float:
        """Coverage signal, never a score modifier.

        Falls with each rule that could not run and with each stated default the
        run leaned on, so a report built entirely on assumptions reads as one.
        """
        if not rule_results:
            return 0.0
        assessed = sum(1 for r in rule_results if r.counts_toward_score)
        coverage = assessed / len(rule_results)
        penalty = self.config.confidence_assumption_penalty * len(_dedupe(assumptions))
        return round(
            max(self.config.confidence_floor, min(1.0, coverage - penalty)), 2
        )

    # ------------------------------------------------------------------
    # Best-process recommendation
    # ------------------------------------------------------------------

    def recommend_process(self, reports: List[ProcessReport]) -> ProcessRecommendation:
        """Compare process reports and pick one.

        Cross-link from the spec: an un-mouldable undercut Blocker (M4) directly
        boosts 3D printing, because the two check-sets are not independent.
        """
        if not reports:
            return ProcessRecommendation(reason="No process was evaluated.")

        comparison = {
            report.process.value: (
                f"{report.verdict_label} — score {report.score:.0f}/100"
                + (
                    f", blocked by {', '.join(report.blocking_rule_ids)}"
                    if report.blocking_rule_ids else ""
                )
            )
            for report in reports
        }

        if len(reports) == 1:
            only = reports[0]
            return ProcessRecommendation(
                recommended_process=only.process if only.manufacturable else None,
                reason=(
                    f"Only {_label(only.process)} was evaluated: {only.verdict_label.lower()} "
                    f"with a score of {only.score:.0f}/100."
                ),
                comparison=comparison,
            )

        # Effective score used for ranking only — the reported score is untouched.
        bonus: Dict[ProcessType, float] = {report.process: 0.0 for report in reports}
        molding = next(
            (r for r in reports if r.process == ProcessType.injection_molding), None
        )
        printing = next((r for r in reports if r.process == ProcessType.printing), None)
        m4_blocked = bool(molding and "M4" in molding.blocking_rule_ids)
        if m4_blocked and printing is not None:
            bonus[printing.process] = self.config.m4_blocker_printing_bonus

        def rank_key(report: ProcessReport) -> Tuple[int, float]:
            return (1 if report.manufacturable else 0, report.score + bonus[report.process])

        ranked = sorted(reports, key=rank_key, reverse=True)
        best, runner_up = ranked[0], ranked[1]

        if not best.manufacturable:
            return ProcessRecommendation(
                recommended_process=None,
                reason=(
                    "Neither process can make this part as designed: "
                    + "; ".join(
                        f"{_label(r.process)} is blocked by "
                        f"{', '.join(r.blocking_rule_ids) or 'a blocking issue'}"
                        for r in reports
                    )
                    + "."
                ),
                comparison=comparison,
            )

        if m4_blocked and best.process == ProcessType.printing:
            reason = (
                f"{_label(best.process)} is recommended: the part has an undercut that cannot be "
                f"released by the mould (M4), which rules out injection moulding as designed, "
                f"while printing scores {best.score:.0f}/100."
            )
        elif not runner_up.manufacturable:
            reason = (
                f"{_label(best.process)} is recommended: it scores {best.score:.0f}/100, while "
                f"{_label(runner_up.process)} is not viable "
                f"({', '.join(runner_up.blocking_rule_ids) or 'blocked'})."
            )
        elif abs(best.score - runner_up.score) <= self.config.recommendation_tie_margin:
            reason = (
                f"Both processes are viable and score within "
                f"{self.config.recommendation_tie_margin:.0f} points "
                f"({_label(best.process)} {best.score:.0f}, "
                f"{_label(runner_up.process)} {runner_up.score:.0f}); "
                f"{_label(best.process)} edges it, so choose on volume and cost rather than "
                f"manufacturability."
            )
        else:
            reason = (
                f"{_label(best.process)} is recommended: it scores {best.score:.0f}/100 against "
                f"{runner_up.score:.0f}/100 for {_label(runner_up.process)}."
            )

        return ProcessRecommendation(
            recommended_process=best.process,
            reason=reason,
            comparison=comparison,
        )


def _label(process: ProcessType) -> str:
    return {
        ProcessType.injection_molding: "Injection moulding",
        ProcessType.printing: "3D printing",
    }.get(process, process.value.replace("_", " ").title())


def _dedupe(values: List[str]) -> List[str]:
    """Order-preserving de-duplication for assumption lists."""
    seen: set[str] = set()
    result: List[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result
