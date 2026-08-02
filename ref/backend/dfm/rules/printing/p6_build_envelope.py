"""P6 · Bounding Box vs Build Envelope (Type 1 — printer-dependent)."""

from __future__ import annotations

from typing import List

from ...base import RuleEvaluator
from ...context import EvaluationContext
from ...models import (
    ProcessType,
    RuleResult,
    Severity,
    SubScore,
    ThresholdType,
)

_SEVERITY_BY_NAME = {
    "blocker": Severity.blocker,
    "major": Severity.major,
    "minor": Severity.minor,
}


class BuildEnvelopeRule(RuleEvaluator):
    """Does the part fit the build volume?

    Orientation-relative, and the spec is specific about what that means: only
    hard-fail when the part fits **no** candidate orientation. Fitting only in
    an orientation other than the recommended one is a trade-off, not a
    failure — the user loses the low-support orientation to gain the fit.

    The fit test sorts both the part extents and the envelope and compares them
    term by term, which is exactly "is there some axis-aligned orientation in
    which this fits".
    """

    rule_id = "P6"
    name = "Bounding Box vs Build Envelope"
    process = ProcessType.printing
    sub_score = SubScore.geometry
    threshold_type = ThresholdType.material_process
    what_it_flags = (
        "A part larger than the build volume cannot be printed in one piece, whatever the "
        "orientation."
    )

    def _evaluate(self, context: EvaluationContext) -> RuleResult:
        extents = context.geometry.bbox_extents()
        if extents is None:
            return self.not_assessed(
                "The geometry engine reported no usable bounding box.",
                missing_inputs=["bounding_box"],
            )

        envelope = context.build_envelope_mm
        if not envelope:
            return self.not_assessed(
                "No build envelope was supplied and no default is configured.",
                missing_inputs=["inputs.build_envelope_mm", "defaults.build_envelope_mm"],
            )

        clearance = float(self.thresholds.get("clearance_mm", 5.0))
        usable = [max(0.0, dimension - clearance) for dimension in envelope]

        assumptions: List[str] = [
            a for a in (context.build_envelope_assumption, context.build_axis_assumption) if a
        ]

        # Fits in *some* axis-aligned orientation?
        sorted_part = sorted(extents)
        sorted_usable = sorted(usable)
        fits_somehow = all(p <= u for p, u in zip(sorted_part, sorted_usable))

        # Fits in the orientation the printing checks actually assume?
        build_extents = context.extents_in_build_frame()
        fits_as_oriented = False
        if build_extents is not None:
            # The build-frame tuple is (footprint_a, footprint_b, height); the
            # envelope is (x, y, z) with z the vertical axis.
            footprint = sorted(build_extents[:2])
            bed = sorted(usable[:2])
            fits_as_oriented = (
                footprint[0] <= bed[0]
                and footprint[1] <= bed[1]
                and build_extents[2] <= usable[2]
            )

        printer_label = context.inputs.printer_name or "the build envelope"
        thresholds_used = {
            "part_extents_mm": [round(e, 2) for e in extents],
            "envelope_mm": [round(e, 2) for e in envelope],
            "clearance_mm": clearance,
            "usable_envelope_mm": [round(u, 2) for u in usable],
            "fits_in_some_orientation": fits_somehow,
            "fits_in_build_orientation": fits_as_oriented,
            "build_orientation": context.build_axis,
        }

        if not fits_somehow:
            oversize = [
                f"{axis}: {part:.0f} mm vs {limit:.0f} mm usable"
                for axis, part, limit in zip("XYZ", sorted_part, sorted_usable)
                if part > limit
            ]
            finding = self.finding(
                severity=Severity.blocker,
                message=(
                    f"Part measures {extents[0]:.0f} x {extents[1]:.0f} x {extents[2]:.0f} mm and "
                    f"does not fit {printer_label} "
                    f"({envelope[0]:.0f} x {envelope[1]:.0f} x {envelope[2]:.0f} mm, "
                    f"{clearance:.0f} mm clearance) in any orientation — "
                    + "; ".join(oversize) + "."
                ),
                recommendation=(
                    "Split the part for assembly, scale it down, or use a printer with a larger "
                    "build volume."
                ),
                index=0,
                measured=round(max(sorted_part), 2),
                threshold=round(max(sorted_usable), 2),
                unit="mm",
            )
            return self.failed(
                summary=f"Part does not fit {printer_label} in any orientation.",
                findings=[finding],
                recommendations=[
                    "Split the part into printable sections and bond or fasten them.",
                    "Confirm the printer — a larger machine may already be available.",
                ],
                thresholds_used=thresholds_used,
                assumptions=assumptions,
            )

        if fits_as_oriented:
            return self.passed(
                summary=(
                    f"Part fits {printer_label} in the {context.build_axis} orientation "
                    f"({extents[0]:.0f} x {extents[1]:.0f} x {extents[2]:.0f} mm inside "
                    f"{envelope[0]:.0f} x {envelope[1]:.0f} x {envelope[2]:.0f} mm)."
                ),
                thresholds_used=thresholds_used,
                assumptions=assumptions,
            )

        severity = _SEVERITY_BY_NAME.get(
            str(self.thresholds.get("awkward_orientation_severity", "minor")).lower(),
            Severity.minor,
        )
        finding = self.finding(
            severity=severity,
            message=(
                f"Part fits {printer_label}, but not in the {context.build_axis} orientation the "
                f"other printing checks assume — it has to be laid differently to fit."
            ),
            recommendation=(
                "Re-run the analysis with the orientation that fits, or accept the extra support "
                "material the fitting orientation costs."
            ),
            index=0,
            measured=round(max(extents), 2),
            threshold=round(max(usable), 2),
            unit="mm",
        )
        return self.failed(
            summary=f"Part fits {printer_label} only in a different orientation.",
            findings=[finding],
            recommendations=[
                "Choose between the low-support orientation and the one that fits the bed.",
            ],
            thresholds_used=thresholds_used,
            assumptions=assumptions,
        )
