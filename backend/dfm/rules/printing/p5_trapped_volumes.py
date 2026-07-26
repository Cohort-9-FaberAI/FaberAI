"""P5 · Trapped Volumes / No Drain (Type 3 — topological, binary)."""

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

_SEVERITY_BY_NAME = {
    "blocker": Severity.blocker,
    "major": Severity.major,
    "minor": Severity.minor,
}


class TrappedVolumeRule(RuleEvaluator):
    """A hollow region with no escape hole traps liquid resin (SLA) or unfused
    powder (SLS/MJF).

    Type 3: there is no threshold to tune, only detection. The engine consumes
    detection results rather than producing them, preferring, in order:

    1. ``trapped_volumes[]`` — a dedicated void analysis, if geometry ships one;
    2. ``cavities[]`` — a cavity with ``is_enclosed`` true, or with no opening
       face and no opening area, is enclosed.

    Severity is process-dependent: fatal for resin and powder, cosmetic for
    FDM where the cavity is simply printed as sparse infill and nothing needs
    to drain.
    """

    rule_id = "P5"
    name = "Trapped Volumes / No Drain"
    process = ProcessType.printing
    sub_score = SubScore.geometry
    threshold_type = ThresholdType.topological
    what_it_flags = (
        "Fully enclosed internal cavities have no way to release uncured resin or unfused "
        "powder, which stays inside the part and adds weight, cost and contamination."
    )

    def _evaluate(self, context: EvaluationContext) -> RuleResult:
        process_spec = context.printing_process
        assumptions = [a for a in (context.printing_process_assumption,) if a]

        source = "trapped_volumes"
        candidates = context.geometry.trapped_volumes
        if candidates is None:
            source = "cavities"
            candidates = context.geometry.cavities

        if not candidates:
            if source == "cavities" and not context.geometry.cavities:
                # No cavity detection on the STL path — say so rather than
                # claiming a clean bill of health the data cannot support.
                if context.geometry.source_format and \
                        context.geometry.source_format.lower() != "step":
                    return self.not_assessed(
                        "Internal cavity detection is not available for this input format, so "
                        "trapped volumes could not be checked.",
                        missing_inputs=["cavities", "trapped_volumes"],
                        assumptions=assumptions,
                    )
            return self.passed(
                summary="No enclosed internal cavities were detected.",
                thresholds_used={"source": source, "cavities_checked": 0},
                assumptions=assumptions,
            )

        min_volume = float(self.thresholds.get("min_cavity_volume_mm3", 10.0))
        severity_table = self.thresholds.get("severity_by_process", {}) or {}
        severity = _SEVERITY_BY_NAME.get(
            str(severity_table.get(process_spec.key, "major")).lower(), Severity.major
        )

        enclosed = []
        for cavity in candidates:
            if cavity.volume and cavity.volume < min_volume:
                continue
            if cavity.is_enclosed is True:
                enclosed.append(cavity)
                continue
            if cavity.is_enclosed is False:
                continue
            # Fall back to the opening data: no opening face and no opening
            # area means nothing connects the void to the outside.
            if cavity.opening_face is None and not (cavity.opening_area or 0) > 0:
                enclosed.append(cavity)

        thresholds_used = {
            "source": source,
            "printing_process": process_spec.key,
            "traps_material": process_spec.traps_material,
            "cavities_checked": len(candidates),
            "enclosed_cavities": len(enclosed),
            "min_cavity_volume_mm3": min_volume,
            "severity_for_process": severity.value,
        }

        if not enclosed:
            return self.passed(
                summary=(
                    f"All {len(candidates)} internal cavity(ies) have an opening to the "
                    f"exterior — nothing is trapped."
                ),
                thresholds_used=thresholds_used,
                assumptions=assumptions,
            )

        if not process_spec.traps_material:
            # Same treatment as P1 on powder bed: the check does not apply to
            # this process, so it is suppressed rather than passed or penalised.
            return self.suppressed(
                f"{len(enclosed)} enclosed cavity(ies) were found, but "
                f"{process_spec.display_name} leaves no liquid resin or unfused powder inside "
                f"them — it fills voids with sparse infill, so no drain hole is required.",
                summary=(
                    f"Trapped volumes not applicable to {process_spec.display_name} "
                    f"({len(enclosed)} enclosed cavity(ies) found)."
                ),
                assumptions=assumptions,
            )

        material_word = "resin" if process_spec.key == "sla" else "powder"
        findings: List[Finding] = []
        for index, cavity in enumerate(enclosed):
            volume_text = f"{cavity.volume:,.0f} mm³ " if cavity.volume else ""
            findings.append(self.finding(
                severity=severity,
                message=(
                    f"Cavity {cavity.id} ({volume_text}enclosed) has no opening to the "
                    f"exterior — {material_word} will be trapped inside on "
                    f"{process_spec.display_name}."
                ),
                recommendation=(
                    f"Add at least one drain/escape hole (typically ø3–5 mm, two holes for "
                    f"through-flow) so trapped {material_word} can escape."
                ),
                index=index,
                measured=cavity.volume or None,
                unit="mm3" if cavity.volume else None,
                geometry_ref=self.feature_ref(
                    "cavity", [cavity.id], None, cavity.wall_faces or cavity.bottom_faces
                ),
            ))

        return self.failed(
            summary=(
                f"{len(enclosed)} enclosed cavity(ies) with no drain — trapped {material_word} "
                f"on {process_spec.display_name}."
            ),
            findings=self.cap_findings(findings),
            recommendations=[
                f"Add drain holes to every enclosed void before printing on "
                f"{process_spec.display_name}.",
                "Two holes drain far better than one — one lets material out, one lets air in.",
            ],
            thresholds_used=thresholds_used,
            assumptions=assumptions,
        )
