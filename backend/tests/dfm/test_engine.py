"""End-to-end DFM engine behaviour."""

from __future__ import annotations

import copy

import pytest

from dfm import DFMInputs, run_dfm_analysis
from dfm.inputs import ToleranceRequest
from dfm.models import ProcessType, RuleStatus


class TestReportShape:
    def test_evaluates_both_processes_by_default(self, step_geometry):
        report = run_dfm_analysis(step_geometry)
        assert {p.process for p in report.processes} == {
            ProcessType.injection_molding, ProcessType.printing
        }

    def test_evaluates_only_the_requested_process(self, step_geometry):
        report = run_dfm_analysis(step_geometry, DFMInputs(process=ProcessType.printing))
        assert [p.process for p in report.processes] == [ProcessType.printing]

    def test_every_rule_in_the_check_set_is_reported(self, step_geometry):
        report = run_dfm_analysis(step_geometry)
        molding = report.process_report(ProcessType.injection_molding)
        printing = report.process_report(ProcessType.printing)
        assert [r.rule_id for r in molding.rule_results] == \
            ["M1", "M2", "M3", "M4", "M5", "M6", "M7"]
        assert [r.rule_id for r in printing.rule_results] == \
            ["P1", "P2", "P3", "P4", "P5", "P6"]

    def test_reports_both_headline_values(self, step_geometry):
        report = run_dfm_analysis(step_geometry)
        assert isinstance(report.manufacturable, bool)
        assert 0 <= report.manufacturability_score <= 100

    def test_captures_part_measurements_verbatim(self, step_geometry):
        report = run_dfm_analysis(step_geometry)
        assert report.part.filename == "bracket.stp"
        assert report.part.nominal_wall_mm == 3.0
        assert report.part.bounding_box_mm == [100.0, 60.0, 40.0]

    def test_echoes_the_resolved_inputs(self, step_geometry):
        report = run_dfm_analysis(step_geometry, DFMInputs(material="ABS"))
        assert report.inputs["material_resolved"] == "abs"
        assert report.inputs["material_class"] == "amorphous"
        assert report.inputs["printing_process"] == "fdm"

    def test_records_the_config_version(self, step_geometry):
        report = run_dfm_analysis(step_geometry)
        assert "thresholds" in report.config_version

    def test_states_the_build_orientation_for_printing(self, step_geometry):
        report = run_dfm_analysis(step_geometry)
        printing = report.process_report(ProcessType.printing)
        assert printing.orientation_assumed == "+Z"
        assert report.process_report(ProcessType.injection_molding).orientation_assumed is None

    def test_report_serialises_to_json(self, step_geometry):
        report = run_dfm_analysis(step_geometry)
        payload = report.model_dump(mode="json")
        assert payload["processes"][0]["rule_results"]
        assert isinstance(payload["generated_at"], str)

    def test_is_deterministic(self, step_geometry):
        first = run_dfm_analysis(copy.deepcopy(step_geometry), DFMInputs(material="ABS"))
        second = run_dfm_analysis(copy.deepcopy(step_geometry), DFMInputs(material="ABS"))
        assert first.manufacturability_score == second.manufacturability_score
        assert [r.status for r in first.failed_rules()] == \
            [r.status for r in second.failed_rules()]


class TestGracefulDegradation:
    def test_a_nearly_empty_payload_produces_a_report_not_an_error(self, empty_geometry):
        report = run_dfm_analysis(empty_geometry)
        assert report.processes
        for process in report.processes:
            for rule in process.rule_results:
                assert rule.status in (RuleStatus.not_assessed, RuleStatus.suppressed)

    def test_unassessable_part_is_not_penalised(self, empty_geometry):
        report = run_dfm_analysis(empty_geometry)
        for process in report.processes:
            assert process.score == 100.0
            assert process.manufacturable is True

    def test_low_confidence_signals_the_lack_of_data(self, empty_geometry):
        report = run_dfm_analysis(empty_geometry)
        for process in report.processes:
            assert process.confidence < 0.5

    def test_missing_optional_inputs_never_lower_the_score(self, step_geometry):
        bare = run_dfm_analysis(step_geometry)
        with_context = run_dfm_analysis(
            step_geometry,
            DFMInputs(
                material="ABS", surface_finish="semi_gloss", printing_process="fdm",
                build_envelope_mm=[250.0, 210.0, 220.0],
            ),
        )
        bare_molding = bare.process_report(ProcessType.injection_molding)
        context_molding = with_context.process_report(ProcessType.injection_molding)
        assert bare_molding.score >= context_molding.score

    def test_warns_about_unreliable_measurements(self, stl_geometry):
        stl_geometry["measurements_reliable"] = False
        report = run_dfm_analysis(stl_geometry)
        assert any("unreliable" in w for w in report.warnings)

    def test_warns_when_feature_recognition_is_absent(self, geometry_without_features):
        report = run_dfm_analysis(geometry_without_features)
        assert any("Rib and/or boss" in w for w in report.warnings)

    def test_accepts_a_pydantic_geometry_payload(self, step_geometry):
        from dfm.geometry_contract import GeometryInput

        report = run_dfm_analysis(GeometryInput.model_validate(step_geometry))
        assert report.processes

    def test_rejects_a_payload_of_the_wrong_type(self):
        with pytest.raises(TypeError):
            run_dfm_analysis("not a geometry payload")

    def test_unknown_geometry_fields_are_tolerated(self, step_geometry):
        step_geometry["some_future_extractor"] = {"anything": [1, 2, 3]}
        report = run_dfm_analysis(step_geometry)
        assert report.processes


class TestEndToEndVerdicts:
    def test_clean_part_is_manufacturable_by_both_processes(self, step_geometry):
        # Walls thick enough for both check-sets, drafted, fits the bed.
        report = run_dfm_analysis(step_geometry, DFMInputs(material="ABS"))
        for process in report.processes:
            assert process.manufacturable is True

    def test_blocker_flips_manufacturable_and_caps_the_score(self, stl_geometry, config):
        report = run_dfm_analysis(stl_geometry, DFMInputs(process=ProcessType.printing))
        printing = report.process_report(ProcessType.printing)
        assert printing.manufacturable is False
        assert "P2" in printing.blocking_rule_ids
        assert printing.score <= config.blocker_cap_value

    def test_unmouldable_undercut_recommends_printing(self, step_geometry):
        step_geometry["undercuts"] = [{"id": 1, "face_ids": [1], "releasable": False}]
        report = run_dfm_analysis(step_geometry, DFMInputs(material="ABS"))
        assert report.recommendation.recommended_process == ProcessType.printing
        assert "undercut" in report.recommendation.reason.lower()

    def test_headline_follows_the_requested_process(self, step_geometry):
        step_geometry["undercuts"] = [{"id": 1, "face_ids": [1], "releasable": False}]
        report = run_dfm_analysis(
            step_geometry, DFMInputs(process=ProcessType.injection_molding)
        )
        assert report.manufacturable is False

    def test_tolerances_feed_the_tolerance_sub_score(self, step_geometry):
        report = run_dfm_analysis(step_geometry, DFMInputs(
            process=ProcessType.injection_molding,
            tolerances=[ToleranceRequest(
                label="bore", feature_size_mm=8.0, requested_tolerance_mm=0.01
            )],
        ))
        molding = report.process_report(ProcessType.injection_molding)
        tolerance_rule = next(r for r in molding.rule_results if r.rule_id == "M7")
        assert tolerance_rule.status == RuleStatus.failed
        assert "M7" not in molding.not_assessed_rule_ids

    def test_findings_carry_geometry_references(self, step_geometry):
        orientation = step_geometry["print_orientations"]["orientations"][0]
        orientation["face_angles"] = {1: 90.0, 2: 90.0, 3: 0.0}
        report = run_dfm_analysis(step_geometry, DFMInputs(
            process=ProcessType.injection_molding, material="ABS"
        ))
        draft = report.rule("M3")
        assert draft.findings
        assert draft.findings[0].geometry_ref.face_ids
        assert draft.findings[0].geometry_ref.centroid is not None

    def test_findings_record_measured_and_threshold(self, step_geometry_with_features):
        step_geometry_with_features["ribs"][0]["thickness"] = 2.4
        report = run_dfm_analysis(step_geometry_with_features, DFMInputs(material="ABS"))
        rib = report.rule("M5")
        assert rib.findings[0].measured == pytest.approx(0.8)
        assert rib.findings[0].threshold == 0.6

    def test_score_impact_is_attributed_per_finding(self, stl_geometry):
        report = run_dfm_analysis(stl_geometry, DFMInputs(process=ProcessType.printing))
        printing = report.process_report(ProcessType.printing)
        for rule in printing.rule_results:
            attributed = sum(f.score_impact for f in rule.findings)
            assert attributed == pytest.approx(rule.score_impact, abs=0.01)
