"""M6 · Boss Design (Type 2 — same ratio family as ribs)."""

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


class BossDesignRule(RuleEvaluator):
    """Standalone thick masses sink and trap internal voids.

    Two shapes of the same problem:

    * a **hollow boss** is judged on its wall thickness, which follows the same
      40–60%-of-nominal-wall guideline as ribs and gussets;
    * a **solid boss** has no wall to measure — it *is* the thick mass, so it is
      judged on diameter against the nominal wall and the fix is to core it out.

    Like M5, an absent ``bosses[]`` array means the detector did not run
    (Not assessed), while an empty array means it ran and found nothing (pass).
    """

    rule_id = "M6"
    name = "Boss Design"
    process = ProcessType.injection_molding
    sub_score = SubScore.geometry
    threshold_type = ThresholdType.geometric_ratio
    what_it_flags = (
        "Bosses thicker than about 60% of the nominal wall, or solid bulky bosses, cool slowly "
        "and pull sink marks or leave internal voids."
    )

    def _evaluate(self, context: EvaluationContext) -> RuleResult:
        bosses = context.geometry.bosses
        if bosses is None:
            return self.not_assessed(
                "The geometry engine did not report a bosses[] array — boss feature recognition "
                "is not available for this part.",
                missing_inputs=["bosses"],
            )

        if not bosses and self.thresholds.get("treat_empty_as_not_assessed", False):
            return self.not_assessed(
                "Boss detection returned no features and the engine is configured to treat an "
                "empty bosses[] array as unassessed.",
                missing_inputs=["bosses"],
            )

        nominal = context.nominal_wall()
        if not nominal:
            return self.not_assessed(
                "No nominal wall thickness is available to ratio boss thickness against.",
                missing_inputs=["nominal_wall"],
            )

        major_above = float(self.thresholds.get("major_above", 0.6))
        minor_above = float(self.thresholds.get("minor_above", 0.4))
        core_out_ratio = float(self.thresholds.get("solid_core_out_diameter_ratio", 2.0))
        solid_minor_ratio = float(self.thresholds.get("solid_minor_diameter_ratio", 1.5))

        thresholds_used = {
            "nominal_wall_mm": round(nominal, 3),
            "major_above_ratio": major_above,
            "minor_above_ratio": minor_above,
            "solid_core_out_diameter_ratio": core_out_ratio,
            "bosses_reported": len(bosses),
            "bosses_evaluated": 0,
        }

        if not bosses:
            return self.passed(
                summary="No bosses were detected on this part.",
                thresholds_used=thresholds_used,
            )

        findings: List[Finding] = []
        assumptions: List[str] = []
        evaluated = 0
        skipped: List[int] = []
        index = 0
        used_part_nominal = False

        for boss in bosses:
            base_wall = boss.base_wall_thickness
            if not base_wall or base_wall <= 0:
                base_wall = nominal
                used_part_nominal = True

            is_solid = boss.is_solid
            if is_solid is None:
                is_solid = boss.inner_diameter is None

            if not is_solid and boss.wall_thickness and boss.wall_thickness > 0:
                evaluated += 1
                ratio = boss.wall_thickness / base_wall
                if ratio > major_above:
                    severity = Severity.major
                elif ratio > minor_above:
                    severity = Severity.minor
                else:
                    continue
                findings.append(self.finding(
                    severity=severity,
                    message=(
                        f"Boss {boss.id} has a {boss.wall_thickness:.2f} mm wall, "
                        f"{ratio * 100:.0f}% of the {base_wall:.2f} mm nominal wall "
                        f"(guideline: {minor_above * 100:.0f}–{major_above * 100:.0f}%)."
                    ),
                    recommendation=(
                        f"Thin the boss wall to {base_wall * minor_above:.2f}–"
                        f"{base_wall * major_above:.2f} mm and blend it into the wall with a "
                        f"fillet rather than an abrupt join."
                    ),
                    index=index,
                    measured=round(ratio, 3),
                    threshold=major_above,
                    unit="ratio",
                    geometry_ref=self.feature_ref("boss", [boss.id], boss.center, boss.faces),
                ))
                index += 1
                continue

            if is_solid and boss.outer_diameter and boss.outer_diameter > 0:
                evaluated += 1
                ratio = boss.outer_diameter / base_wall
                if ratio > core_out_ratio:
                    severity = Severity.major
                    verdict = "a thick standalone mass that will sink or void"
                elif ratio > solid_minor_ratio:
                    severity = Severity.minor
                    verdict = "bulky enough to risk a sink mark"
                else:
                    continue
                findings.append(self.finding(
                    severity=severity,
                    message=(
                        f"Boss {boss.id} is solid at ø{boss.outer_diameter:.2f} mm, "
                        f"{ratio:.1f}x the {base_wall:.2f} mm nominal wall — {verdict}."
                    ),
                    recommendation=(
                        f"Core the boss out to a wall of {base_wall * minor_above:.2f}–"
                        f"{base_wall * major_above:.2f} mm and support it with gussets instead "
                        f"of solid material."
                    ),
                    index=index,
                    measured=round(ratio, 3),
                    threshold=core_out_ratio,
                    unit="ratio",
                    geometry_ref=self.feature_ref("boss", [boss.id], boss.center, boss.faces),
                ))
                index += 1
                continue

            skipped.append(boss.id)

        thresholds_used["bosses_evaluated"] = evaluated
        if skipped:
            thresholds_used["bosses_without_measurements"] = skipped
            assumptions.append(
                f"{len(skipped)} boss(es) carried neither a wall thickness nor a diameter and "
                f"were skipped rather than counted against the part."
            )
        if used_part_nominal:
            assumptions.append(
                f"Boss ratios were taken against the part's nominal wall ({nominal:.2f} mm) "
                f"because the geometry engine does not yet report the local wall each boss "
                f"sits on."
            )

        if evaluated == 0:
            return self.not_assessed(
                "Bosses were reported but none carried usable dimensions.",
                missing_inputs=["bosses[].wall_thickness", "bosses[].outer_diameter"],
                assumptions=assumptions,
            )

        if not findings:
            return self.passed(
                summary=(
                    f"All {evaluated} boss(es) are within the "
                    f"{minor_above * 100:.0f}–{major_above * 100:.0f}% wall guideline."
                ),
                thresholds_used=thresholds_used,
                assumptions=assumptions,
            )

        return self.failed(
            summary=f"{len(findings)} of {evaluated} boss(es) form a thick mass.",
            findings=self.cap_findings(findings),
            recommendations=[
                f"Hold boss walls to {minor_above * 100:.0f}–{major_above * 100:.0f}% of the "
                f"nominal wall.",
                "Core out bulky bosses and blend them into the wall instead of joining abruptly.",
            ],
            thresholds_used=thresholds_used,
            assumptions=assumptions,
        )
