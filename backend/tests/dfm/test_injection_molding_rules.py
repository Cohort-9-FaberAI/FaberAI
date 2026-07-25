"""Injection molding rules M1–M7."""

from __future__ import annotations

import copy

import pytest

from dfm.context import build_context
from dfm.inputs import DFMInputs, ToleranceRequest
from dfm.models import RuleStatus, Severity
from dfm.rules.injection_molding import (
    BossDesignRule,
    DraftAngleRule,
    RibThicknessRule,
    ToleranceFeasibilityRule,
    UndercutRule,
    WallThicknessRule,
    WallUniformityRule,
)


def run_rule(rule_class, config, geometry, inputs=None):
    context = build_context(geometry, inputs or DFMInputs(), config)
    return rule_class(config).run(context)


def set_wall(geometry, samples):
    """Replace the wall thickness field with (face_id, thickness) pairs."""
    geometry["wall_samples"] = [
        {"id": index, "point": {"x": 0, "y": 0, "z": 0},
         "normal": {"x": 1, "y": 0, "z": 0}, "thickness": thickness,
         "face_id": face_id, "ray_length": thickness, "reliable": True}
        for index, (face_id, thickness) in enumerate(samples)
    ]
    values = [thickness for _face, thickness in samples]
    geometry["wall_thickness_stats"] = {
        "minimum_wall": min(values), "maximum_wall": max(values),
        "mean_wall": sum(values) / len(values),
        "median_wall": sorted(values)[len(values) // 2],
        "wall_thickness_field": values,
    }
    return geometry


# ---------------------------------------------------------------------------
# M1
# ---------------------------------------------------------------------------

class TestM1WallThickness:
    def test_passes_on_uniform_in_range_walls(self, config, step_geometry):
        result = run_rule(WallThicknessRule, config, step_geometry, DFMInputs(material="ABS"))
        assert result.status == RuleStatus.passed

    def test_below_material_minimum_is_a_blocker(self, config, step_geometry):
        set_wall(step_geometry, [(1, 0.9), (1, 0.95), (2, 1.0)])
        result = run_rule(WallThicknessRule, config, step_geometry, DFMInputs(material="ABS"))
        assert result.status == RuleStatus.failed
        assert result.severity == Severity.blocker
        assert result.thresholds_used["min_wall_mm"] == 1.5

    def test_uses_generic_floor_and_states_it_when_no_material(self, config, step_geometry):
        set_wall(step_geometry, [(1, 1.2), (2, 1.25)])
        result = run_rule(WallThicknessRule, config, step_geometry)
        # 1.2 mm passes the 0.8 mm generic floor but would fail ABS's 1.5 mm —
        # a blank material field must not penalise the user.
        assert result.status == RuleStatus.passed
        assert any("No material supplied" in a for a in result.assumptions)
        assert result.thresholds_used["min_wall_mm"] == 0.8

    def test_above_material_maximum_is_major(self, config, step_geometry):
        set_wall(step_geometry, [(1, 6.0), (1, 6.1), (2, 6.0)])
        result = run_rule(WallThicknessRule, config, step_geometry, DFMInputs(material="ABS"))
        assert result.status == RuleStatus.failed
        assert result.severity == Severity.major

    def test_neighbour_rule_catches_locally_thin_wall(self, config, step_geometry):
        # 1.6 mm passes ABS's absolute minimum but is only 40% of its 4 mm
        # neighbour — the spec's "thin is not judged in isolation" case.
        set_wall(step_geometry, [(1, 1.6), (2, 4.0), (3, 4.0)])
        result = run_rule(WallThicknessRule, config, step_geometry, DFMInputs(material="ABS"))
        assert result.status == RuleStatus.failed
        assert any("adjacent wall" in f.message for f in result.findings)

    def test_not_assessed_without_wall_samples(self, config, empty_geometry):
        result = run_rule(WallThicknessRule, config, empty_geometry)
        assert result.status == RuleStatus.not_assessed
        assert "wall_samples" in result.missing_inputs


# ---------------------------------------------------------------------------
# M2
# ---------------------------------------------------------------------------

class TestM2WallUniformity:
    def test_passes_on_uniform_walls(self, config, step_geometry):
        result = run_rule(WallUniformityRule, config, step_geometry, DFMInputs(material="ABS"))
        assert result.status == RuleStatus.passed

    def test_semi_crystalline_gets_the_tighter_band(self, config, step_geometry):
        result = run_rule(WallUniformityRule, config, step_geometry, DFMInputs(material="PP"))
        assert result.thresholds_used["variation_band"] == 0.15

    def test_amorphous_band_is_the_no_material_default(self, config, step_geometry):
        result = run_rule(WallUniformityRule, config, step_geometry)
        assert result.thresholds_used["variation_band"] == 0.25
        assert any("amorphous" in a for a in result.assumptions)

    def test_flags_variation_beyond_band(self, config, step_geometry):
        set_wall(step_geometry, [(1, 1.0), (1, 1.1), (2, 4.0), (2, 4.2), (3, 3.0)])
        step_geometry["nominal_wall"] = 3.0
        result = run_rule(WallUniformityRule, config, step_geometry, DFMInputs(material="ABS"))
        assert result.status == RuleStatus.failed

    def test_flags_abrupt_transition_beyond_taper(self, config, step_geometry):
        # 1.0 next to 5.0 is a 5:1 step, past the 3:1 taper limit.
        set_wall(step_geometry, [(1, 1.0), (2, 5.0), (3, 3.0)])
        step_geometry["nominal_wall"] = 3.0
        result = run_rule(WallUniformityRule, config, step_geometry, DFMInputs(material="ABS"))
        assert result.status == RuleStatus.failed
        assert any("transition" in f.message for f in result.findings)
        assert result.thresholds_used["abrupt_transitions"] >= 1


# ---------------------------------------------------------------------------
# M3
# ---------------------------------------------------------------------------

class TestM3DraftAngle:
    def test_passes_when_faces_carry_enough_draft(self, config, step_geometry):
        result = run_rule(DraftAngleRule, config, step_geometry)
        assert result.status == RuleStatus.passed

    def test_flags_undrafted_vertical_faces(self, config, step_geometry):
        orientation = step_geometry["print_orientations"]["orientations"][0]
        orientation["face_angles"] = {1: 90.0, 2: 89.8, 3: 0.0}
        result = run_rule(DraftAngleRule, config, step_geometry)
        assert result.status == RuleStatus.failed
        # Under 0.5° is a near-certain problem at any finish.
        assert result.severity == Severity.major

    def test_severity_softens_when_finish_was_assumed(self, config, step_geometry):
        orientation = step_geometry["print_orientations"]["orientations"][0]
        orientation["face_angles"] = {1: 89.3, 2: 90.7, 3: 0.0}   # 0.7° draft
        assumed = run_rule(DraftAngleRule, config, step_geometry)
        supplied = run_rule(
            DraftAngleRule, config, step_geometry, DFMInputs(surface_finish="semi_gloss")
        )
        assert assumed.severity == Severity.minor
        assert supplied.severity == Severity.major
        assert any("No surface finish supplied" in a for a in assumed.assumptions)

    def test_polished_finish_lowers_the_requirement(self, config, step_geometry):
        orientation = step_geometry["print_orientations"]["orientations"][0]
        orientation["face_angles"] = {1: 89.4, 2: 90.6, 3: 0.0}   # 0.6° draft
        result = run_rule(
            DraftAngleRule, config, step_geometry, DFMInputs(surface_finish="polished")
        )
        assert result.status == RuleStatus.passed
        assert result.thresholds_used["minimum_draft_deg"] == 0.5

    def test_top_faces_are_not_treated_as_vertical(self, config, step_geometry):
        result = run_rule(DraftAngleRule, config, step_geometry)
        assert result.thresholds_used["vertical_faces_checked"] == 2

    def test_not_assessed_without_face_angles(self, config, empty_geometry):
        result = run_rule(DraftAngleRule, config, empty_geometry)
        assert result.status == RuleStatus.not_assessed


# ---------------------------------------------------------------------------
# M4
# ---------------------------------------------------------------------------

class TestM4Undercuts:
    def test_not_assessed_when_geometry_supplies_nothing(self, config, step_geometry):
        result = run_rule(UndercutRule, config, step_geometry)
        assert result.status == RuleStatus.not_assessed
        assert "undercuts" in result.missing_inputs

    def test_uses_detection_results_when_present(self, config, step_geometry):
        step_geometry["undercuts"] = [
            {"id": 1, "face_ids": [1], "requires_side_action": True, "releasable": True},
        ]
        result = run_rule(UndercutRule, config, step_geometry)
        assert result.status == RuleStatus.failed
        assert result.severity == Severity.major

    def test_unreleasable_undercut_is_a_blocker(self, config, step_geometry):
        step_geometry["undercuts"] = [
            {"id": 1, "face_ids": [1], "releasable": False},
        ]
        result = run_rule(UndercutRule, config, step_geometry)
        assert result.severity == Severity.blocker

    def test_empty_detection_array_passes(self, config, step_geometry):
        step_geometry["undercuts"] = []
        result = run_rule(UndercutRule, config, step_geometry)
        assert result.status == RuleStatus.passed

    def test_infers_side_action_from_off_axis_hole(self, config, step_geometry):
        step_geometry["holes"] = [{
            "id": 1, "type": "through", "diameter": 6.0, "depth": 20.0,
            "axis": {"x": 1, "y": 0, "z": 0}, "center": {"x": 50, "y": 30, "z": 20},
            "through": True, "cylindrical_faces": [1],
        }]
        result = run_rule(UndercutRule, config, step_geometry)
        assert result.status == RuleStatus.failed
        # An inference must never escalate to a Blocker.
        assert result.severity == Severity.major
        assert any("not yet available" in a for a in result.assumptions)

    def test_axial_hole_needs_no_side_action(self, config, step_geometry):
        step_geometry["holes"] = [{
            "id": 1, "type": "through", "diameter": 6.0, "depth": 20.0,
            "axis": {"x": 0, "y": 0, "z": 1}, "center": {"x": 50, "y": 30, "z": 20},
            "through": True, "cylindrical_faces": [1],
        }]
        result = run_rule(UndercutRule, config, step_geometry)
        assert result.status == RuleStatus.passed


# ---------------------------------------------------------------------------
# M5 / M6 — the mocked rib and boss arrays
# ---------------------------------------------------------------------------

class TestM5RibRatio:
    def test_not_assessed_when_ribs_array_is_absent(self, config, geometry_without_features):
        result = run_rule(RibThicknessRule, config, geometry_without_features)
        assert result.status == RuleStatus.not_assessed
        assert result.missing_inputs == ["ribs"]
        assert result.score_impact == 0.0

    def test_empty_ribs_array_passes(self, config, step_geometry):
        result = run_rule(RibThicknessRule, config, step_geometry)
        assert result.status == RuleStatus.passed

    def test_mocked_rib_within_guideline_passes(self, config, step_geometry_with_features):
        # 1.5 mm rib on a 3 mm wall = 50%, at the boundary and not over it.
        result = run_rule(RibThicknessRule, config, step_geometry_with_features)
        assert result.status == RuleStatus.passed

    def test_rib_over_60_percent_is_major(self, config, step_geometry_with_features):
        step_geometry_with_features["ribs"][0]["thickness"] = 2.4   # 80% of 3 mm
        result = run_rule(RibThicknessRule, config, step_geometry_with_features)
        assert result.status == RuleStatus.failed
        assert result.severity == Severity.major
        assert result.findings[0].measured == pytest.approx(0.8)

    def test_rib_between_50_and_60_percent_is_minor(self, config, step_geometry_with_features):
        step_geometry_with_features["ribs"][0]["thickness"] = 1.65   # 55%
        result = run_rule(RibThicknessRule, config, step_geometry_with_features)
        assert result.severity == Severity.minor

    def test_prefers_local_base_wall_over_part_nominal(self, config, step_geometry_with_features):
        rib = step_geometry_with_features["ribs"][0]
        rib["thickness"] = 2.4
        rib["base_wall_thickness"] = 5.0    # 2.4/5.0 = 48% -> passes locally
        result = run_rule(RibThicknessRule, config, step_geometry_with_features)
        assert result.status == RuleStatus.passed

    def test_rib_without_thickness_is_skipped_not_failed(
        self, config, step_geometry_with_features
    ):
        step_geometry_with_features["ribs"][0]["thickness"] = 0.0
        result = run_rule(RibThicknessRule, config, step_geometry_with_features)
        assert result.status == RuleStatus.not_assessed


class TestM6BossDesign:
    def test_not_assessed_when_bosses_array_is_absent(self, config, geometry_without_features):
        result = run_rule(BossDesignRule, config, geometry_without_features)
        assert result.status == RuleStatus.not_assessed
        assert result.missing_inputs == ["bosses"]

    def test_mocked_hollow_boss_within_guideline_passes(
        self, config, step_geometry_with_features
    ):
        result = run_rule(BossDesignRule, config, step_geometry_with_features)
        assert result.status == RuleStatus.passed

    def test_thick_boss_wall_is_major(self, config, step_geometry_with_features):
        step_geometry_with_features["bosses"][0]["wall_thickness"] = 2.4   # 80%
        result = run_rule(BossDesignRule, config, step_geometry_with_features)
        assert result.status == RuleStatus.failed
        assert result.severity == Severity.major

    def test_solid_bulky_boss_gets_a_core_out_recommendation(
        self, config, step_geometry_with_features
    ):
        step_geometry_with_features["bosses"][0].update(
            {"is_solid": True, "inner_diameter": None, "wall_thickness": None,
             "outer_diameter": 9.0}     # 3x the 3 mm wall
        )
        result = run_rule(BossDesignRule, config, step_geometry_with_features)
        assert result.status == RuleStatus.failed
        assert any("core" in f.recommendation.lower() for f in result.findings)


# ---------------------------------------------------------------------------
# M7
# ---------------------------------------------------------------------------

class TestM7ToleranceFeasibility:
    def test_not_assessed_without_tolerances(self, config, step_geometry):
        result = run_rule(ToleranceFeasibilityRule, config, step_geometry)
        assert result.status == RuleStatus.not_assessed
        assert result.score_impact == 0.0

    def test_achievable_tolerance_passes(self, config, step_geometry):
        inputs = DFMInputs(tolerances=[
            ToleranceRequest(label="bore", feature_size_mm=8.0, requested_tolerance_mm=0.2)
        ])
        result = run_rule(ToleranceFeasibilityRule, config, step_geometry, inputs)
        assert result.status == RuleStatus.passed

    def test_tighter_than_capability_is_major(self, config, step_geometry):
        inputs = DFMInputs(tolerances=[
            ToleranceRequest(label="bore", feature_size_mm=8.0, requested_tolerance_mm=0.01)
        ])
        result = run_rule(ToleranceFeasibilityRule, config, step_geometry, inputs)
        assert result.status == RuleStatus.failed
        assert result.severity == Severity.major

    def test_borderline_tolerance_is_minor(self, config, step_geometry):
        inputs = DFMInputs(tolerances=[
            ToleranceRequest(label="bore", feature_size_mm=8.0, requested_tolerance_mm=0.09)
        ])
        result = run_rule(ToleranceFeasibilityRule, config, step_geometry, inputs)
        assert result.severity == Severity.minor

    def test_capability_widens_with_feature_size(self, config, step_geometry):
        inputs = DFMInputs(tolerances=[
            ToleranceRequest(label="big", feature_size_mm=250.0, requested_tolerance_mm=0.2)
        ])
        result = run_rule(ToleranceFeasibilityRule, config, step_geometry, inputs)
        assert result.status == RuleStatus.failed   # 0.2 is tight at 250 mm

    def test_material_floor_is_respected(self, config, step_geometry):
        inputs = DFMInputs(
            material="PA66",     # 0.15 mm capability, looser than the 0.10 size band
            tolerances=[
                ToleranceRequest(label="bore", feature_size_mm=8.0, requested_tolerance_mm=0.12)
            ],
        )
        result = run_rule(ToleranceFeasibilityRule, config, step_geometry, inputs)
        assert result.status == RuleStatus.failed


def test_every_molding_rule_survives_empty_geometry(config, empty_geometry):
    """Graceful degradation: no rule may raise, and none may fail the part."""
    from dfm.rules.injection_molding import INJECTION_MOLDING_RULES

    for rule_class in INJECTION_MOLDING_RULES:
        result = run_rule(rule_class, config, copy.deepcopy(empty_geometry))
        assert result.status in (RuleStatus.not_assessed, RuleStatus.suppressed), (
            f"{rule_class.__name__} returned {result.status}"
        )
        assert result.score_impact == 0.0
