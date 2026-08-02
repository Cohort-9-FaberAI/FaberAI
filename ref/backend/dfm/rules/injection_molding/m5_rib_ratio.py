"""M5 · Rib Thickness Ratio (Type 2 — material-independent ratio)."""

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


class RibThicknessRule(RuleEvaluator):
    """Thick ribs create a localized hot spot that cools slower than the wall
    it sits on, producing a visible sink mark on the show surface.

    Clean Type 2 ratio — no material lookup. Rib base thickness should be
    50–60% of the nominal wall; the common belief that 80% is safe is false.

    Geometry dependency: ``ribs[]`` with a base thickness. Rib recognition is
    still landing in the geometry engine, so the three states are handled
    distinctly — array absent → Not assessed; array present but empty → pass
    ("detector ran, found no ribs"); rib present without a thickness → that rib
    is skipped and reported as missing data, the others still evaluate.
    """

    rule_id = "M5"
    name = "Rib Thickness Ratio"
    process = ProcessType.injection_molding
    sub_score = SubScore.geometry
    threshold_type = ThresholdType.geometric_ratio
    what_it_flags = (
        "A rib thicker than about 60% of the wall it joins cools slower than the wall and pulls "
        "a sink mark into the opposite surface."
    )

    def _evaluate(self, context: EvaluationContext) -> RuleResult:
        ribs = context.geometry.ribs
        if ribs is None:
            return self.not_assessed(
                "The geometry engine did not report a ribs[] array — rib feature recognition is "
                "not available for this part.",
                missing_inputs=["ribs"],
            )

        if not ribs and self.thresholds.get("treat_empty_as_not_assessed", False):
            return self.not_assessed(
                "Rib detection returned no features and the engine is configured to treat an "
                "empty ribs[] array as unassessed.",
                missing_inputs=["ribs"],
            )

        nominal = context.nominal_wall()
        if not nominal:
            return self.not_assessed(
                "No nominal wall thickness is available to ratio the rib thickness against.",
                missing_inputs=["nominal_wall"],
            )

        major_above = float(self.thresholds.get("major_above", 0.6))
        minor_above = float(self.thresholds.get("minor_above", 0.5))

        thresholds_used = {
            "nominal_wall_mm": round(nominal, 3),
            "major_above_ratio": major_above,
            "minor_above_ratio": minor_above,
            "ribs_evaluated": 0,
            "ribs_reported": len(ribs),
        }

        if not ribs:
            return self.passed(
                summary="No ribs were detected on this part, so there is no rib-to-wall ratio to check.",
                thresholds_used=thresholds_used,
            )

        findings: List[Finding] = []
        assumptions: List[str] = []
        skipped: List[int] = []
        evaluated = 0
        index = 0
        used_part_nominal = False

        for rib in ribs:
            if not rib.thickness or rib.thickness <= 0:
                skipped.append(rib.id)
                continue

            # Prefer the thickness of the wall this rib actually grows from;
            # fall back to the part nominal wall when the geometry engine does
            # not supply it.
            base_wall = rib.base_wall_thickness
            if not base_wall or base_wall <= 0:
                base_wall = nominal
                used_part_nominal = True

            evaluated += 1
            ratio = rib.thickness / base_wall

            if ratio > major_above:
                severity = Severity.major
                verdict = "sink marks are likely"
            elif ratio > minor_above:
                severity = Severity.minor
                verdict = "borderline — at the top of the 50–60% band"
            else:
                continue

            findings.append(self.finding(
                severity=severity,
                message=(
                    f"Rib {rib.id} is {rib.thickness:.2f} mm at the base, "
                    f"{ratio * 100:.0f}% of the {base_wall:.2f} mm wall — {verdict}."
                ),
                recommendation=(
                    f"Reduce the rib base to {base_wall * minor_above:.2f}–"
                    f"{base_wall * major_above:.2f} mm (50–60% of the wall). Add height or more "
                    f"ribs rather than thickness if you need stiffness."
                ),
                index=index,
                measured=round(ratio, 3),
                threshold=major_above,
                unit="ratio",
                geometry_ref=self.feature_ref("rib", [rib.id], rib.center, rib.face_pair),
            ))
            index += 1

        thresholds_used["ribs_evaluated"] = evaluated
        if skipped:
            thresholds_used["ribs_without_thickness"] = skipped
            assumptions.append(
                f"{len(skipped)} rib(s) had no base thickness from the geometry engine and were "
                f"skipped rather than counted against the part."
            )
        if used_part_nominal:
            assumptions.append(
                f"Rib ratios were taken against the part's nominal wall ({nominal:.2f} mm) "
                f"because the geometry engine does not yet report the local wall each rib "
                f"joins."
            )

        if evaluated == 0:
            return self.not_assessed(
                "Ribs were reported but none carried a usable base thickness.",
                missing_inputs=["ribs[].thickness"],
                assumptions=assumptions,
            )

        if not findings:
            return self.passed(
                summary=(
                    f"All {evaluated} rib(s) are at or below {minor_above * 100:.0f}% of the "
                    f"{nominal:.2f} mm nominal wall."
                ),
                thresholds_used=thresholds_used,
                assumptions=assumptions,
            )

        return self.failed(
            summary=(
                f"{len(findings)} of {evaluated} rib(s) exceed "
                f"{minor_above * 100:.0f}% of the nominal wall."
            ),
            findings=self.cap_findings(findings),
            recommendations=[
                f"Keep rib base thickness between {minor_above * 100:.0f}% and "
                f"{major_above * 100:.0f}% of the adjoining wall.",
                "Gain stiffness with rib height, count or gussets — not rib thickness.",
            ],
            thresholds_used=thresholds_used,
            assumptions=assumptions,
        )
