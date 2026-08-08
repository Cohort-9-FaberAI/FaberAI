"""Report schemas for the DFM rule engine.

These models are the contract everything downstream reads: the API response,
the persisted ``results_json`` payload, and the deterministic context handed
to the AI layer. Nothing here performs geometry work — every value is either
copied from the geometry engine output or derived from a threshold comparison.

Severity uses the spec's Blocker / Major / Minor tiers rather than the legacy
``high/medium/low`` enum in ``app.schemas`` because only a Blocker carries the
extra "process is not viable" behaviour, which high/medium/low cannot express.
``SEVERITY_TO_LEGACY`` maps back for consumers still on the old enum.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

REPORT_VERSION = "1.0"


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Severity(str, Enum):
    """Spec severity tiers. Only ``blocker`` makes a process non-viable."""

    blocker = "blocker"
    major = "major"
    minor = "minor"


class RuleStatus(str, Enum):
    """Outcome of a single rule evaluation.

    ``not_assessed`` is the graceful-degradation state: the rule could not run
    because optional user input or geometry data was absent. It never costs the
    user points and is excluded from the roll-up denominator.
    """

    passed = "pass"
    failed = "fail"
    not_assessed = "not_assessed"
    suppressed = "suppressed"   # rule does not apply to this process (e.g. P1 on SLS)
    error = "error"             # rule raised unexpectedly; treated like not_assessed


class ProcessType(str, Enum):
    """Manufacturing processes the engine can evaluate.

    New processes (CNC, sheet metal) are added here plus a rules package and a
    ``processes:`` block in thresholds.yaml — no engine changes required.
    """

    injection_molding = "injection_molding"
    printing = "printing"


class SubScore(str, Enum):
    """PRD sub-score buckets each rule feeds."""

    geometry = "geometry"
    tolerance_feature = "tolerance_feature"
    cost_risk = "cost_risk"


class ThresholdType(str, Enum):
    """Spec threshold taxonomy — kept explicit so the report can state how a
    verdict was reached (looked-up value vs fixed ratio vs binary detection)."""

    material_process = "type_1"   # looked up from a material / process table
    geometric_ratio = "type_2"    # fixed proportion between two measurements
    topological = "type_3"        # yes/no feasibility test, no threshold


SEVERITY_TO_LEGACY: Dict[Severity, str] = {
    Severity.blocker: "high",
    Severity.major: "medium",
    Severity.minor: "low",
}

SEVERITY_ORDER: Dict[Severity, int] = {
    Severity.minor: 1,
    Severity.major: 2,
    Severity.blocker: 3,
}


# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------

class Vector3(BaseModel):
    model_config = ConfigDict(extra="forbid")
    x: float
    y: float
    z: float


class GeometryRef(BaseModel):
    """Pointer back into the geometry engine output for one finding.

    Everything is optional because coverage differs per rule and per input
    format: a STEP part has face ids, an STL part usually only has triangle
    indices and a bounding box. The frontend uses ``centroid``/``bbox_min``/
    ``bbox_max`` for the Three.js highlight; the AI layer quotes the ids.
    """

    model_config = ConfigDict(extra="forbid")

    face_ids: List[int] = Field(default_factory=list)
    edge_ids: List[int] = Field(default_factory=list)
    wall_sample_ids: List[int] = Field(default_factory=list)
    feature_type: Optional[str] = None      # "rib" | "boss" | "hole" | "cavity" | ...
    feature_ids: List[int] = Field(default_factory=list)
    centroid: Optional[Vector3] = None
    bbox_min: Optional[Vector3] = None
    bbox_max: Optional[Vector3] = None


class Finding(BaseModel):
    """One concrete instance of a rule being violated.

    A rule can produce many findings (e.g. 200 thin-wall regions); the scoring
    engine caps their combined impact so one noisy rule cannot dominate.
    """

    model_config = ConfigDict(extra="forbid")

    finding_id: str
    rule_id: str
    severity: Severity
    message: str
    recommendation: str
    # Measured value vs the threshold it was compared against, so the AI layer
    # can quote real numbers instead of inventing them.
    measured: Optional[float] = None
    threshold: Optional[float] = None
    unit: Optional[str] = None
    geometry_ref: Optional[GeometryRef] = None
    # Filled in by the scoring engine once per-rule capping is applied.
    score_impact: float = 0.0

    @property
    def legacy_severity(self) -> str:
        return SEVERITY_TO_LEGACY[self.severity]


# ---------------------------------------------------------------------------
# Rule results
# ---------------------------------------------------------------------------

class RuleResult(BaseModel):
    """Outcome of one rule for one process."""

    model_config = ConfigDict(extra="forbid")

    rule_id: str                       # "M1", "P3", ...
    name: str
    process: ProcessType
    sub_score: SubScore
    threshold_type: ThresholdType
    status: RuleStatus
    # Highest severity across findings; None when the rule passed / did not run.
    severity: Optional[Severity] = None
    summary: str = ""
    explanation: str = ""
    recommendations: List[str] = Field(default_factory=list)
    findings: List[Finding] = Field(default_factory=list)
    # The concrete numbers this run compared against, so a report is
    # reproducible even after thresholds.yaml is retuned.
    thresholds_used: Dict[str, Any] = Field(default_factory=dict)
    # Stated defaults the rule fell back on (spec: never penalise, always say so).
    assumptions: List[str] = Field(default_factory=list)
    # Set when status is not_assessed / suppressed / error.
    not_assessed_reason: Optional[str] = None
    # Geometry fields the rule needed but did not receive.
    missing_inputs: List[str] = Field(default_factory=list)
    score_impact: float = 0.0

    @property
    def counts_toward_score(self) -> bool:
        """not_assessed / suppressed / error rules leave the denominator."""
        return self.status in (RuleStatus.passed, RuleStatus.failed)


# ---------------------------------------------------------------------------
# Process-level and top-level report
# ---------------------------------------------------------------------------

class SubScoreResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sub_score: SubScore
    score: Optional[float] = None      # None when every rule in the bucket is not_assessed
    assessed_rules: int = 0
    total_rules: int = 0
    deductions: float = 0.0


class ProcessReport(BaseModel):
    """Manufacturability verdict for a single process."""

    model_config = ConfigDict(extra="forbid")

    process: ProcessType
    # The two headline outputs the PRD asks for.
    manufacturable: bool
    score: float = Field(ge=0, le=100)

    verdict_label: str = ""            # "Manufacturable" | "Needs review" | "Not viable"
    redesign_recommended: bool = False
    # Coverage of the check-set: how much of the verdict rests on real data.
    confidence: float = Field(default=1.0, ge=0, le=1)

    sub_scores: List[SubScoreResult] = Field(default_factory=list)
    rule_results: List[RuleResult] = Field(default_factory=list)
    blocking_rule_ids: List[str] = Field(default_factory=list)
    not_assessed_rule_ids: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    # Printing only: which build orientation every P-check was measured against.
    orientation_assumed: Optional[str] = None

    @property
    def findings(self) -> List[Finding]:
        return [f for r in self.rule_results for f in r.findings]


class ProcessRecommendation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recommended_process: Optional[ProcessType] = None
    reason: str = ""
    # Per-process one-liners the AI layer can quote directly.
    comparison: Dict[str, str] = Field(default_factory=dict)


class PartSummary(BaseModel):
    """Geometry facts copied verbatim from the geometry engine output."""

    model_config = ConfigDict(extra="forbid")

    filename: Optional[str] = None
    source_format: Optional[str] = None
    units: str = "mm"
    volume_mm3: Optional[float] = None
    surface_area_mm2: Optional[float] = None
    bounding_box_mm: Optional[List[float]] = None   # [width, depth, height]
    nominal_wall_mm: Optional[float] = None
    min_wall_mm: Optional[float] = None
    max_wall_mm: Optional[float] = None
    face_count: int = 0
    measurements_reliable: bool = True


class DFMReport(BaseModel):
    """Full manufacturability report — the single object the AI layer reads."""

    model_config = ConfigDict(extra="forbid")

    report_version: str = REPORT_VERSION
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    config_version: str = ""
    analysis_id: Optional[str] = None

    part: PartSummary = Field(default_factory=PartSummary)
    # Echo of the optional user inputs, including which ones were defaulted.
    inputs: Dict[str, Any] = Field(default_factory=dict)

    processes: List[ProcessReport] = Field(default_factory=list)
    recommendation: ProcessRecommendation = Field(default_factory=ProcessRecommendation)

    # Headline values for the process the user asked about (or the recommended
    # one when no process was specified) — mirrors the frontend contract.
    manufacturable: bool = True
    manufacturability_score: float = Field(default=100.0, ge=0, le=100)
    # Convenience per-process headline values so callers can read scores
    # for printing and injection moulding directly from the top-level report.
    printing_manufacturable: Optional[bool] = None
    printing_score: Optional[float] = Field(default=None, ge=0, le=100)
    molding_manufacturable: Optional[bool] = None
    molding_score: Optional[float] = Field(default=None, ge=0, le=100)

    # Non-fatal problems with the *input* (unreliable mesh, missing topology).
    warnings: List[str] = Field(default_factory=list)

    def process_report(self, process: ProcessType) -> Optional[ProcessReport]:
        for report in self.processes:
            if report.process == process:
                return report
        return None

    def rule(self, rule_id: str) -> Optional[RuleResult]:
        """Look up a rule result by id (e.g. "M1") across all processes."""
        for report in self.processes:
            for result in report.rule_results:
                if result.rule_id == rule_id.upper():
                    return result
        return None

    def failed_rules(self) -> List[RuleResult]:
        return [
            result
            for report in self.processes
            for result in report.rule_results
            if result.status == RuleStatus.failed
        ]
