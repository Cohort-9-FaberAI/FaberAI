"""Threshold/scoring YAML loading, lookups and validation."""

from __future__ import annotations

import pytest
import yaml

from dfm.config import ConfigError, DFMConfig, capability_table, load_dfm_config
from dfm.config.loader import _read_yaml


class TestLoading:
    def test_loads_both_files(self, config):
        assert config.version
        assert config.scoring_version
        assert config.start_score == 100.0

    def test_is_cached_across_calls(self):
        assert load_dfm_config() is load_dfm_config()

    def test_every_rule_has_a_threshold_block(self, config):
        for rule_id in ("M1", "M2", "M3", "M4", "M5", "M6", "M7",
                        "P1", "P2", "P3", "P4", "P5", "P6"):
            assert config.rule(rule_id), f"{rule_id} has no thresholds configured"
            assert config.rule_enabled(rule_id)


class TestMaterialLookup:
    def test_known_material(self, config):
        abs_spec = config.material("ABS")
        assert abs_spec is not None
        assert abs_spec.wall_min_mm == 1.5
        assert abs_spec.material_class == "amorphous"

    def test_alias_resolves(self, config):
        assert config.material("Nylon").key == "pa66"
        assert config.material("polypropylene").key == "pp"

    def test_free_text_is_normalised(self, config):
        assert config.material("  POM / Acetal ") is not None

    def test_unknown_material_returns_none(self, config):
        assert config.material("unobtanium") is None
        assert config.material(None) is None

    def test_semi_crystalline_classification(self, config):
        assert config.material("PP").material_class == "semi_crystalline"
        assert config.material("PC").material_class == "amorphous"


class TestPrintingProcessLookup:
    def test_known_processes(self, config):
        assert config.printing_process("FDM").min_wall_mm == 1.0
        assert config.printing_process("SLA").min_wall_mm == 0.4

    def test_powder_bed_needs_no_supports(self, config):
        for name in ("sls", "mjf"):
            spec = config.printing_process(name)
            assert spec.overhang_limit_deg is None
            assert spec.needs_supports is False
            assert spec.traps_material is True

    def test_default_is_the_most_restrictive_case(self, config):
        assert config.default_printing_process().key == "fdm"

    def test_alias_resolves(self, config):
        assert config.printing_process("resin").key == "sla"


class TestScoringAccessors:
    def test_severity_weights(self, config):
        assert config.severity_weight("major") > config.severity_weight("minor")

    def test_rule_impact_cap_has_a_default(self, config):
        assert config.rule_impact_cap("M1") == config.rule_impact_cap("P3")

    def test_blocker_defaults_to_capping(self, config):
        assert config.blocker_mode == "cap"
        assert config.blocker_cap_value < config.redesign_below


class TestValidation:
    def _config_with(self, tmp_path, thresholds_patch=None, scoring_patch=None):
        from dfm.config.loader import SCORING_FILE, THRESHOLDS_FILE

        thresholds = _read_yaml(THRESHOLDS_FILE)
        scoring = _read_yaml(SCORING_FILE)
        if thresholds_patch:
            thresholds_patch(thresholds)
        if scoring_patch:
            scoring_patch(scoring)
        return thresholds, scoring

    def test_rejects_missing_severity_weight(self, tmp_path):
        thresholds, scoring = self._config_with(
            tmp_path, scoring_patch=lambda s: s["severity_weights"].pop("major")
        )
        with pytest.raises(ConfigError, match="severity_weights.major"):
            DFMConfig(thresholds, scoring)

    def test_rejects_unknown_blocker_mode(self, tmp_path):
        thresholds, scoring = self._config_with(
            tmp_path, scoring_patch=lambda s: s["blocker"].update({"mode": "explode"})
        )
        with pytest.raises(ConfigError, match="blocker.mode"):
            DFMConfig(thresholds, scoring)

    def test_rejects_default_process_not_in_table(self, tmp_path):
        thresholds, scoring = self._config_with(
            tmp_path,
            thresholds_patch=lambda t: t["defaults"].update({"printing_process": "laser"}),
        )
        with pytest.raises(ConfigError, match="printing_processes"):
            DFMConfig(thresholds, scoring)

    def test_rejects_missing_file(self, tmp_path):
        with pytest.raises(ConfigError, match="not found"):
            _read_yaml(tmp_path / "nope.yaml")

    def test_rejects_malformed_yaml(self, tmp_path):
        bad = tmp_path / "bad.yaml"
        bad.write_text("rules: [unclosed", encoding="utf-8")
        with pytest.raises(ConfigError, match="not valid YAML"):
            _read_yaml(bad)


class TestCapabilityTable:
    def test_null_upper_bound_sorts_last(self):
        table = capability_table([[100.0, 0.25], [None, 0.8], [10.0, 0.1]])
        assert table[0][0] == 10.0
        assert table[-1][0] is None

    def test_ignores_malformed_rows(self):
        assert capability_table([[10.0, 0.1], "nonsense", [1, 2, 3]]) == [(10.0, 0.1)]


def test_yaml_files_are_parseable_standalone():
    """Guards against a tuning edit that breaks the file for other tools."""
    from dfm.config.loader import SCORING_FILE, THRESHOLDS_FILE

    for path in (THRESHOLDS_FILE, SCORING_FILE):
        with path.open(encoding="utf-8") as handle:
            assert isinstance(yaml.safe_load(handle), dict)
