"""FaberAI DFM rule engine.

Sits downstream of the geometry engine: it consumes measurements, never
produces them. One evaluator class per rule, grouped by manufacturing process,
with every threshold and scoring weight read from YAML at startup.

    from dfm import DFMInputs, run_dfm_analysis

    report = run_dfm_analysis(geometry_results_json, DFMInputs(material="ABS"))
"""

from .config import DFMConfig, load_dfm_config, reload_dfm_config
from .engine import run_dfm_analysis
from .inputs import DFMInputs, ToleranceRequest
from .models import (
    DFMReport,
    Finding,
    ProcessReport,
    ProcessType,
    RuleResult,
    RuleStatus,
    Severity,
    SubScore,
)

__all__ = [
    "DFMConfig",
    "DFMInputs",
    "DFMReport",
    "Finding",
    "ProcessReport",
    "ProcessType",
    "RuleResult",
    "RuleStatus",
    "Severity",
    "SubScore",
    "ToleranceRequest",
    "load_dfm_config",
    "reload_dfm_config",
    "run_dfm_analysis",
]
