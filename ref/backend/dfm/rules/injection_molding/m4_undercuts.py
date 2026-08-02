"""M4 · Undercuts (Type 3 — topological, not a threshold)."""

from __future__ import annotations

from typing import List

from ...base import RuleEvaluator
from ...context import EvaluationContext
from ...models import (
    Finding,
    ProcessType,
    RuleResult,
    Severity,
    SubScore,
    ThresholdType,
)


class UndercutRule(RuleEvaluator):
    """Features that cannot release along the parting direction.

    Detection is the geometry engine's job — this rule never reasons about
    B-rep topology itself. It consumes, in order of preference:

    1. ``undercuts[]`` from the geometry engine (not shipped yet). Severity
       follows actionability, not size: solvable with a side-action → Major
       (tooling cost, feeds Cost-Risk); un-actionable → Blocker.
    2. A conservative inference from ``holes[]``: a hole whose axis is not
       parallel to the pull direction cannot be cored along the parting line
       and needs a side-action. Inferences are capped at Major by
       ``inferred_max_severity`` — the engine will not call a part unmouldable
       on an inference.
    3. Neither available → Not assessed.

    Cross-link: an un-actionable undercut Blocker here pushes the best-process
    recommendation toward 3D printing (see ``dfm/scoring.py``).
    """

    rule_id = "M4"
    name = "Undercuts"
    process = ProcessType.injection_molding
    sub_score = SubScore.cost_risk
    threshold_type = ThresholdType.topological
    what_it_flags = (
        "Features the mould cannot release along its opening direction, requiring side-actions "
        "or lifters — or making the part unmouldable altogether."
    )

    def _evaluate(self, context: EvaluationContext) -> RuleResult:
        assumptions: List[str] = []
        if context.parting_axis_assumption:
            assumptions.append(context.parting_axis_assumption)

        if context.geometry.undercuts is not None:
            return self._from_detection(context, assumptions)
        return self._from_hole_inference(context, assumptions)

    # ------------------------------------------------------------------

    def _from_detection(
        self, context: EvaluationContext, assumptions: List[str]
    ) -> RuleResult:
        """Path taken once the geometry engine ships undercut detection."""
        undercuts = context.geometry.undercuts or []
        thresholds_used = {
            "source": "geometry.undercuts",
            "parting_direction": context.parting_axis,
            "undercuts_detected": len(undercuts),
        }

        if not undercuts:
            return self.passed(
                summary=(
                    f"No undercuts: every feature releases along the {context.parting_axis} "
                    f"pull direction."
                ),
                thresholds_used=thresholds_used,
                assumptions=assumptions,
            )

        findings: List[Finding] = []
        for index, undercut in enumerate(undercuts):
            # releasable is the authoritative flag; requires_side_action refines
            # a releasable feature into "needs tooling" vs "opens cleanly".
            unactionable = undercut.releasable is False
            severity = Severity.blocker if unactionable else Severity.major
            if unactionable:
                message = (
                    f"Undercut {undercut.id} cannot be released in any mould-opening "
                    f"direction — the part is not mouldable as designed."
                )
                recommendation = (
                    "Redesign the feature to open along the parting line, split the part, or "
                    "move this part to 3D printing."
                )
            else:
                message = (
                    f"Undercut {undercut.id} needs a side-action or lifter to release along "
                    f"{context.parting_axis}."
                )
                recommendation = (
                    "Either redesign the feature to open along the parting line, or budget for "
                    "a side-action — it adds tooling cost and cycle time."
                )
            findings.append(self.finding(
                severity=severity,
                message=message,
                recommendation=recommendation,
                index=index,
                geometry_ref=self.feature_ref(
                    "undercut", [undercut.id], undercut.center, undercut.face_ids
                ),
            ))

        blockers = sum(1 for f in findings if f.severity == Severity.blocker)
        return self.failed(
            summary=(
                f"{len(findings)} undercut(s) detected"
                + (f", {blockers} of them un-actionable" if blockers else
                   " — all solvable with side-actions")
                + "."
            ),
            findings=self.cap_findings(findings),
            recommendations=[
                "Reorient the parting line so features release along the pull direction.",
                "Where a side-action is unavoidable, confirm the tooling cost is acceptable.",
            ],
            thresholds_used=thresholds_used,
            assumptions=assumptions,
        )

    # ------------------------------------------------------------------

    def _from_hole_inference(
        self, context: EvaluationContext, assumptions: List[str]
    ) -> RuleResult:
        """Fallback while undercut detection is still a geometry-side spike."""
        holes = context.geometry.holes
        if not holes:
            return self.not_assessed(
                "The geometry engine does not yet report undercut detection, and the part has "
                "no cylindrical features to infer side-actions from.",
                missing_inputs=["undercuts"],
                assumptions=assumptions,
            )

        tolerance = float(self.thresholds.get("hole_axis_tolerance_deg", 15.0))
        max_severity = str(self.thresholds.get("inferred_max_severity", "major")).lower()
        severity = Severity.major if max_severity == "major" else Severity.minor

        assumptions.append(
            "Undercut detection is not yet available from the geometry engine. This result is "
            "inferred from cylindrical feature axes only and is capped at "
            f"{severity.value} severity — it cannot mark the part unmouldable."
        )

        findings: List[Finding] = []
        index = 0
        checked = 0
        for hole in holes:
            if hole.axis is None:
                continue
            angle = context.angle_between_axis_and_vector(
                context.parting_axis, (hole.axis.x, hole.axis.y, hole.axis.z)
            )
            if angle is None:
                continue
            checked += 1
            # A hole is coreable along the pull direction if its axis is
            # parallel or antiparallel to it.
            off_axis = min(angle, 180.0 - angle)
            if off_axis <= tolerance:
                continue
            findings.append(self.finding(
                severity=severity,
                message=(
                    f"Hole {hole.id} (ø{hole.diameter:.1f} mm) runs {off_axis:.0f}° off the "
                    f"{context.parting_axis} pull direction, so it cannot be cored along the "
                    f"parting line."
                ),
                recommendation=(
                    "Reorient the hole to the pull direction, or plan a side-action core — it "
                    "adds tooling cost."
                ),
                index=index,
                measured=round(off_axis, 1),
                threshold=tolerance,
                unit="deg",
                geometry_ref=self.feature_ref(
                    "hole", [hole.id], hole.center, hole.cylindrical_faces
                ),
            ))
            index += 1

        thresholds_used = {
            "source": "inferred from holes[] (undercut detection unavailable)",
            "parting_direction": context.parting_axis,
            "hole_axis_tolerance_deg": tolerance,
            "holes_checked": checked,
            "inferred_max_severity": severity.value,
        }

        if checked == 0:
            return self.not_assessed(
                "The geometry engine does not yet report undercut detection, and no usable "
                "feature axes were available to infer side-actions from.",
                missing_inputs=["undercuts"],
                assumptions=assumptions,
            )

        if not findings:
            return self.passed(
                summary=(
                    f"No side-actions inferred: all {checked} cylindrical feature(s) core along "
                    f"the {context.parting_axis} pull direction. Full undercut detection is "
                    f"still pending in the geometry engine."
                ),
                thresholds_used=thresholds_used,
                assumptions=assumptions,
            )

        return self.failed(
            summary=(
                f"{len(findings)} feature(s) appear to need a side-action (inferred from "
                f"feature axes; full undercut detection pending)."
            ),
            findings=self.cap_findings(findings),
            recommendations=[
                "Reorient off-axis features to the pull direction where the design allows.",
                "Budget for side-action tooling on the features that must stay off-axis.",
            ],
            thresholds_used=thresholds_used,
            assumptions=assumptions,
        )
