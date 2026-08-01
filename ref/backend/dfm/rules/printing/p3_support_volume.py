"""P3 · Support Volume Estimate (Type 1/2 blend — orientation-driven)."""

from __future__ import annotations

from typing import List, Optional

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


class SupportVolumeRule(RuleEvaluator):
    """Support material is wasted plastic plus post-processing labour, and the
    surfaces it touches come out rougher. It is the primary cost driver for
    printing and the main lever the orientation search minimises.

    Derived from P1, in the chosen orientation. Severity is driven by the
    overhang *area ratio* the geometry engine already reports, because that is
    a measured value. The support *volume* is only ever an estimate:

    * if the geometry engine supplies ``support_volume_mm3`` for the
      orientation, that number is used and labelled as measured;
    * otherwise it is estimated as ``overhang_area x mean_drop_fraction x part
      height`` and labelled as an estimate. The estimate can raise a Minor to a
      Major but never fires the rule on its own — a cost proxy should not
      invent a defect.
    """

    rule_id = "P3"
    name = "Support Volume Estimate"
    process = ProcessType.printing
    sub_score = SubScore.cost_risk
    threshold_type = ThresholdType.geometric_ratio
    what_it_flags = (
        "Large support volumes mean wasted material, long post-processing and rough downward "
        "surfaces — the dominant cost driver in printing."
    )

    def _evaluate(self, context: EvaluationContext) -> RuleResult:
        process_spec = context.printing_process
        if not process_spec.needs_supports:
            return self.suppressed(
                f"{process_spec.display_name} prints without support structures — unfused powder "
                f"holds the part up, so there is no support volume to cost.",
                summary=f"Support volume not applicable to {process_spec.display_name}.",
                assumptions=[context.printing_process_assumption],
            )

        orientation = context.build_orientation()
        if orientation is None or orientation.overhang_ratio is None:
            return self.not_assessed(
                "The geometry engine reported no overhang area for the "
                f"{context.build_axis} build orientation, so support volume cannot be estimated.",
                missing_inputs=["print_orientations.overhang_ratio"],
                assumptions=[context.build_axis_assumption],
            )

        ratio_minor = float(self.thresholds.get("overhang_ratio_minor", 0.15))
        ratio_major = float(self.thresholds.get("overhang_ratio_major", 0.35))
        drop_fraction = float(self.thresholds.get("mean_drop_fraction", 0.5))
        volume_major = float(self.thresholds.get("support_volume_ratio_major", 0.30))

        overhang_ratio = float(orientation.overhang_ratio)
        overhang_area = float(orientation.overhang_area_mm2 or 0.0)

        support_volume, volume_is_measured = self._support_volume(
            context, orientation, overhang_area, drop_fraction
        )
        part_volume = context.geometry.volume_mm3
        volume_ratio: Optional[float] = None
        if support_volume is not None and part_volume and part_volume > 0:
            volume_ratio = support_volume / part_volume

        assumptions = [a for a in (
            context.printing_process_assumption,
            context.build_axis_assumption,
        ) if a]
        if support_volume is not None and not volume_is_measured:
            assumptions.append(
                f"Support volume is an estimate: overhang area x {drop_fraction:.0%} of part "
                f"height. The geometry engine does not yet integrate a true support volume."
            )

        thresholds_used = {
            "build_orientation": context.build_axis,
            "overhang_ratio": round(overhang_ratio, 4),
            "overhang_area_mm2": round(overhang_area, 2),
            "overhang_ratio_minor": ratio_minor,
            "overhang_ratio_major": ratio_major,
            "support_volume_mm3": (
                round(support_volume, 1) if support_volume is not None else None
            ),
            "support_volume_is_estimate": not volume_is_measured,
            "support_volume_ratio": (
                round(volume_ratio, 4) if volume_ratio is not None else None
            ),
        }

        # Severity from the measured overhang ratio.
        if overhang_ratio <= ratio_minor:
            severity: Optional[Severity] = None
        elif overhang_ratio <= ratio_major:
            severity = Severity.minor
        else:
            severity = Severity.major

        # A *measured* support volume can escalate a Minor to a Major, but never
        # create a finding on its own. The fallback estimate never escalates:
        # it assumes every overhang drops half the part height, which is far too
        # crude to move a severity, so it is reported and nothing more.
        escalated = False
        if (
            severity == Severity.minor
            and volume_is_measured
            and volume_ratio is not None
            and volume_ratio > volume_major
        ):
            severity = Severity.major
            escalated = True

        if severity is None:
            return self.passed(
                summary=(
                    f"Support demand is modest: {overhang_ratio * 100:.1f}% of the surface "
                    f"overhangs in the {context.build_axis} orientation."
                ),
                thresholds_used=thresholds_used,
                assumptions=assumptions,
            )

        volume_phrase = ""
        if support_volume is not None:
            label = "estimated" if not volume_is_measured else "computed"
            volume_phrase = f" — {label} support volume {support_volume:,.0f} mm³"
            if volume_ratio is not None:
                volume_phrase += f" ({volume_ratio * 100:.0f}% of part volume)"

        best_alternative = self._better_orientation(context, overhang_ratio)

        findings: List[Finding] = [self.finding(
            severity=severity,
            message=(
                f"{overhang_ratio * 100:.1f}% of the surface needs support in the "
                f"{context.build_axis} orientation{volume_phrase}."
                + (" The support volume estimate raised this to Major." if escalated else "")
            ),
            recommendation=(
                (
                    f"Reorienting to {best_alternative[0]} drops the supported area to "
                    f"{best_alternative[1] * 100:.1f}%."
                    if best_alternative else
                    "Reorient the part or redesign the steepest overhangs to reduce support."
                )
                + " Expect rougher finish and manual clean-up wherever support touches the part."
            ),
            index=0,
            measured=round(overhang_ratio, 4),
            threshold=ratio_major if severity == Severity.major else ratio_minor,
            unit="fraction of surface area",
        )]

        return self.failed(
            summary=(
                f"Support material is a significant cost on this part "
                f"({overhang_ratio * 100:.1f}% of surface area overhangs)."
            ),
            findings=findings,
            recommendations=[
                "Reorient to minimise supported area — it is the cheapest lever available.",
                "Chamfer or fillet steep overhangs so they self-support.",
                "A powder-bed process (SLS/MJF) removes support cost entirely.",
            ],
            thresholds_used=thresholds_used,
            assumptions=assumptions,
        )

    # ------------------------------------------------------------------

    def _support_volume(
        self, context, orientation, overhang_area: float, drop_fraction: float
    ) -> tuple[Optional[float], bool]:
        """(volume_mm3, is_measured). Prefers a geometry-supplied volume."""
        if orientation.support_volume_mm3 is not None:
            return float(orientation.support_volume_mm3), True
        extents = context.extents_in_build_frame()
        if extents is None or overhang_area <= 0:
            return None, False
        height = extents[2]
        return overhang_area * drop_fraction * height, False

    def _better_orientation(self, context, current_ratio: float):
        """The candidate orientation with the least overhang, when it beats the
        one in use — read straight from the geometry engine's analysis."""
        analysis = context.geometry.print_orientations
        if analysis is None:
            return None
        candidates = [
            (o.axis_label, float(o.overhang_ratio))
            for o in analysis.orientations
            if o.overhang_ratio is not None and o.axis_label != context.build_axis
        ]
        if not candidates:
            return None
        best = min(candidates, key=lambda item: item[1])
        return best if best[1] < current_ratio * 0.9 else None
