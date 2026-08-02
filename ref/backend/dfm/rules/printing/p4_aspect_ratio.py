"""P4 · Aspect Ratio / Tall-Thin (Type 2 — geometric ratio)."""

from __future__ import annotations

from ...base import RuleEvaluator
from ...context import EvaluationContext
from ...models import (
    ProcessType,
    RuleResult,
    Severity,
    SubScore,
    ThresholdType,
)


class AspectRatioRule(RuleEvaluator):
    """Tall, thin geometry warps, wobbles, or detaches from the bed mid-print.

    Ratio of build-direction height to the smallest footprint dimension, taken
    from the bounding box the geometry engine already produced and permuted
    into the chosen build orientation. Short parts are exempt regardless of
    ratio — a 6 mm tall part on a 2 mm footprint is not a stability problem.

    The exact cutoff is explicitly unfrozen in the spec ("tune with the expert
    against test parts"), which is why both bounds live in thresholds.yaml.
    """

    rule_id = "P4"
    name = "Aspect Ratio / Tall-Thin"
    process = ProcessType.printing
    sub_score = SubScore.geometry
    threshold_type = ThresholdType.geometric_ratio
    what_it_flags = (
        "Tall parts on a small footprint wobble as the head moves, warp as they cool, and can "
        "shear off the bed mid-print."
    )

    def _evaluate(self, context: EvaluationContext) -> RuleResult:
        extents = context.extents_in_build_frame()
        if extents is None:
            return self.not_assessed(
                "The geometry engine reported no usable bounding box, so the height-to-footprint "
                "ratio cannot be taken.",
                missing_inputs=["bounding_box"],
                assumptions=[context.build_axis_assumption],
            )

        footprint_a, footprint_b, height = extents
        smallest_footprint = min(footprint_a, footprint_b)
        if smallest_footprint <= 0:
            return self.not_assessed(
                "The part's footprint measures zero in one axis — the bounding box looks "
                "degenerate.",
                missing_inputs=["bounding_box"],
            )

        major_above = float(self.thresholds.get("major_above", 4.0))
        minor_above = float(self.thresholds.get("minor_above", 2.0))
        min_height = float(self.thresholds.get("min_height_mm", 20.0))
        fillet_mm = float(self.thresholds.get("recommended_base_fillet_mm", 1.0))

        ratio = height / smallest_footprint
        assumptions = [a for a in (context.build_axis_assumption,) if a]

        thresholds_used = {
            "build_orientation": context.build_axis,
            "height_mm": round(height, 2),
            "footprint_mm": [round(footprint_a, 2), round(footprint_b, 2)],
            "aspect_ratio": round(ratio, 2),
            "minor_above": minor_above,
            "major_above": major_above,
            "min_height_mm": min_height,
        }

        if height < min_height:
            return self.passed(
                summary=(
                    f"Part is only {height:.1f} mm tall in the {context.build_axis} orientation — "
                    f"too short for a stability problem."
                ),
                thresholds_used=thresholds_used,
                assumptions=assumptions,
            )

        if ratio <= minor_above:
            return self.passed(
                summary=(
                    f"Height-to-footprint ratio is {ratio:.1f}:1 "
                    f"({height:.0f} mm tall on a {smallest_footprint:.0f} mm base) — stable."
                ),
                thresholds_used=thresholds_used,
                assumptions=assumptions,
            )

        severity = Severity.major if ratio > major_above else Severity.minor
        stability_note = (
            "likely to wobble or detach from the bed"
            if severity == Severity.major else
            "tall enough to warrant a brim or raft"
        )

        finding = self.finding(
            severity=severity,
            message=(
                f"Height-to-footprint ratio is {ratio:.1f}:1 ({height:.0f} mm tall on a "
                f"{smallest_footprint:.0f} mm base) in the {context.build_axis} orientation — "
                f"{stability_note}."
            ),
            recommendation=(
                f"Reorient to lower the print height, or print with a brim/raft and add a "
                f"{fillet_mm:.0f} mm fillet at the wall-to-base transition to spread the load."
            ),
            index=0,
            measured=round(ratio, 2),
            threshold=major_above if severity == Severity.major else minor_above,
            unit="ratio",
        )

        return self.failed(
            summary=f"Tall, thin part: {ratio:.1f}:1 height-to-footprint ratio.",
            findings=[finding],
            recommendations=[
                "Lay the part down if any orientation gives a wider base.",
                f"Add a fillet of at least {fillet_mm:.0f} mm where walls meet the base.",
                "Use a brim or raft to increase bed adhesion.",
            ],
            thresholds_used=thresholds_used,
            assumptions=assumptions,
        )
