"""P1 · Overhang Angle (Type 1 — process-dependent, orientation-relative)."""

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


class OverhangAngleRule(RuleEvaluator):
    """Faces past the printable angle have nothing to bond to — they sag, curl,
    or need support material.

    The 45°-from-vertical rule is the FDM/SLA baseline. Powder-bed processes
    (SLS/MJF) need no supports at all — unfused powder holds overhangs up — so
    the rule suppresses itself there rather than penalising the part.

    Measured against the chosen build orientation, never the as-modelled pose.
    See ``EvaluationContext.overhang_angle_from_vertical`` for the datum
    conversion from the geometry engine's normal-to-axis angle.
    """

    rule_id = "P1"
    name = "Overhang Angle"
    process = ProcessType.printing
    sub_score = SubScore.geometry
    threshold_type = ThresholdType.material_process
    what_it_flags = (
        "Down-facing surfaces steeper than the process limit have nothing beneath them, so they "
        "sag or curl unless support material is printed under them."
    )

    def _evaluate(self, context: EvaluationContext) -> RuleResult:
        process_spec = context.printing_process
        limit = process_spec.overhang_limit_deg

        if limit is None or not process_spec.needs_supports:
            return self.suppressed(
                f"{process_spec.display_name} is a powder-bed process: unfused powder supports "
                f"overhangs, so overhang angle does not constrain this part.",
                summary=f"Overhang angle not applicable to {process_spec.display_name}.",
                assumptions=[context.printing_process_assumption],
            )

        orientation = context.build_orientation()
        if orientation is None or not orientation.face_angles:
            return self.not_assessed(
                "The geometry engine reported no per-face angles for the "
                f"{context.build_axis} build orientation.",
                missing_inputs=["print_orientations.face_angles"],
                assumptions=[context.build_axis_assumption],
            )

        minor_fraction = float(self.thresholds.get("overhang_area_fraction_minor", 0.05))
        major_fraction = float(self.thresholds.get("overhang_area_fraction_major", 0.20))
        severe_margin = float(self.thresholds.get("severe_margin_deg", 25.0))

        total_area = context.total_surface_area or 0.0
        has_face_areas = bool(context.geometry.faces)

        offending: List[tuple[int, float, float]] = []   # (face_id, angle, area)
        offending_area = 0.0
        for raw_face_id, normal_angle in orientation.face_angles.items():
            overhang = context.overhang_angle_from_vertical(float(normal_angle))
            if overhang <= limit:
                continue
            face_id = int(raw_face_id)
            face = context.face(face_id)
            area = float(face.area) if face is not None else 0.0
            offending.append((face_id, overhang, area))
            offending_area += area

        # STL parts carry no faces[] array, so per-face area is unavailable —
        # fall back to the overhang area ratio the geometry engine reports.
        if not has_face_areas and orientation.overhang_ratio is not None:
            area_fraction = float(orientation.overhang_ratio)
            offending_area = float(orientation.overhang_area_mm2 or 0.0)
        else:
            area_fraction = offending_area / total_area if total_area else 0.0

        assumptions = [a for a in (
            context.printing_process_assumption,
            context.build_axis_assumption,
        ) if a]

        thresholds_used = {
            "printing_process": process_spec.key,
            "overhang_limit_deg": limit,
            "build_orientation": context.build_axis,
            "overhang_faces": len(offending),
            "overhang_area_mm2": round(offending_area, 2),
            "overhang_area_fraction": round(area_fraction, 4),
            "minor_fraction": minor_fraction,
            "major_fraction": major_fraction,
        }

        if not offending:
            return self.passed(
                summary=(
                    f"No faces exceed the {limit:.0f}° overhang limit for "
                    f"{process_spec.display_name} in the {context.build_axis} orientation."
                ),
                thresholds_used=thresholds_used,
                assumptions=assumptions,
            )

        steepest = max(offending, key=lambda item: item[1])
        severe = [item for item in offending if item[1] > limit + severe_margin]

        # Spec P1 maps any face past the limit to Major. `minor_fraction`
        # defaults to 0, so nothing is downgraded; raising it in thresholds.yaml
        # introduces a Minor band for parts with only a sliver of overhang.
        if area_fraction < minor_fraction and not severe:
            severity = Severity.minor
        else:
            severity = Severity.major

        findings: List[Finding] = []
        index = 0
        findings.append(self.finding(
            severity=severity,
            message=(
                f"{len(offending)} face(s) exceed the {limit:.0f}° overhang limit for "
                f"{process_spec.display_name} in the {context.build_axis} orientation "
                f"({area_fraction * 100:.1f}% of surface area; steepest {steepest[1]:.0f}° "
                f"on face {steepest[0]})."
            ),
            recommendation=(
                "Add support material for these faces, reorient the part, or chamfer the "
                f"overhangs back to {limit:.0f}° or less from vertical."
            ),
            index=index,
            measured=round(steepest[1], 1),
            threshold=limit,
            unit="deg",
            geometry_ref=self.face_ref(context, [item[0] for item in offending[:50]]),
        ))
        index += 1

        # Call out the worst individual faces so the viewer can highlight them.
        for face_id, angle, _area in sorted(severe, key=lambda item: -item[1])[
            : max(0, self.max_findings - 1)
        ]:
            findings.append(self.finding(
                severity=Severity.major,
                message=(
                    f"Face {face_id} overhangs at {angle:.0f}° from vertical, "
                    f"{angle - limit:.0f}° past the {limit:.0f}° limit — high sag/tear risk."
                ),
                recommendation=(
                    "Support this face or reorient the part; at this angle the extrusion has "
                    "almost nothing to bond to."
                ),
                index=index,
                measured=round(angle, 1),
                threshold=limit,
                unit="deg",
                geometry_ref=self.face_ref(context, [face_id]),
            ))
            index += 1

        return self.failed(
            summary=(
                f"{len(offending)} overhanging face(s) past {limit:.0f}° "
                f"({area_fraction * 100:.1f}% of surface area) in the {context.build_axis} "
                f"orientation."
            ),
            findings=self.cap_findings(findings),
            recommendations=[
                f"Keep down-facing surfaces within {limit:.0f}° of vertical where possible.",
                "Reorienting the part is usually cheaper than adding support material.",
                "A powder-bed process (SLS/MJF) removes this constraint entirely.",
            ],
            thresholds_used=thresholds_used,
            assumptions=assumptions,
        )
