"""Loads the DFM YAML configuration once and hands it to the rule engine.

``load_dfm_config()`` is cached, so the YAML is read from disk exactly once per
process. FastAPI calls it during startup (see ``main.py`` lifespan) so a broken
config fails fast at boot rather than on the first upload, and the Celery worker
warms the same cache on first use.

Tests and the tuning workflow can pass explicit paths or call
``reload_dfm_config()`` after editing a file.
"""

from __future__ import annotations

import logging
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

logger = logging.getLogger(__name__)

CONFIG_DIR = Path(__file__).resolve().parent
THRESHOLDS_FILE = CONFIG_DIR / "thresholds.yaml"
SCORING_FILE = CONFIG_DIR / "scoring.yaml"


class ConfigError(RuntimeError):
    """Raised when the YAML config is missing, malformed, or incomplete."""


def _read_yaml(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        raise ConfigError(f"DFM config file not found: {path}")
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except yaml.YAMLError as exc:
        raise ConfigError(f"DFM config file {path.name} is not valid YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError(f"DFM config file {path.name} must contain a mapping at the top level.")
    return data


def _normalise_key(value: Optional[str]) -> Optional[str]:
    """Free-text user input ('ABS', 'Nylon PA66', 'POM / Acetal') -> table key.

    Any run of separators collapses to a single underscore so a user typing
    'POM / Acetal' lands on the same row as 'pom_acetal'.
    """
    if value is None:
        return None
    key = re.sub(r"[\s\-/\\_]+", "_", str(value).strip().lower()).strip("_")
    return key or None


class MaterialSpec:
    """One row of the injection-molding material table (Type 1 lookups)."""

    def __init__(self, key: str, data: Dict[str, Any]):
        self.key = key
        self.display_name: str = data.get("display_name", key.upper())
        self.material_class: str = data.get("class", "amorphous")
        self.wall_min_mm: Optional[float] = data.get("wall_min_mm")
        self.wall_max_mm: Optional[float] = data.get("wall_max_mm")
        self.tolerance_capability_mm: Optional[float] = data.get("tolerance_capability_mm")


class PrintingProcessSpec:
    """One row of the printing process table (Type 1 lookups)."""

    def __init__(self, key: str, data: Dict[str, Any]):
        self.key = key
        self.display_name: str = data.get("display_name", key.upper())
        # None means "this process needs no supports" (powder bed).
        self.overhang_limit_deg: Optional[float] = data.get("overhang_limit_deg")
        self.min_wall_mm: Optional[float] = data.get("min_wall_mm")
        self.safe_wall_multiplier: float = data.get("safe_wall_multiplier", 1.5)
        self.absolute_min_wall_mm: Optional[float] = data.get("absolute_min_wall_mm")
        self.min_pin_diameter_mm: Optional[float] = data.get("min_pin_diameter_mm")
        self.needs_supports: bool = bool(data.get("needs_supports", True))
        self.traps_material: bool = bool(data.get("traps_material", False))


class DFMConfig:
    """Parsed, validated view over thresholds.yaml + scoring.yaml."""

    def __init__(self, thresholds: Dict[str, Any], scoring: Dict[str, Any]):
        self._thresholds = thresholds
        self._scoring = scoring

        self.version: str = str(thresholds.get("version", "unknown"))
        self.scoring_version: str = str(scoring.get("version", "unknown"))

        self.defaults: Dict[str, Any] = thresholds.get("defaults", {}) or {}

        self._materials = {
            key: MaterialSpec(key, value)
            for key, value in (thresholds.get("materials") or {}).items()
        }
        self._material_aliases = {
            _normalise_key(k): _normalise_key(v)
            for k, v in (thresholds.get("material_aliases") or {}).items()
        }
        self._printing_processes = {
            key: PrintingProcessSpec(key, value)
            for key, value in (thresholds.get("printing_processes") or {}).items()
        }
        self._printing_aliases = {
            _normalise_key(k): _normalise_key(v)
            for k, v in (thresholds.get("printing_process_aliases") or {}).items()
        }
        self._rules: Dict[str, Dict[str, Any]] = thresholds.get("rules", {}) or {}

        self._validate()

    # -- validation --------------------------------------------------------

    def _validate(self) -> None:
        if not self._rules:
            raise ConfigError("thresholds.yaml defines no `rules:` block.")
        if not self._materials:
            raise ConfigError("thresholds.yaml defines no `materials:` table.")
        if not self._printing_processes:
            raise ConfigError("thresholds.yaml defines no `printing_processes:` table.")

        weights = self._scoring.get("severity_weights") or {}
        for tier in ("blocker", "major", "minor"):
            if tier not in weights:
                raise ConfigError(f"scoring.yaml is missing severity_weights.{tier}")

        blocker_mode = self.blocker_mode
        if blocker_mode not in ("cap", "zero", "deduct"):
            raise ConfigError(
                f"scoring.yaml blocker.mode must be cap|zero|deduct, got '{blocker_mode}'"
            )
        if self.rollup_mode not in ("deductive", "weighted"):
            raise ConfigError(
                f"scoring.yaml rollup.mode must be deductive|weighted, got '{self.rollup_mode}'"
            )

        default_process = _normalise_key(self.defaults.get("printing_process"))
        if default_process and default_process not in self._printing_processes:
            raise ConfigError(
                f"defaults.printing_process '{default_process}' is not in printing_processes."
            )

    # -- rule thresholds ---------------------------------------------------

    def rule(self, rule_id: str) -> Dict[str, Any]:
        """Threshold block for a rule id ('M1'), or {} when unconfigured."""
        return self._rules.get(rule_id.upper(), {}) or {}

    def rule_enabled(self, rule_id: str) -> bool:
        return bool(self.rule(rule_id).get("enabled", True))

    def rule_value(self, rule_id: str, key: str, default: Any = None) -> Any:
        return self.rule(rule_id).get(key, default)

    # -- material lookups (Type 1) ----------------------------------------

    def material(self, name: Optional[str]) -> Optional[MaterialSpec]:
        """Resolve free-text material input to a table row, or None."""
        key = _normalise_key(name)
        if key is None:
            return None
        key = self._material_aliases.get(key, key)
        return self._materials.get(key)

    @property
    def material_keys(self) -> List[str]:
        return sorted(self._materials)

    # -- printing process lookups (Type 1) --------------------------------

    def printing_process(self, name: Optional[str]) -> Optional[PrintingProcessSpec]:
        key = _normalise_key(name)
        if key is None:
            return None
        key = self._printing_aliases.get(key, key)
        return self._printing_processes.get(key)

    def default_printing_process(self) -> PrintingProcessSpec:
        spec = self.printing_process(self.defaults.get("printing_process"))
        if spec is None:  # pragma: no cover - guarded by _validate
            raise ConfigError("No usable default printing process configured.")
        return spec

    @property
    def printing_process_keys(self) -> List[str]:
        return sorted(self._printing_processes)

    # -- scoring -----------------------------------------------------------

    @property
    def start_score(self) -> float:
        return float(self._scoring.get("start_score", 100.0))

    def severity_weight(self, severity: str) -> float:
        return float((self._scoring.get("severity_weights") or {}).get(severity, 0.0))

    def rule_impact_cap(self, rule_id: str) -> float:
        block = self._scoring.get("per_rule_impact_cap") or {}
        overrides = block.get("overrides") or {}
        if rule_id.upper() in overrides:
            return float(overrides[rule_id.upper()])
        return float(block.get("default", float("inf")))

    @property
    def blocker_mode(self) -> str:
        return str((self._scoring.get("blocker") or {}).get("mode", "cap"))

    @property
    def blocker_cap_value(self) -> float:
        return float((self._scoring.get("blocker") or {}).get("cap_value", 25.0))

    @property
    def rollup_mode(self) -> str:
        return str((self._scoring.get("rollup") or {}).get("mode", "deductive"))

    @property
    def rollup_weights(self) -> Dict[str, float]:
        weights = (self._scoring.get("rollup") or {}).get("weights") or {}
        return {str(k): float(v) for k, v in weights.items()}

    @property
    def redesign_below(self) -> float:
        return float((self._scoring.get("verdict_thresholds") or {}).get("redesign_below", 30.0))

    @property
    def review_below(self) -> float:
        return float((self._scoring.get("verdict_thresholds") or {}).get("review_below", 50.0))

    def verdict_label(self, key: str) -> str:
        labels = self._scoring.get("verdict_labels") or {}
        return str(labels.get(key, key.replace("_", " ").title()))

    @property
    def confidence_assumption_penalty(self) -> float:
        return float((self._scoring.get("confidence") or {}).get("assumption_penalty", 0.05))

    @property
    def confidence_floor(self) -> float:
        return float((self._scoring.get("confidence") or {}).get("floor", 0.2))

    @property
    def recommendation_tie_margin(self) -> float:
        return float((self._scoring.get("recommendation") or {}).get("tie_margin", 5.0))

    @property
    def m4_blocker_printing_bonus(self) -> float:
        return float(
            (self._scoring.get("recommendation") or {}).get("m4_blocker_printing_bonus", 0.0)
        )

    # -- introspection -----------------------------------------------------

    def as_dict(self) -> Dict[str, Any]:
        """Raw config, for embedding in a report or debugging a tuning run."""
        return {"thresholds": self._thresholds, "scoring": self._scoring}


@lru_cache(maxsize=4)
def _load(thresholds_path: str, scoring_path: str) -> DFMConfig:
    config = DFMConfig(_read_yaml(Path(thresholds_path)), _read_yaml(Path(scoring_path)))
    logger.info(
        "DFM config loaded (thresholds v%s, scoring v%s, %d rules)",
        config.version,
        config.scoring_version,
        len(config._rules),
    )
    return config


def load_dfm_config(
    thresholds_path: Optional[Path] = None,
    scoring_path: Optional[Path] = None,
) -> DFMConfig:
    """Return the cached config, loading it on first call.

    Raises ``ConfigError`` if either file is missing or malformed — call this at
    application startup so that surfaces as a boot failure, not a 500 later.
    """
    return _load(
        str(thresholds_path or THRESHOLDS_FILE),
        str(scoring_path or SCORING_FILE),
    )


def reload_dfm_config() -> DFMConfig:
    """Drop the cache and re-read the YAML from disk (tuning / tests)."""
    _load.cache_clear()
    return load_dfm_config()


def capability_table(rows: Any) -> List[Tuple[Optional[float], float]]:
    """Normalise M7's ``capability_by_size_mm`` into (max_size, tolerance) pairs.

    A ``null`` size bound means "no upper limit" and must sort last.
    """
    table: List[Tuple[Optional[float], float]] = []
    for row in rows or []:
        if not isinstance(row, (list, tuple)) or len(row) != 2:
            continue
        size, tolerance = row
        table.append((None if size is None else float(size), float(tolerance)))
    table.sort(key=lambda item: (item[0] is None, item[0] if item[0] is not None else 0.0))
    return table
