"""M7 · Tolerance Feasibility (Type 1 — data-gated, ISO 20457)."""

from __future__ import annotations

from typing import List, Optional

from ...base import RuleEvaluator
from ...config import capability_table
from ...context import EvaluationContext
from ...models import (
    Finding,
    ProcessType,
    RuleResult,
    Severity,
    SubScore,
    ThresholdType,
)


class ToleranceFeasibilityRule(RuleEvaluator):
    """A requested tolerance tighter than moulding reliably holds for that
    material and feature size.

    This is the rule the spec is most explicit about degrading: with no
    tolerance data it reports **Not assessed** and leaves the roll-up
    denominator entirely. It is never a penalty for the user's silence.

    Capability comes from the size-banded table in ``thresholds.yaml`` (an
    ISO 20457-shaped table, not invented numbers), refined by the material's
    own capability when the material is known.
    """

    rule_id = "M7"
    name = "Tolerance Feasibility"
    process = ProcessType.injection_molding
    sub_score = SubScore.tolerance_feature
    threshold_type = ThresholdType.material_process
    what_it_flags = (
        "Dimensional tolerances tighter than the moulding process can hold for that material "
        "and feature size, which show up as scrap rather than as a design problem."
    )

    def _evaluate(self, context: EvaluationContext) -> RuleResult:
        requests = context.inputs.tolerances
        if not requests:
            return self.not_assessed(
                "No tolerances were supplied, so tolerance feasibility was excluded from the "
                "score entirely — it has not lowered the result.",
                missing_inputs=["inputs.tolerances"],
                summary="Tolerance feasibility: not assessed (no tolerances supplied).",
            )

        table = capability_table(self.thresholds.get("capability_by_size_mm"))
        if not table:
            return self.not_assessed(
                "No tolerance capability table is configured in thresholds.yaml.",
                missing_inputs=["rules.M7.capability_by_size_mm"],
            )

        borderline_multiplier = float(self.thresholds.get("borderline_multiplier", 1.25))
        assumptions: List[str] = []
        material_capability: Optional[float] = None
        if context.material is not None:
            material_capability = context.material.tolerance_capability_mm
        else:
            assumptions.append(
                f"{context.material_assumption} Tolerance capability was taken from the generic "
                f"size table only."
            )

        findings: List[Finding] = []
        for index, request in enumerate(requests):
            capability = self._capability_for_size(table, request.feature_size_mm)
            if material_capability is not None:
                # The material's own floor cannot be beaten, whatever the size band.
                capability = max(capability, material_capability)

            if request.requested_tolerance_mm >= capability:
                continue

            borderline = request.requested_tolerance_mm >= capability / borderline_multiplier
            severity = Severity.minor if borderline else Severity.major
            findings.append(self.finding(
                severity=severity,
                message=(
                    f"'{request.label}' requests ±{request.requested_tolerance_mm:.3f} mm on a "
                    f"{request.feature_size_mm:.1f} mm feature; injection moulding holds about "
                    f"±{capability:.3f} mm at that size"
                    + (" — borderline." if borderline else " — tighter than the process holds.")
                ),
                recommendation=(
                    f"Open the tolerance to ±{capability:.3f} mm, or plan a secondary machining "
                    f"operation for this dimension."
                ),
                index=index,
                measured=request.requested_tolerance_mm,
                threshold=round(capability, 4),
                unit="mm",
                geometry_ref=(
                    self.face_ref(context, [request.face_id])
                    if request.face_id is not None else None
                ),
            ))

        thresholds_used = {
            "standard": "ISO 20457 (plastic moulded tolerances)",
            "tolerances_checked": len(requests),
            "material_capability_mm": material_capability,
            "borderline_multiplier": borderline_multiplier,
            "capability_by_size_mm": [
                [size, tolerance] for size, tolerance in table
            ],
        }

        if not findings:
            return self.passed(
                summary=(
                    f"All {len(requests)} requested tolerance(s) are within moulding capability."
                ),
                thresholds_used=thresholds_used,
                assumptions=assumptions,
            )

        return self.failed(
            summary=(
                f"{len(findings)} of {len(requests)} requested tolerance(s) are tighter than "
                f"moulding capability."
            ),
            findings=self.cap_findings(findings),
            recommendations=[
                "Open tolerances to the process capability wherever the function allows.",
                "Reserve tight tolerances for the few dimensions that genuinely need them, and "
                "machine those as a secondary operation.",
            ],
            thresholds_used=thresholds_used,
            assumptions=assumptions,
        )

    @staticmethod
    def _capability_for_size(table, feature_size_mm: float) -> float:
        """First band whose upper size bound covers the feature."""
        for max_size, tolerance in table:
            if max_size is None or feature_size_mm <= max_size:
                return tolerance
        return table[-1][1]
