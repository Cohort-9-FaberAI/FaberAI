"""M1 · Minimum / Maximum Wall Thickness (Type 1 — material lookup)."""

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


class WallThicknessRule(RuleEvaluator):
    """Walls too thin won't fill (short shots); walls too thick sink, trap
    voids and extend cycle time.

    Three separate tests, because "too thin" is not one question:

    1. **Below the fill floor** — under the material minimum (or the generic
       0.8 mm floor when no material was supplied) → Blocker.
    2. **Risky-thin / over-max** — inside the short-shot-prone band just above
       the minimum, or above the material maximum → Major.
    3. **Neighbourhood** — the spec's "thin is not judged in isolation"
       subtlety: no wall may be less than ~50% of the walls adjacent to it or
       flow stalls. A 1.0 mm wall is fine next to 1.2 mm and a problem next to
       4 mm, so this runs off the face graph, not the global minimum.
    """

    rule_id = "M1"
    name = "Minimum / Maximum Wall Thickness"
    process = ProcessType.injection_molding
    sub_score = SubScore.geometry
    threshold_type = ThresholdType.material_process
    what_it_flags = (
        "Walls below the material's fill floor will short-shot; walls above its maximum "
        "sink, trap voids and extend cycle time."
    )

    def _evaluate(self, context: EvaluationContext) -> RuleResult:
        wall_field = context.geometry.wall_field()
        if not wall_field:
            return self.not_assessed(
                "The geometry engine produced no usable wall thickness samples.",
                missing_inputs=["wall_samples", "wall_thickness_stats"],
            )

        material = context.material
        assumptions: List[str] = []

        if material is not None and material.wall_min_mm is not None:
            min_wall = float(material.wall_min_mm)
            max_wall = float(material.wall_max_mm or self.thresholds.get("generic_max_wall_mm", 5.0))
            material_label = material.display_name
        else:
            min_wall = float(self.thresholds.get("generic_min_wall_mm", 0.8))
            max_wall = float(self.thresholds.get("generic_max_wall_mm", 5.0))
            material_label = "generic engineering thermoplastic"
            assumptions.append(context.material_assumption)

        risky_multiplier = float(self.thresholds.get("risky_band_multiplier", 1.25))
        risky_ceiling = min_wall * risky_multiplier
        neighbour_ratio = float(self.thresholds.get("neighbour_ratio_min", 0.5))
        neighbour_floor = float(self.thresholds.get("neighbour_min_thickness_mm", 0.5))

        thresholds_used = {
            "material": material_label,
            "min_wall_mm": min_wall,
            "max_wall_mm": max_wall,
            "risky_band_ceiling_mm": round(risky_ceiling, 3),
            "neighbour_ratio_min": neighbour_ratio,
        }

        findings: List[Finding] = []
        measured_min = min(wall_field)
        measured_max = max(wall_field)

        # --- 1 & 2: absolute thin / thick, reported per offending face ------
        below_floor_faces: dict[int, float] = {}
        risky_faces: dict[int, float] = {}
        over_max_faces: dict[int, float] = {}

        for face_id, thickness in context.thickness_by_face().items():
            if thickness < min_wall:
                below_floor_faces[face_id] = thickness
            elif thickness < risky_ceiling:
                risky_faces[face_id] = thickness
            elif thickness > max_wall:
                over_max_faces[face_id] = thickness

        # STL parts have no face ids on their samples; fall back to a single
        # part-level finding built from the thickness field.
        has_face_detail = bool(context.thickness_by_face())

        index = 0
        if has_face_detail:
            for face_id, thickness in sorted(below_floor_faces.items(), key=lambda kv: kv[1]):
                findings.append(self.finding(
                    severity=Severity.blocker,
                    message=(
                        f"Wall on face {face_id} measures {thickness:.2f} mm, below the "
                        f"{min_wall:.2f} mm fill floor for {material_label}."
                    ),
                    recommendation=(
                        f"Thicken this wall to at least {min_wall:.2f} mm "
                        f"(target {risky_ceiling:.2f} mm) or the cavity will not fill."
                    ),
                    index=index, measured=round(thickness, 3), threshold=min_wall, unit="mm",
                    geometry_ref=self.face_ref(context, [face_id]),
                ))
                index += 1
            for face_id, thickness in sorted(risky_faces.items(), key=lambda kv: kv[1]):
                findings.append(self.finding(
                    severity=Severity.major,
                    message=(
                        f"Wall on face {face_id} measures {thickness:.2f} mm — mouldable but "
                        f"short-shot prone for {material_label} (minimum {min_wall:.2f} mm)."
                    ),
                    recommendation=(
                        f"Increase to at least {risky_ceiling:.2f} mm, or confirm a short flow "
                        f"path and gate location with the moulder."
                    ),
                    index=index, measured=round(thickness, 3), threshold=risky_ceiling, unit="mm",
                    geometry_ref=self.face_ref(context, [face_id]),
                ))
                index += 1
            for face_id, thickness in sorted(over_max_faces.items(), key=lambda kv: -kv[1]):
                findings.append(self.finding(
                    severity=Severity.major,
                    message=(
                        f"Wall on face {face_id} measures {thickness:.2f} mm, above the "
                        f"{max_wall:.2f} mm maximum for {material_label}."
                    ),
                    recommendation=(
                        "Core out the thick section to keep the wall uniform — thick masses "
                        "sink, trap voids and lengthen cycle time."
                    ),
                    index=index, measured=round(thickness, 3), threshold=max_wall, unit="mm",
                    geometry_ref=self.face_ref(context, [face_id]),
                ))
                index += 1
        else:
            if measured_min < min_wall:
                findings.append(self.finding(
                    severity=Severity.blocker,
                    message=(
                        f"Thinnest wall measures {measured_min:.2f} mm, below the "
                        f"{min_wall:.2f} mm fill floor for {material_label}."
                    ),
                    recommendation=f"Thicken the thinnest walls to at least {min_wall:.2f} mm.",
                    index=index, measured=round(measured_min, 3), threshold=min_wall, unit="mm",
                ))
                index += 1
            elif measured_min < risky_ceiling:
                findings.append(self.finding(
                    severity=Severity.major,
                    message=(
                        f"Thinnest wall measures {measured_min:.2f} mm — mouldable but "
                        f"short-shot prone for {material_label}."
                    ),
                    recommendation=f"Increase thin walls to at least {risky_ceiling:.2f} mm.",
                    index=index, measured=round(measured_min, 3), threshold=risky_ceiling,
                    unit="mm",
                ))
                index += 1
            if measured_max > max_wall:
                findings.append(self.finding(
                    severity=Severity.major,
                    message=(
                        f"Thickest wall measures {measured_max:.2f} mm, above the "
                        f"{max_wall:.2f} mm maximum for {material_label}."
                    ),
                    recommendation="Core out thick sections to keep the wall uniform.",
                    index=index, measured=round(measured_max, 3), threshold=max_wall, unit="mm",
                ))
                index += 1

        # --- 3: local neighbourhood ---------------------------------------
        neighbour_pairs = context.adjacent_wall_pairs()
        neighbour_hits = 0
        for face_a, face_b, thickness_a, thickness_b in neighbour_pairs:
            thin, thick = sorted((thickness_a, thickness_b))
            thin_face = face_a if thickness_a < thickness_b else face_b
            thick_face = face_b if thickness_a < thickness_b else face_a
            if thick < neighbour_floor:
                continue
            if thin >= thick * neighbour_ratio:
                continue
            neighbour_hits += 1
            findings.append(self.finding(
                severity=Severity.major,
                message=(
                    f"Wall on face {thin_face} ({thin:.2f} mm) is only "
                    f"{thin / thick * 100:.0f}% of the adjacent wall on face {thick_face} "
                    f"({thick:.2f} mm); flow stalls below "
                    f"{neighbour_ratio * 100:.0f}%."
                ),
                recommendation=(
                    f"Bring the thin wall up to at least {thick * neighbour_ratio:.2f} mm or "
                    f"taper the transition so the section change is gradual."
                ),
                index=index,
                measured=round(thin / thick, 3),
                threshold=neighbour_ratio,
                unit="ratio",
                geometry_ref=self.face_ref(context, [thin_face, thick_face]),
            ))
            index += 1

        thresholds_used["measured_min_wall_mm"] = round(measured_min, 3)
        thresholds_used["measured_max_wall_mm"] = round(measured_max, 3)
        thresholds_used["sample_count"] = len(wall_field)
        thresholds_used["neighbour_pairs_checked"] = len(neighbour_pairs)

        if not neighbour_pairs:
            assumptions.append(
                "No face-adjacency data was available, so the adjacent-wall (40–60%) check "
                "could not run; only absolute wall limits were applied."
            )

        if not findings:
            return self.passed(
                summary=(
                    f"Wall thickness {measured_min:.2f}–{measured_max:.2f} mm is within the "
                    f"{min_wall:.2f}–{max_wall:.2f} mm range for {material_label}."
                ),
                thresholds_used=thresholds_used,
                assumptions=assumptions,
            )

        total = len(findings)
        blockers = sum(1 for f in findings if f.severity == Severity.blocker)
        summary_bits = []
        if blockers:
            summary_bits.append(f"{blockers} wall region(s) below the fill floor")
        if risky_faces or (not has_face_detail and measured_min < risky_ceiling):
            summary_bits.append("risky-thin walls")
        if over_max_faces or (not has_face_detail and measured_max > max_wall):
            summary_bits.append("walls above the material maximum")
        if neighbour_hits:
            summary_bits.append(f"{neighbour_hits} abrupt thin/thick neighbour pair(s)")

        return self.failed(
            summary=(
                f"{total} wall thickness issue(s): " + ", ".join(summary_bits) + "."
            ),
            findings=self.cap_findings(findings),
            recommendations=[
                f"Keep every wall between {min_wall:.2f} mm and {max_wall:.2f} mm for "
                f"{material_label}.",
                f"Keep any wall at or above {neighbour_ratio * 100:.0f}% of the walls it "
                f"joins, tapering section changes rather than stepping them.",
            ],
            thresholds_used=thresholds_used,
            assumptions=assumptions,
        )
