"""3D printing rules P1–P6. Every check is orientation-relative."""

from __future__ import annotations

import copy

from dfm.context import build_context
from dfm.inputs import DFMInputs
from dfm.models import RuleStatus, Severity
from dfm.rules.printing import (
    AspectRatioRule,
    BuildEnvelopeRule,
    MinimumFeatureSizeRule,
    OverhangAngleRule,
    SupportVolumeRule,
    TrappedVolumeRule,
)


def run_rule(rule_class, config, geometry, inputs=None):
    context = build_context(geometry, inputs or DFMInputs(), config)
    return rule_class(config).run(context)


def set_wall_field(geometry, values):
    geometry["wall_samples"] = []
    geometry["wall_thickness_stats"] = {
        "minimum_wall": min(values), "maximum_wall": max(values),
        "mean_wall": sum(values) / len(values),
        "median_wall": sorted(values)[len(values) // 2],
        "wall_thickness_field": list(values),
    }
    return geometry


# ---------------------------------------------------------------------------
# P1
# ---------------------------------------------------------------------------

class TestP1Overhang:
    def test_flags_faces_past_45_degrees_on_fdm(self, config, stl_geometry):
        # A face normal 150° from the build axis is 60° from vertical.
        result = run_rule(OverhangAngleRule, config, stl_geometry)
        assert result.status == RuleStatus.failed
        assert result.severity == Severity.major
        assert result.thresholds_used["overhang_limit_deg"] == 45.0

    def test_vertical_and_upward_faces_never_overhang(self, config, stl_geometry):
        stl_geometry["print_orientations"]["orientations"][0]["face_angles"] = {
            0: 90.0, 1: 45.0, 2: 0.0,
        }
        result = run_rule(OverhangAngleRule, config, stl_geometry)
        assert result.status == RuleStatus.passed

    def test_135_degrees_is_exactly_the_limit(self, config, stl_geometry):
        # 135° to the build axis == 45° from vertical == at the limit, not past it.
        stl_geometry["print_orientations"]["orientations"][0]["face_angles"] = {0: 135.0}
        result = run_rule(OverhangAngleRule, config, stl_geometry)
        assert result.status == RuleStatus.passed

    def test_suppressed_for_powder_bed_processes(self, config, stl_geometry):
        for process in ("sls", "mjf"):
            result = run_rule(
                OverhangAngleRule, config, stl_geometry,
                DFMInputs(printing_process=process),
            )
            assert result.status == RuleStatus.suppressed
            assert result.score_impact == 0.0

    def test_defaults_to_fdm_and_states_the_assumption(self, config, stl_geometry):
        result = run_rule(OverhangAngleRule, config, stl_geometry)
        assert result.thresholds_used["printing_process"] == "fdm"
        assert any("most restrictive" in a for a in result.assumptions)

    def test_measured_against_the_recommended_orientation(self, config, step_geometry):
        # +Z is recommended and has no overhangs; -Z has 33%.
        result = run_rule(OverhangAngleRule, config, step_geometry)
        assert result.thresholds_used["build_orientation"] == "+Z"
        assert result.status == RuleStatus.passed

    def test_user_can_force_an_orientation(self, config, step_geometry):
        result = run_rule(
            OverhangAngleRule, config, step_geometry, DFMInputs(build_orientation="-Z")
        )
        assert result.thresholds_used["build_orientation"] == "-Z"
        assert result.status == RuleStatus.failed


# ---------------------------------------------------------------------------
# P2
# ---------------------------------------------------------------------------

class TestP2MinimumFeatureSize:
    def test_below_process_minimum_is_a_blocker(self, config, stl_geometry):
        result = run_rule(MinimumFeatureSizeRule, config, stl_geometry)
        assert result.status == RuleStatus.failed
        assert result.severity == Severity.blocker

    def test_sla_resolves_what_fdm_cannot(self, config, stl_geometry):
        result = run_rule(
            MinimumFeatureSizeRule, config, stl_geometry, DFMInputs(printing_process="SLA")
        )
        # 0.6 mm clears SLA's 0.4 mm minimum but sits inside the 1.5x fragile band.
        assert result.severity == Severity.major

    def test_passes_above_the_safe_target(self, config, stl_geometry):
        set_wall_field(stl_geometry, [1.8, 2.0, 2.2, 2.5])
        result = run_rule(MinimumFeatureSizeRule, config, stl_geometry)
        assert result.status == RuleStatus.passed

    def test_single_thin_sample_is_treated_as_noise(self, config, stl_geometry):
        set_wall_field(stl_geometry, [0.2] + [2.0] * 400)
        result = run_rule(MinimumFeatureSizeRule, config, stl_geometry)
        assert result.status == RuleStatus.passed

    def test_flags_pins_below_the_minimum_diameter(self, config, stl_geometry):
        set_wall_field(stl_geometry, [2.0, 2.1, 2.2])
        stl_geometry["bosses"] = [
            {"id": 1, "outer_diameter": 1.0, "height": 8.0, "is_solid": True, "faces": []}
        ]
        result = run_rule(MinimumFeatureSizeRule, config, stl_geometry)
        assert result.status == RuleStatus.failed
        assert any("Pin/boss" in f.message for f in result.findings)

    def test_not_assessed_without_wall_data(self, config, empty_geometry):
        result = run_rule(MinimumFeatureSizeRule, config, empty_geometry)
        assert result.status == RuleStatus.not_assessed


# ---------------------------------------------------------------------------
# P3
# ---------------------------------------------------------------------------

class TestP3SupportVolume:
    def test_flags_heavy_support_demand(self, config, stl_geometry):
        stl_geometry["print_orientations"]["orientations"][0]["overhang_ratio"] = 0.5
        result = run_rule(SupportVolumeRule, config, stl_geometry)
        assert result.status == RuleStatus.failed
        assert result.severity == Severity.major

    def test_modest_support_is_minor(self, config, stl_geometry):
        result = run_rule(SupportVolumeRule, config, stl_geometry)   # 0.25 ratio
        assert result.severity == Severity.minor

    def test_passes_when_little_overhangs(self, config, stl_geometry):
        stl_geometry["print_orientations"]["orientations"][0]["overhang_ratio"] = 0.05
        result = run_rule(SupportVolumeRule, config, stl_geometry)
        assert result.status == RuleStatus.passed

    def test_volume_is_labelled_an_estimate(self, config, stl_geometry):
        result = run_rule(SupportVolumeRule, config, stl_geometry)
        assert result.thresholds_used["support_volume_is_estimate"] is True
        assert result.thresholds_used["support_volume_mm3"] is not None

    def test_prefers_a_geometry_supplied_volume(self, config, stl_geometry):
        stl_geometry["print_orientations"]["orientations"][0]["support_volume_mm3"] = 1234.0
        result = run_rule(SupportVolumeRule, config, stl_geometry)
        assert result.thresholds_used["support_volume_mm3"] == 1234.0
        assert result.thresholds_used["support_volume_is_estimate"] is False

    def test_suppressed_for_powder_bed(self, config, stl_geometry):
        result = run_rule(
            SupportVolumeRule, config, stl_geometry, DFMInputs(printing_process="sls")
        )
        assert result.status == RuleStatus.suppressed

    def test_suggests_a_better_orientation_when_one_exists(self, config, step_geometry):
        result = run_rule(
            SupportVolumeRule, config, step_geometry, DFMInputs(build_orientation="-Z")
        )
        assert result.status == RuleStatus.failed
        assert "+Z" in result.findings[0].recommendation


# ---------------------------------------------------------------------------
# P4
# ---------------------------------------------------------------------------

class TestP4AspectRatio:
    def test_tall_thin_part_is_major(self, config, stl_geometry):
        result = run_rule(AspectRatioRule, config, stl_geometry)   # 180 / 20 = 9:1
        assert result.status == RuleStatus.failed
        assert result.severity == Severity.major

    def test_stable_part_passes(self, config, step_geometry):
        result = run_rule(AspectRatioRule, config, step_geometry)   # 40 / 60
        assert result.status == RuleStatus.passed

    def test_short_parts_are_exempt(self, config, stl_geometry):
        stl_geometry["bounding_box"] = {
            "min": {"x": 0, "y": 0, "z": 0}, "max": {"x": 2, "y": 2, "z": 15},
            "width": 2.0, "depth": 2.0, "height": 15.0,
        }
        result = run_rule(AspectRatioRule, config, stl_geometry)
        assert result.status == RuleStatus.passed

    def test_ratio_follows_the_build_orientation(self, config, stl_geometry):
        # Laid on its side, the 180 mm dimension becomes footprint, not height.
        result = run_rule(
            AspectRatioRule, config, stl_geometry, DFMInputs(build_orientation="+X")
        )
        assert result.status == RuleStatus.passed
        assert result.thresholds_used["height_mm"] == 30.0

    def test_not_assessed_without_a_bounding_box(self, config, empty_geometry):
        result = run_rule(AspectRatioRule, config, empty_geometry)
        assert result.status == RuleStatus.not_assessed


# ---------------------------------------------------------------------------
# P5
# ---------------------------------------------------------------------------

class TestP5TrappedVolumes:
    def test_enclosed_cavity_is_major_on_resin(self, config, stl_geometry):
        result = run_rule(
            TrappedVolumeRule, config, stl_geometry, DFMInputs(printing_process="sla")
        )
        assert result.status == RuleStatus.failed
        assert result.severity == Severity.major
        assert "resin" in result.findings[0].message

    def test_enclosed_cavity_is_major_on_powder(self, config, stl_geometry):
        result = run_rule(
            TrappedVolumeRule, config, stl_geometry, DFMInputs(printing_process="mjf")
        )
        assert result.severity == Severity.major
        assert "powder" in result.findings[0].message

    def test_suppressed_on_fdm_which_traps_nothing(self, config, stl_geometry):
        result = run_rule(TrappedVolumeRule, config, stl_geometry)
        assert result.status == RuleStatus.suppressed
        assert result.score_impact == 0.0

    def test_cavity_with_an_opening_is_not_trapped(self, config, stl_geometry):
        stl_geometry["cavities"][0].update({"opening_face": 12, "opening_area": 30.0})
        result = run_rule(
            TrappedVolumeRule, config, stl_geometry, DFMInputs(printing_process="sla")
        )
        assert result.status == RuleStatus.passed

    def test_explicit_is_enclosed_flag_wins(self, config, stl_geometry):
        stl_geometry["cavities"][0].update(
            {"opening_face": 12, "opening_area": 30.0, "is_enclosed": True}
        )
        result = run_rule(
            TrappedVolumeRule, config, stl_geometry, DFMInputs(printing_process="sla")
        )
        assert result.status == RuleStatus.failed

    def test_uses_dedicated_trapped_volumes_array_when_present(self, config, stl_geometry):
        stl_geometry["cavities"] = []
        stl_geometry["trapped_volumes"] = [
            {"id": 7, "volume": 400.0, "depth": 10.0, "is_enclosed": True}
        ]
        result = run_rule(
            TrappedVolumeRule, config, stl_geometry, DFMInputs(printing_process="sla")
        )
        assert result.status == RuleStatus.failed
        assert result.thresholds_used["source"] == "trapped_volumes"

    def test_tiny_voids_are_ignored(self, config, stl_geometry):
        stl_geometry["cavities"][0]["volume"] = 1.0
        result = run_rule(
            TrappedVolumeRule, config, stl_geometry, DFMInputs(printing_process="sla")
        )
        assert result.status == RuleStatus.passed


# ---------------------------------------------------------------------------
# P6
# ---------------------------------------------------------------------------

class TestP6BuildEnvelope:
    def test_part_that_fits_passes(self, config, stl_geometry):
        result = run_rule(BuildEnvelopeRule, config, stl_geometry)
        assert result.status == RuleStatus.passed

    def test_uses_and_states_the_default_envelope(self, config, stl_geometry):
        result = run_rule(BuildEnvelopeRule, config, stl_geometry)
        assert result.thresholds_used["envelope_mm"] == [250.0, 210.0, 220.0]
        assert any("No printer envelope supplied" in a for a in result.assumptions)

    def test_oversized_part_is_a_blocker(self, config, stl_geometry):
        result = run_rule(
            BuildEnvelopeRule, config, stl_geometry,
            DFMInputs(build_envelope_mm=[100.0, 100.0, 100.0], printer_name="Mini"),
        )
        assert result.status == RuleStatus.failed
        assert result.severity == Severity.blocker
        assert result.thresholds_used["fits_in_some_orientation"] is False

    def test_fits_only_in_another_orientation_is_major_not_blocker(self, config, stl_geometry):
        # 180 mm tall does not fit a 100 mm Z, but lying down it fits the bed.
        result = run_rule(
            BuildEnvelopeRule, config, stl_geometry,
            DFMInputs(build_envelope_mm=[250.0, 210.0, 100.0]),
        )
        assert result.status == RuleStatus.failed
        assert result.severity == Severity.major
        assert result.thresholds_used["fits_in_some_orientation"] is True
        assert result.thresholds_used["fits_in_build_orientation"] is False

    def test_clearance_is_applied(self, config, stl_geometry):
        result = run_rule(BuildEnvelopeRule, config, stl_geometry)
        usable = result.thresholds_used["usable_envelope_mm"]
        envelope = result.thresholds_used["envelope_mm"]
        assert all(u == e - 5.0 for u, e in zip(usable, envelope))

    def test_not_assessed_without_a_bounding_box(self, config, empty_geometry):
        result = run_rule(BuildEnvelopeRule, config, empty_geometry)
        assert result.status == RuleStatus.not_assessed


def test_every_printing_rule_survives_empty_geometry(config, empty_geometry):
    from dfm.rules.printing import PRINTING_RULES

    for rule_class in PRINTING_RULES:
        result = run_rule(rule_class, config, copy.deepcopy(empty_geometry))
        assert result.status in (RuleStatus.not_assessed, RuleStatus.suppressed), (
            f"{rule_class.__name__} returned {result.status}"
        )
        assert result.score_impact == 0.0
