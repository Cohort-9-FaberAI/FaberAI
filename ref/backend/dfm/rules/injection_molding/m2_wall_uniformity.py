"""M2 · Wall Thickness Uniformity (Type 2 ratio + Type 1 material band)."""

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


class WallUniformityRule(RuleEvaluator):
    """Thick/thin variation causes differential cooling → sink, warp, residual
    stress. The PRD's single highest-impact rule.

    Two tests:

    1. **The 25% rule** — amorphous polymers (ABS, PC, PS) should stay within
       ±25% of nominal; semi-crystalline (Nylon, PP, PBT) tighten to ±15%
       because they shrink more. The material class picks the band; with no
       material the wider (more forgiving) band is used and stated.
    2. **Taper** — any section transition should be 3:1 or gentler. Measured
       across adjacent faces from the geometry engine's face graph.
    """

    rule_id = "M2"
    name = "Wall Thickness Uniformity"
    process = ProcessType.injection_molding
    sub_score = SubScore.geometry
    threshold_type = ThresholdType.geometric_ratio
    what_it_flags = (
        "Thick and thin sections cool at different rates, producing sink marks, warp and "
        "locked-in stress."
    )

    def _evaluate(self, context: EvaluationContext) -> RuleResult:
        wall_field = context.geometry.wall_field()
        nominal = context.nominal_wall()
        if not wall_field or not nominal:
            return self.not_assessed(
                "Wall thickness sampling produced no nominal wall to compare against.",
                missing_inputs=["wall_samples", "nominal_wall"],
            )

        assumptions: List[str] = []
        bands = self.thresholds.get("variation_band", {}) or {}
        if context.material is not None:
            material_class = context.material.material_class
            band = float(bands.get(material_class, self.thresholds.get("default_band", 0.25)))
            band_label = f"{context.material.display_name} ({material_class.replace('_', '-')})"
        else:
            material_class = None
            band = float(self.thresholds.get("default_band", 0.25))
            band_label = "no material supplied — amorphous band applied"
            assumptions.append(
                f"{context.material_assumption} The wider ±{band * 100:.0f}% amorphous "
                f"uniformity band was applied, which is the more forgiving of the two."
            )

        minor_fraction = float(self.thresholds.get("out_of_band_fraction_minor", 0.10))
        major_fraction = float(self.thresholds.get("out_of_band_fraction_major", 0.25))
        max_taper = float(self.thresholds.get("max_transition_ratio", 3.0))

        out_of_band = [t for t in wall_field if abs(t - nominal) / nominal > band]
        out_fraction = len(out_of_band) / len(wall_field)

        # Abrupt transitions across adjacent walls.
        pairs = context.adjacent_wall_pairs()
        abrupt: List[tuple[int, int, float]] = []
        for face_a, face_b, thickness_a, thickness_b in pairs:
            thin, thick = sorted((thickness_a, thickness_b))
            if thin <= 0:
                continue
            ratio = thick / thin
            if ratio > max_taper:
                thin_face = face_a if thickness_a < thickness_b else face_b
                thick_face = face_b if thickness_a < thickness_b else face_a
                abrupt.append((thin_face, thick_face, ratio))

        thresholds_used = {
            "nominal_wall_mm": round(nominal, 3),
            "variation_band": band,
            "material_class": material_class or "unknown",
            "band_basis": band_label,
            "max_transition_ratio": max_taper,
            "samples": len(wall_field),
            "out_of_band_samples": len(out_of_band),
            "out_of_band_fraction": round(out_fraction, 4),
            "abrupt_transitions": len(abrupt),
            "adjacent_pairs_checked": len(pairs),
        }
        if not pairs:
            assumptions.append(
                "No face-adjacency data was available, so the 3:1 taper check could not run; "
                "only the variation band was applied."
            )

        findings: List[Finding] = []
        index = 0

        if out_fraction > minor_fraction:
            worst = max(wall_field, key=lambda t: abs(t - nominal))
            deviation = abs(worst - nominal) / nominal
            # Variation beyond the band *with* an abrupt transition is Major;
            # mild variation that still tapers gently is Minor (spec mapping).
            severity = (
                Severity.major
                if out_fraction > major_fraction or abrupt
                else Severity.minor
            )
            findings.append(self.finding(
                severity=severity,
                message=(
                    f"{out_fraction * 100:.0f}% of wall samples fall outside ±{band * 100:.0f}% "
                    f"of the {nominal:.2f} mm nominal wall (worst: {worst:.2f} mm, "
                    f"{deviation * 100:.0f}% off nominal)."
                ),
                recommendation=(
                    f"Bring wall sections within ±{band * 100:.0f}% of {nominal:.2f} mm — core "
                    f"out thick areas rather than thickening thin ones."
                ),
                index=index,
                measured=round(deviation, 3),
                threshold=band,
                unit="fraction of nominal",
            ))
            index += 1

        for thin_face, thick_face, ratio in sorted(abrupt, key=lambda item: -item[2]):
            findings.append(self.finding(
                severity=Severity.major,
                message=(
                    f"Section transition between faces {thin_face} and {thick_face} steps "
                    f"{ratio:.1f}:1, steeper than the {max_taper:.0f}:1 limit."
                ),
                recommendation=(
                    f"Taper the transition over a length of at least {max_taper:.0f}x the "
                    f"thickness change so the melt front does not stall."
                ),
                index=index,
                measured=round(ratio, 2),
                threshold=max_taper,
                unit="ratio",
                geometry_ref=self.face_ref(context, [thin_face, thick_face]),
            ))
            index += 1

        if not findings:
            return self.passed(
                summary=(
                    f"Wall thickness is uniform: {(1 - out_fraction) * 100:.0f}% of samples sit "
                    f"within ±{band * 100:.0f}% of the {nominal:.2f} mm nominal wall."
                ),
                thresholds_used=thresholds_used,
                assumptions=assumptions,
            )

        return self.failed(
            summary=(
                f"Wall thickness varies beyond the ±{band * 100:.0f}% band"
                + (f" with {len(abrupt)} abrupt transition(s)" if abrupt else "")
                + "."
            ),
            findings=self.cap_findings(findings),
            recommendations=[
                f"Hold the wall within ±{band * 100:.0f}% of {nominal:.2f} mm.",
                f"Taper every section change at {max_taper:.0f}:1 or gentler.",
                "Core out thick regions instead of adding material to thin ones.",
            ],
            thresholds_used=thresholds_used,
            assumptions=assumptions,
        )
