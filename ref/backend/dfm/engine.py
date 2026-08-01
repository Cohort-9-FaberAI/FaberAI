"""The DFM rule engine entry point.

Pipeline position::

    CAD upload -> Geometry Engine -> results_json -> [DFM RULE ENGINE]
        -> Manufacturability Report -> AI endpoint

``run_dfm_analysis`` is the only function callers need. It consumes geometry
output and optional user context, runs the rule-set for each requested process,
scores the results and returns a ``DFMReport``. It performs no geometry work of
its own and never raises for a bad part — a part it cannot assess comes back as
a report full of "Not assessed", not an exception.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from .config import DFMConfig, load_dfm_config
from .context import EvaluationContext, build_context
from .geometry_contract import GeometryInput
from .inputs import DFMInputs
from .models import (
    DFMReport,
    PartSummary,
    ProcessReport,
    ProcessType,
    RuleResult,
)
from .rules import rules_for
from .scoring import ScoringEngine

logger = logging.getLogger(__name__)


def run_dfm_analysis(
    geometry_payload: object,
    inputs: Optional[DFMInputs] = None,
    config: Optional[DFMConfig] = None,
    analysis_id: Optional[str] = None,
) -> DFMReport:
    """Evaluate a part and return its manufacturability report.

    Args:
        geometry_payload: The geometry engine output — a ``GeometryEngineResponse``,
            its ``model_dump()``, or any dict of the same shape.
        inputs: Optional user context (material, printer, tolerances...). Every
            field is optional and a missing field never costs the user points.
        config: Loaded YAML config. Defaults to the process-wide cached config.
        analysis_id: Analysis record this report belongs to, for traceability.
    """
    config = config or load_dfm_config()
    context = build_context(geometry_payload, inputs, config)
    scorer = ScoringEngine(config)

    report = DFMReport(
        config_version=f"thresholds {config.version} / scoring {config.scoring_version}",
        analysis_id=analysis_id,
        part=_part_summary(context),
        inputs=context.input_echo(),
        warnings=_input_warnings(context),
    )

    process_reports: List[ProcessReport] = []
    for process in context.inputs.processes_to_evaluate():
        process_reports.append(_evaluate_process(process, context, scorer))

    report.processes = process_reports
    report.recommendation = scorer.recommend_process(process_reports)

    headline = _headline_report(report, context)
    if headline is not None:
        report.manufacturable = headline.manufacturable
        report.manufacturability_score = headline.score

    return report


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------

def _evaluate_process(
    process: ProcessType,
    context: EvaluationContext,
    scorer: ScoringEngine,
) -> ProcessReport:
    """Run every rule registered for a process and score the outcome."""
    results: List[RuleResult] = []
    for rule_class in rules_for(process):
        evaluator = rule_class(context.config)
        results.append(evaluator.run(context))

    # Process-level assumptions are the union of what the rules assumed, so the
    # report can state its footing in one place.
    assumptions = [assumption for result in results for assumption in result.assumptions]

    orientation = context.build_axis if process == ProcessType.printing else None
    return scorer.score_process(
        process=process,
        rule_results=results,
        assumptions=assumptions,
        orientation_assumed=orientation,
    )


def _part_summary(context: EvaluationContext) -> PartSummary:
    """Geometry facts copied verbatim, so the AI layer never has to guess."""
    geometry: GeometryInput = context.geometry
    stats = geometry.wall_thickness_stats
    wall_field = geometry.wall_field()

    minimum = stats.minimum_wall if stats and stats.minimum_wall else None
    maximum = stats.maximum_wall if stats and stats.maximum_wall else None
    if minimum is None and wall_field:
        minimum = min(wall_field)
    if maximum is None and wall_field:
        maximum = max(wall_field)

    extents = geometry.bbox_extents()
    return PartSummary(
        filename=geometry.filename,
        source_format=geometry.source_format,
        volume_mm3=geometry.volume_mm3,
        surface_area_mm2=geometry.surface_area_mm2,
        bounding_box_mm=[round(e, 3) for e in extents] if extents else None,
        nominal_wall_mm=context.nominal_wall(),
        min_wall_mm=minimum,
        max_wall_mm=maximum,
        face_count=len(geometry.faces),
        measurements_reliable=geometry.measurements_reliable,
    )


def _input_warnings(context: EvaluationContext) -> List[str]:
    """Problems with the *input* rather than the design.

    These are stated separately from findings so an unreliable mesh reads as
    "we could not measure this properly", not "your part is badly designed".
    """
    warnings: List[str] = []
    geometry = context.geometry

    if not geometry.measurements_reliable:
        warnings.append(
            "The geometry engine flagged this part's measurements as unreliable (the mesh could "
            "not be fully repaired). Volume-derived results should be treated as indicative."
        )

    quality = geometry.mesh_quality
    if quality is not None:
        if quality.is_watertight is False:
            warnings.append(
                "The mesh is not watertight, so wall thickness and internal cavity results are "
                "approximate."
            )
        if quality.is_winding_consistent is False:
            warnings.append(
                "The mesh has inconsistent triangle winding, which can invert face normals and "
                "distort overhang and draft angles."
            )

    if not geometry.wall_field():
        warnings.append(
            "No wall thickness samples were available: every wall-based check "
            "(M1, M2, M5, M6, P2) reported Not assessed."
        )
    if not geometry.faces and geometry.print_orientations is None:
        warnings.append(
            "No per-face topology was available: draft angle and overhang checks could not run."
        )
    if geometry.ribs is None or geometry.bosses is None:
        warnings.append(
            "Rib and/or boss feature recognition was not present in the geometry output, so "
            "M5/M6 reported Not assessed rather than counting against the part."
        )

    return warnings


def _headline_report(
    report: DFMReport, context: EvaluationContext
) -> Optional[ProcessReport]:
    """Which process the top-level manufacturable/score fields describe.

    The process the user asked about, or the recommended one when they asked
    for a comparison. Falls back to the best-scoring report so the headline is
    never empty.
    """
    if context.inputs.process is not None:
        return report.process_report(context.inputs.process)
    recommended = report.recommendation.recommended_process
    if recommended is not None:
        return report.process_report(recommended)
    if report.processes:
        return max(report.processes, key=lambda r: (r.manufacturable, r.score))
    return None
