"""Builds the deterministic context the AI answers from.

The rule the whole AI layer is built around: **the model never measures and
never judges**. Geometry produced the numbers, the DFM rule engine produced the
verdicts, and this module flattens both into a compact record the model may
quote but not recompute. If a value is not in this context, the model has no
business stating it.

Everything here is derived from a ``DFMReport`` that already exists. Nothing in
this module runs geometry or evaluates a rule.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from dfm.models import DFMReport, ProcessReport, RuleResult, RuleStatus

# Findings per rule handed to the model. The full list stays in the report;
# this keeps the prompt bounded on parts with hundreds of thin-wall regions.
MAX_FINDINGS_PER_RULE = 5


def build_ai_context(
    report: DFMReport,
    geometry: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Flatten a DFM report (and optional geometry facts) into model context."""
    context: Dict[str, Any] = {
        "report_version": report.report_version,
        "config_version": report.config_version,
        "generated_at": report.generated_at.isoformat(),
        "part": report.part.model_dump(exclude_none=True),
        "user_inputs": {k: v for k, v in report.inputs.items() if v is not None},
        "headline": {
            "manufacturable": report.manufacturable,
            "manufacturability_score": report.manufacturability_score,
        },
        "processes": [_process_context(p) for p in report.processes],
        "recommendation": report.recommendation.model_dump(exclude_none=True),
        "input_warnings": report.warnings,
    }

    if geometry:
        context["geometry_facts"] = _geometry_facts(geometry)

    return context


def _process_context(process: ProcessReport) -> Dict[str, Any]:
    return {
        "process": process.process.value,
        "manufacturable": process.manufacturable,
        "score": process.score,
        "verdict": process.verdict_label,
        "redesign_recommended": process.redesign_recommended,
        "confidence": process.confidence,
        "orientation_assumed": process.orientation_assumed,
        "blocking_rules": process.blocking_rule_ids,
        "not_assessed_rules": process.not_assessed_rule_ids,
        "assumptions": process.assumptions,
        "sub_scores": [
            {
                "name": s.sub_score.value,
                "score": s.score,
                "assessed_rules": s.assessed_rules,
                "total_rules": s.total_rules,
            }
            for s in process.sub_scores
        ],
        "rules": [_rule_context(r) for r in process.rule_results],
    }


def _rule_context(rule: RuleResult) -> Dict[str, Any]:
    entry: Dict[str, Any] = {
        "rule_id": rule.rule_id,
        "name": rule.name,
        "status": rule.status.value,
        "severity": rule.severity.value if rule.severity else None,
        "sub_score": rule.sub_score.value,
        "threshold_type": rule.threshold_type.value,
        "summary": rule.summary,
        "explanation": rule.explanation,
        "score_impact": rule.score_impact,
    }

    if rule.recommendations:
        entry["recommendations"] = rule.recommendations
    if rule.thresholds_used:
        entry["thresholds_used"] = rule.thresholds_used
    if rule.assumptions:
        entry["assumptions"] = rule.assumptions
    if rule.status in (RuleStatus.not_assessed, RuleStatus.suppressed, RuleStatus.error):
        entry["not_assessed_reason"] = rule.not_assessed_reason
        if rule.missing_inputs:
            entry["missing_geometry_inputs"] = rule.missing_inputs

    if rule.findings:
        entry["finding_count"] = len(rule.findings)
        entry["findings"] = [
            _finding_context(f) for f in rule.findings[:MAX_FINDINGS_PER_RULE]
        ]
        if len(rule.findings) > MAX_FINDINGS_PER_RULE:
            entry["findings_truncated"] = (
                f"Showing {MAX_FINDINGS_PER_RULE} of {len(rule.findings)} findings; "
                f"the rest are in the full report."
            )

    return entry


def _finding_context(finding) -> Dict[str, Any]:
    entry: Dict[str, Any] = {
        "finding_id": finding.finding_id,
        "severity": finding.severity.value,
        "message": finding.message,
        "recommendation": finding.recommendation,
        "score_impact": finding.score_impact,
    }
    if finding.measured is not None:
        entry["measured"] = finding.measured
    if finding.threshold is not None:
        entry["threshold"] = finding.threshold
    if finding.unit:
        entry["unit"] = finding.unit

    ref = finding.geometry_ref
    if ref is not None:
        geometry_ref: Dict[str, Any] = {}
        if ref.face_ids:
            # Long id lists add tokens without adding meaning to an answer.
            geometry_ref["face_ids"] = ref.face_ids[:10]
            if len(ref.face_ids) > 10:
                geometry_ref["face_id_count"] = len(ref.face_ids)
        if ref.feature_type:
            geometry_ref["feature_type"] = ref.feature_type
        if ref.feature_ids:
            geometry_ref["feature_ids"] = ref.feature_ids[:10]
        if ref.centroid is not None:
            geometry_ref["centroid"] = ref.centroid.model_dump()
        if geometry_ref:
            entry["geometry_ref"] = geometry_ref

    return entry


def _geometry_facts(geometry: Dict[str, Any]) -> Dict[str, Any]:
    """A small, safe slice of the raw geometry payload.

    Only aggregate measurements — never the faces/edges/samples arrays, which
    would blow the context window and invite the model to re-derive results the
    rule engine already computed.
    """
    keys = (
        "source_format",
        "volume_mm3",
        "surface_area_mm2",
        "measurements_reliable",
        "nominal_wall",
    )
    facts: Dict[str, Any] = {k: geometry.get(k) for k in keys if geometry.get(k) is not None}

    stats = geometry.get("wall_thickness_stats")
    if isinstance(stats, dict):
        facts["wall_thickness"] = {
            k: stats.get(k)
            for k in ("minimum_wall", "maximum_wall", "mean_wall", "median_wall")
            if stats.get(k) is not None
        }

    bbox = geometry.get("bounding_box")
    if isinstance(bbox, dict):
        facts["bounding_box"] = {
            k: bbox.get(k) for k in ("width", "depth", "height") if bbox.get(k) is not None
        }

    orientations = geometry.get("print_orientations")
    if isinstance(orientations, dict):
        facts["print_orientations"] = {
            "recommended": orientations.get("recommended"),
            "candidates": [
                {
                    "axis": o.get("axis_label"),
                    "overhang_ratio": o.get("overhang_ratio"),
                }
                for o in (orientations.get("orientations") or [])
                if isinstance(o, dict)
            ],
        }

    counts = {
        name: len(geometry[name])
        for name in ("faces", "edges", "holes", "bosses", "ribs", "cavities", "wall_samples")
        if isinstance(geometry.get(name), list)
    }
    if counts:
        facts["feature_counts"] = counts

    return facts


def summarise_failures(report: DFMReport) -> List[str]:
    """One line per failed rule — used by the deterministic answerer and as a
    compact fallback when the full context is not needed."""
    lines: List[str] = []
    for process in report.processes:
        for rule in process.rule_results:
            if rule.status != RuleStatus.failed:
                continue
            severity = rule.severity.value if rule.severity else "issue"
            lines.append(
                f"[{process.process.value}] {rule.rule_id} {rule.name} — {severity}: {rule.summary}"
            )
    return lines
