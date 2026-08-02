"""M3 · Draft Angle on Vertical Faces (Type 1 — surface-finish driven)."""

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


class DraftAngleRule(RuleEvaluator):
    """Insufficient draft means the part won't eject cleanly: drag marks,
    ejector-pin damage, stuck parts.

    The honest MVP problem the spec calls out: the *measurement* is geometric
    but the *pass threshold* is contextual — it is driven by surface finish and
    cavity depth, and neither is in the CAD file. So this rule reads the finish
    from user input, falls back to the stated default, and always says which
    finish the verdict assumed.

    Datum: the geometry engine reports the angle between each face normal and
    the pull axis. A perfectly vertical wall reads 90° and has 0° of draft, so
    draft = ``|normal_angle - 90|``. Faces more than
    ``vertical_face_window_deg`` away from vertical are top/bottom faces that
    need no draft and are skipped.
    """

    rule_id = "M3"
    name = "Draft Angle on Vertical Faces"
    process = ProcessType.injection_molding
    sub_score = SubScore.geometry
    threshold_type = ThresholdType.material_process
    what_it_flags = (
        "Vertical walls without enough taper drag against the mould on ejection, scarring the "
        "part and damaging ejector pins."
    )

    def _evaluate(self, context: EvaluationContext) -> RuleResult:
        orientation = context.parting_orientation()
        if orientation is None or not orientation.face_angles:
            return self.not_assessed(
                "The geometry engine reported no per-face angles for the "
                f"{context.parting_axis} pull direction.",
                missing_inputs=["print_orientations.face_angles"],
            )

        finish_table = self.thresholds.get("finish_minimum_deg", {}) or {}
        minimum_deg = float(finish_table.get(context.surface_finish, 1.0))
        near_certain = float(self.thresholds.get("near_certain_deg", 0.5))
        window = float(self.thresholds.get("vertical_face_window_deg", 20.0))
        min_area_fraction = float(self.thresholds.get("min_face_area_fraction", 0.001))

        assumptions: List[str] = []
        if context.surface_finish_assumption:
            assumptions.append(context.surface_finish_assumption)
        if context.parting_axis_assumption:
            assumptions.append(context.parting_axis_assumption)

        # Deep cavities need more draft, but depth is user-supplied context.
        deep_depth = float(self.thresholds.get("deep_cavity_depth_mm", 75.0))
        deep_minimum = float(self.thresholds.get("deep_cavity_minimum_deg", 2.0))
        cavity_depth = context.inputs.max_cavity_depth_mm
        if cavity_depth is None:
            cavity_depth = max(
                (c.depth for c in context.geometry.cavities if c.depth), default=None
            )
        if cavity_depth is not None and cavity_depth > deep_depth:
            if deep_minimum > minimum_deg:
                assumptions.append(
                    f"A cavity {cavity_depth:.0f} mm deep was detected (over {deep_depth:.0f} mm), "
                    f"so the minimum draft was raised from {minimum_deg:.1f}° to {deep_minimum:.1f}°."
                )
                minimum_deg = deep_minimum

        total_area = context.total_surface_area or 0.0
        area_floor = total_area * min_area_fraction if total_area else 0.0

        findings: List[Finding] = []
        index = 0
        vertical_faces = 0
        insufficient_area = 0.0

        for raw_face_id, normal_angle in orientation.face_angles.items():
            face_id = int(raw_face_id)
            face = context.face(face_id)
            area = face.area if face is not None else 0.0
            if area and area < area_floor:
                continue

            draft = abs(float(normal_angle) - 90.0)
            if draft > window:
                continue  # a top/bottom face: no draft required
            vertical_faces += 1

            if draft >= minimum_deg:
                continue

            insufficient_area += area
            # < 0.5° is a near-certain problem whatever the finish; between
            # 0.5° and the finish minimum the severity follows the assumed
            # finish (Major when the finish was supplied, Minor when guessed).
            if draft < near_certain:
                severity = Severity.major
                note = "near-certain ejection problem at any surface finish"
            elif context.inputs.surface_finish:
                severity = Severity.major
                note = f"below the {minimum_deg:.1f}° needed for a {context.surface_finish} finish"
            else:
                severity = Severity.minor
                note = (
                    f"below the {minimum_deg:.1f}° assumed for a "
                    f"{context.surface_finish.replace('_', '-')} finish"
                )

            findings.append(self.finding(
                severity=severity,
                message=(
                    f"Face {face_id} has {draft:.2f}° of draft — {note}."
                ),
                recommendation=(
                    f"Add at least {minimum_deg:.1f}° of draft per side to this face, measured "
                    f"from the {context.parting_axis} pull direction."
                ),
                index=index,
                measured=round(draft, 3),
                threshold=minimum_deg,
                unit="deg",
                geometry_ref=self.face_ref(context, [face_id]),
            ))
            index += 1

        thresholds_used = {
            "surface_finish": context.surface_finish,
            "minimum_draft_deg": minimum_deg,
            "near_certain_deg": near_certain,
            "vertical_face_window_deg": window,
            "parting_direction": context.parting_axis,
            "vertical_faces_checked": vertical_faces,
            "faces_below_minimum": len(findings),
        }

        if vertical_faces == 0:
            return self.not_assessed(
                "No vertical-ish faces were found for the assumed pull direction, so there is "
                "nothing to draft.",
                assumptions=assumptions,
                summary="No draftable vertical faces found.",
            )

        if not findings:
            return self.passed(
                summary=(
                    f"All {vertical_faces} vertical face(s) carry at least {minimum_deg:.1f}° of "
                    f"draft for a {context.surface_finish.replace('_', '-')} finish."
                ),
                thresholds_used=thresholds_used,
                assumptions=assumptions,
            )

        return self.failed(
            summary=(
                f"{len(findings)} of {vertical_faces} vertical face(s) have less than "
                f"{minimum_deg:.1f}° of draft."
            ),
            findings=self.cap_findings(findings),
            recommendations=[
                f"Apply at least {minimum_deg:.1f}° of draft per side to vertical walls.",
                "Confirm the surface finish — a textured finish needs 1.5–5° rather than 1°.",
            ],
            thresholds_used=thresholds_used,
            assumptions=assumptions,
        )
