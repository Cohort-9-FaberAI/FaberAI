"""P2 · Minimum Feature Size / Thin Walls (Type 1 — process lookup)."""

from __future__ import annotations

import math
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


class MinimumFeatureSizeRule(RuleEvaluator):
    """Features below the printable resolution won't resolve, or will resolve
    too weak to survive handling.

    Process minimums (FDM 1.0–1.2 mm, SLA 0.4–0.6 mm, SLS/MJF 0.7–1.0 mm) are
    *minimums*, not targets — the safe design target is 1.5x the minimum. On
    FDM anything below one nozzle perimeter simply cannot be extruded, which is
    a harder floor than the process minimum and is treated as such.

    A single sub-minimum sample is ray-cast noise rather than a thin wall, so
    the rule needs a meaningful share of samples below the floor before it
    fires.
    """

    rule_id = "P2"
    name = "Minimum Feature Size / Thin Walls"
    process = ProcessType.printing
    sub_score = SubScore.geometry
    threshold_type = ThresholdType.material_process
    what_it_flags = (
        "Walls and pins thinner than the process can resolve either fail to print at all or come "
        "out too fragile to handle."
    )

    def _evaluate(self, context: EvaluationContext) -> RuleResult:
        wall_field = context.geometry.wall_field()
        if not wall_field:
            return self.not_assessed(
                "The geometry engine produced no usable wall thickness samples.",
                missing_inputs=["wall_samples", "wall_thickness_stats"],
                assumptions=[context.printing_process_assumption],
            )

        process_spec = context.printing_process
        min_wall = float(process_spec.min_wall_mm or 0.0)
        if min_wall <= 0:
            return self.not_assessed(
                f"No minimum wall thickness is configured for {process_spec.display_name}.",
                missing_inputs=[f"printing_processes.{process_spec.key}.min_wall_mm"],
            )

        absolute_floor = float(process_spec.absolute_min_wall_mm or 0.0)
        safe_wall = min_wall * float(process_spec.safe_wall_multiplier or 1.5)
        below_fraction = float(self.thresholds.get("below_min_fraction", 0.02))
        min_count = int(self.thresholds.get("below_min_min_count", 3))

        assumptions = [a for a in (context.printing_process_assumption,) if a]

        below_absolute = [t for t in wall_field if absolute_floor and t < absolute_floor]
        below_min = [t for t in wall_field if t < min_wall]
        fragile = [t for t in wall_field if min_wall <= t < safe_wall]

        sample_count = len(wall_field)
        # The fraction sets the bar, capped by the absolute count so the bar can
        # never exceed a few samples: a densely sampled part needs several hits
        # before firing, while a coarsely sampled one is not made immune by
        # having too few samples to reach the absolute floor.
        required_hits = max(1, min(min_count, math.ceil(sample_count * below_fraction)))
        measured_min = min(wall_field)

        thresholds_used = {
            "printing_process": process_spec.key,
            "min_wall_mm": min_wall,
            "absolute_min_wall_mm": absolute_floor or None,
            "safe_wall_mm": round(safe_wall, 3),
            "measured_min_wall_mm": round(measured_min, 3),
            "samples": sample_count,
            "samples_below_min": len(below_min),
            "samples_in_fragile_band": len(fragile),
            "noise_floor_samples": required_hits,
            "min_pin_diameter_mm": process_spec.min_pin_diameter_mm,
        }

        findings: List[Finding] = []
        index = 0

        if len(below_min) >= required_hits:
            # Spec P2: below the process minimum the feature will not resolve —
            # that is a Blocker. Being below the single-perimeter extrusion
            # floor as well is called out in the message, because no print
            # setting can recover those walls.
            blocking = len(below_absolute) >= required_hits
            findings.append(self.finding(
                severity=Severity.blocker,
                message=(
                    f"{len(below_min)} of {sample_count} wall samples are below the "
                    f"{min_wall:.2f} mm minimum for {process_spec.display_name} "
                    f"(thinnest {measured_min:.2f} mm)"
                    + (
                        f" — {len(below_absolute)} are below the {absolute_floor:.2f} mm "
                        f"extrusion floor and cannot print at all."
                        if blocking else "."
                    )
                ),
                recommendation=(
                    f"Thicken these walls to at least {safe_wall:.2f} mm "
                    f"(1.5x the {min_wall:.2f} mm process minimum)."
                    + ("" if not blocking else
                       f" Below {absolute_floor:.2f} mm the printer cannot lay a single "
                       f"perimeter, so no print setting will recover the feature.")
                ),
                index=index,
                measured=round(measured_min, 3),
                threshold=min_wall,
                unit="mm",
                geometry_ref=self._thin_wall_ref(context, min_wall),
            ))
            index += 1

        elif len(fragile) >= required_hits:
            findings.append(self.finding(
                severity=Severity.major,
                message=(
                    f"{len(fragile)} of {sample_count} wall samples sit between the "
                    f"{min_wall:.2f} mm minimum and the {safe_wall:.2f} mm safe target for "
                    f"{process_spec.display_name} — printable but fragile."
                ),
                recommendation=(
                    f"Design to {safe_wall:.2f} mm (1.5x the process minimum) so walls survive "
                    f"support removal and handling."
                ),
                index=index,
                measured=round(measured_min, 3),
                threshold=round(safe_wall, 3),
                unit="mm",
                geometry_ref=self._thin_wall_ref(context, safe_wall),
            ))
            index += 1

        # Positive features: pins need enough width for two full perimeters.
        pin_minimum = process_spec.min_pin_diameter_mm
        if pin_minimum and context.geometry.bosses:
            thin_pins = [
                boss for boss in context.geometry.bosses
                if boss.outer_diameter and 0 < boss.outer_diameter < pin_minimum
            ]
            for boss in thin_pins[: max(0, self.max_findings - index)]:
                findings.append(self.finding(
                    severity=Severity.major,
                    message=(
                        f"Pin/boss {boss.id} is ø{boss.outer_diameter:.2f} mm, below the "
                        f"ø{pin_minimum:.2f} mm minimum for {process_spec.display_name}."
                    ),
                    recommendation=(
                        f"Increase the diameter to at least ø{pin_minimum:.2f} mm so the printer "
                        f"can lay two full perimeters."
                    ),
                    index=index,
                    measured=round(boss.outer_diameter, 3),
                    threshold=pin_minimum,
                    unit="mm",
                    geometry_ref=self.feature_ref("boss", [boss.id], boss.center, boss.faces),
                ))
                index += 1

        if not findings:
            return self.passed(
                summary=(
                    f"Thinnest wall is {measured_min:.2f} mm, at or above the {min_wall:.2f} mm "
                    f"minimum for {process_spec.display_name}."
                ),
                thresholds_used=thresholds_used,
                assumptions=assumptions,
            )

        return self.failed(
            summary=(
                f"Features below the {min_wall:.2f} mm {process_spec.display_name} minimum "
                f"(thinnest {measured_min:.2f} mm)."
            ),
            findings=self.cap_findings(findings),
            recommendations=[
                f"Target {safe_wall:.2f} mm walls — 1.5x the process minimum.",
                "A finer process (SLA) resolves thinner features if the geometry cannot change.",
            ],
            thresholds_used=thresholds_used,
            assumptions=assumptions,
        )

    def _thin_wall_ref(self, context: EvaluationContext, floor: float):
        """Point the viewer at the faces carrying the thinnest samples."""
        face_ids = [
            face_id
            for face_id, thickness in context.thickness_by_face().items()
            if thickness < floor
        ]
        if not face_ids:
            return None
        return self.face_ref(context, face_ids[:50])
