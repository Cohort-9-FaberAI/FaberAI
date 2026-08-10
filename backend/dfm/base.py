"""``RuleEvaluator`` — the base class every DFM rule inherits from.

One class per rule, grouped into a package per manufacturing process
(``rules/injection_molding/``, ``rules/printing/``, and later ``rules/cnc/``).

The base class owns everything that must behave identically for all 13 rules:

* **graceful degradation** — a rule whose data is absent returns
  ``not_assessed`` with a stated reason and never costs the user points;
* **never crash** — an unexpected exception inside a rule is caught, logged and
  turned into an ``error`` result so one bad rule cannot fail the whole report;
* **stated assumptions** — defaults resolved by the context are copied onto the
  result so the report can always say what it assumed;
* **finding capping** — rules emit at most ``max_findings`` findings, so a noisy
  part cannot produce a 10,000-entry report (the true count is still reported).

Subclasses implement ``_evaluate`` and declare their metadata as class
attributes. They never construct a ``RuleResult`` from scratch — they use the
``passed`` / ``failed`` / ``not_assessed`` / ``suppressed`` helpers.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Sequence

from .config import DFMConfig
from .context import EvaluationContext
from .models import (
    SEVERITY_ORDER,
    Finding,
    GeometryRef,
    ProcessType,
    RuleResult,
    RuleStatus,
    Severity,
    SubScore,
    ThresholdType,
    Vector3,
)

logger = logging.getLogger(__name__)


class RuleEvaluator(ABC):
    """Base class for a single DFM check."""

    # --- Rule metadata: every subclass sets these -------------------------
    rule_id: str = ""
    name: str = ""
    process: ProcessType
    sub_score: SubScore
    threshold_type: ThresholdType
    # Human-readable description of what the rule flags; copied into the
    # report so the AI layer never has to invent an explanation of the check.
    what_it_flags: str = ""

    def __init__(self, config: DFMConfig):
        self.config = config
        self.thresholds: Dict[str, Any] = config.rule(self.rule_id)

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(self, context: EvaluationContext) -> RuleResult:
        """Evaluate the rule, converting any failure into a safe result."""
        if not self.config.rule_enabled(self.rule_id):
            return self.suppressed("Rule is disabled in thresholds.yaml.")
        try:
            return self._evaluate(context)
        except Exception as exc:  # never let one rule sink the report
            logger.exception("DFM rule %s raised: %s", self.rule_id, exc)
            return self._result(
                status=RuleStatus.error,
                summary=f"{self.name} could not be evaluated.",
                explanation=(
                    "The check failed unexpectedly and was excluded from the score. "
                    "This is a tool problem, not a design problem."
                ),
                not_assessed_reason=f"Internal error: {exc}",
            )

    @abstractmethod
    def _evaluate(self, context: EvaluationContext) -> RuleResult:
        """Rule logic. Return one of the helper-built results below."""

    # ------------------------------------------------------------------
    # Result builders
    # ------------------------------------------------------------------

    def _result(
        self,
        status: RuleStatus,
        summary: str,
        explanation: str = "",
        findings: Optional[Sequence[Finding]] = None,
        recommendations: Optional[Sequence[str]] = None,
        thresholds_used: Optional[Dict[str, Any]] = None,
        assumptions: Optional[Sequence[str]] = None,
        not_assessed_reason: Optional[str] = None,
        missing_inputs: Optional[Sequence[str]] = None,
    ) -> RuleResult:
        finding_list = list(findings or [])
        severity = None
        if finding_list:
            severity = max(finding_list, key=lambda f: SEVERITY_ORDER[f.severity]).severity
        return RuleResult(
            rule_id=self.rule_id,
            name=self.name,
            process=self.process,
            sub_score=self.sub_score,
            threshold_type=self.threshold_type,
            status=status,
            severity=severity,
            summary=summary,
            explanation=explanation or self.what_it_flags,
            recommendations=list(recommendations or []),
            findings=finding_list,
            thresholds_used=dict(thresholds_used or {}),
            assumptions=[a for a in (assumptions or []) if a],
            not_assessed_reason=not_assessed_reason,
            missing_inputs=list(missing_inputs or []),
        )

    def passed(
        self,
        summary: str,
        explanation: str = "",
        thresholds_used: Optional[Dict[str, Any]] = None,
        assumptions: Optional[Sequence[str]] = None,
    ) -> RuleResult:
        return self._result(
            status=RuleStatus.passed,
            summary=summary,
            explanation=explanation,
            thresholds_used=thresholds_used,
            assumptions=assumptions,
        )

    def failed(
        self,
        summary: str,
        findings: Sequence[Finding],
        explanation: str = "",
        recommendations: Optional[Sequence[str]] = None,
        thresholds_used: Optional[Dict[str, Any]] = None,
        assumptions: Optional[Sequence[str]] = None,
    ) -> RuleResult:
        return self._result(
            status=RuleStatus.failed,
            summary=summary,
            explanation=explanation,
            findings=findings,
            recommendations=recommendations,
            thresholds_used=thresholds_used,
            assumptions=assumptions,
        )

    def not_assessed(
        self,
        reason: str,
        missing_inputs: Optional[Sequence[str]] = None,
        summary: str = "",
        assumptions: Optional[Sequence[str]] = None,
    ) -> RuleResult:
        """Graceful degradation: excluded from the score, never a penalty."""
        return self._result(
            status=RuleStatus.not_assessed,
            summary=summary or f"{self.name}: not assessed.",
            explanation=(
                "This check was excluded from the score because the data it needs was not "
                "available. It has not counted against the part."
            ),
            not_assessed_reason=reason,
            missing_inputs=missing_inputs,
            assumptions=assumptions,
        )

    def suppressed(
        self,
        reason: str,
        summary: str = "",
        assumptions: Optional[Sequence[str]] = None,
    ) -> RuleResult:
        """The check does not apply to this process (e.g. P1 on powder bed)."""
        return self._result(
            status=RuleStatus.suppressed,
            summary=summary or f"{self.name}: not applicable.",
            explanation=reason,
            not_assessed_reason=reason,
            assumptions=assumptions,
        )

    # ------------------------------------------------------------------
    # Finding helpers
    # ------------------------------------------------------------------

    def finding(
        self,
        severity: Severity,
        message: str,
        recommendation: str,
        index: int = 0,
        measured: Optional[float] = None,
        threshold: Optional[float] = None,
        unit: Optional[str] = None,
        geometry_ref: Optional[GeometryRef] = None,
    ) -> Finding:
        message_text = str(message or "").strip()
        if message_text and not message_text.startswith((f"{self.rule_id}:", f"[{self.rule_id}]")):
            message_text = f"{self.rule_id}: {message_text}"

        return Finding(
            finding_id=f"{self.rule_id.lower()}_{index:03d}",
            rule_id=self.rule_id,
            severity=severity,
            message=message_text,
            recommendation=recommendation,
            measured=measured,
            threshold=threshold,
            unit=unit,
            geometry_ref=geometry_ref,
        )

    @property
    def max_findings(self) -> int:
        return int(self.thresholds.get("max_findings", 20))

    def cap_findings(self, findings: List[Finding]) -> List[Finding]:
        """Keep the most severe findings, up to ``max_findings``."""
        if len(findings) <= self.max_findings:
            return findings
        ordered = sorted(findings, key=lambda f: -SEVERITY_ORDER[f.severity])
        return ordered[: self.max_findings]

    @staticmethod
    def face_ref(context: EvaluationContext, face_ids: Sequence[int]) -> GeometryRef:
        """Build a geometry reference, attaching a centroid when available so
        the frontend can point at the region in the 3D viewer."""
        ids = [int(face_id) for face_id in face_ids]
        centroid = None
        for face_id in ids:
            face = context.face(face_id)
            if face is not None and face.centroid is not None:
                centroid = Vector3(
                    x=face.centroid.x, y=face.centroid.y, z=face.centroid.z
                )
                break
        return GeometryRef(face_ids=ids, centroid=centroid)

    @staticmethod
    def feature_ref(
        feature_type: str,
        feature_ids: Sequence[int],
        centroid: Optional[Any] = None,
        face_ids: Optional[Sequence[int]] = None,
    ) -> GeometryRef:
        point = None
        if centroid is not None:
            point = Vector3(x=centroid.x, y=centroid.y, z=centroid.z)
        return GeometryRef(
            feature_type=feature_type,
            feature_ids=[int(i) for i in feature_ids],
            face_ids=[int(i) for i in (face_ids or [])],
            centroid=point,
        )
