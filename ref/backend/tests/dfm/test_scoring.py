"""Scoring engine: weights, capping, blocker handling and roll-up.

Every number the scoring engine uses is configurable, so these tests build
throwaway ``DFMConfig`` objects to prove each switch actually changes behaviour
rather than asserting against the current defaults alone.
"""

from __future__ import annotations

import copy

import pytest

from dfm.config import DFMConfig
from dfm.config.loader import SCORING_FILE, THRESHOLDS_FILE, _read_yaml
from dfm.models import (
    Finding,
    ProcessReport,
    ProcessType,
    RuleResult,
    RuleStatus,
    Severity,
    SubScore,
    ThresholdType,
)
from dfm.scoring import ScoringEngine


@pytest.fixture()
def raw_config():
    return _read_yaml(THRESHOLDS_FILE), _read_yaml(SCORING_FILE)


def make_config(raw_config, **scoring_overrides) -> DFMConfig:
    thresholds, scoring = copy.deepcopy(raw_config[0]), copy.deepcopy(raw_config[1])
    for key, value in scoring_overrides.items():
        if isinstance(value, dict) and isinstance(scoring.get(key), dict):
            scoring[key].update(value)
        else:
            scoring[key] = value
    return DFMConfig(thresholds, scoring)


def make_rule(
    rule_id="M1",
    status=RuleStatus.failed,
    severities=(Severity.major,),
    sub_score=SubScore.geometry,
) -> RuleResult:
    findings = [
        Finding(
            finding_id=f"{rule_id.lower()}_{index:03d}",
            rule_id=rule_id,
            severity=severity,
            message="issue",
            recommendation="fix it",
        )
        for index, severity in enumerate(severities)
    ]
    return RuleResult(
        rule_id=rule_id,
        name=rule_id,
        process=ProcessType.injection_molding,
        sub_score=sub_score,
        threshold_type=ThresholdType.geometric_ratio,
        status=status,
        severity=findings[-1].severity if findings else None,
        findings=findings if status == RuleStatus.failed else [],
    )


class TestDeductions:
    def test_clean_part_keeps_the_start_score(self, config):
        report = ScoringEngine(config).score_process(
            ProcessType.injection_molding,
            [make_rule(status=RuleStatus.passed, severities=())],
            [],
        )
        assert report.score == 100.0
        assert report.manufacturable is True

    def test_major_and_minor_use_configured_weights(self, config):
        engine = ScoringEngine(config)
        report = engine.score_process(
            ProcessType.injection_molding,
            [
                make_rule("M1", severities=(Severity.major,)),
                make_rule("M2", severities=(Severity.minor,)),
            ],
            [],
        )
        expected = 100.0 - config.severity_weight("major") - config.severity_weight("minor")
        assert report.score == pytest.approx(expected)

    def test_weights_are_configurable(self, raw_config):
        config = make_config(
            raw_config,
            severity_weights={"major": 20.0, "minor": 5.0},
            per_rule_impact_cap={"default": 100.0, "overrides": {}},
        )
        report = ScoringEngine(config).score_process(
            ProcessType.injection_molding, [make_rule(severities=(Severity.major,))], []
        )
        assert report.score == 80.0

    def test_the_per_rule_cap_still_applies_to_a_retuned_weight(self, raw_config):
        config = make_config(raw_config, severity_weights={"major": 20.0, "minor": 5.0})
        report = ScoringEngine(config).score_process(
            ProcessType.injection_molding, [make_rule(severities=(Severity.major,))], []
        )
        assert report.score == 100.0 - config.rule_impact_cap("M1")


class TestPerRuleCapping:
    def test_repeated_findings_cannot_dominate(self, config):
        many = make_rule("M1", severities=(Severity.major,) * 50)
        report = ScoringEngine(config).score_process(
            ProcessType.injection_molding, [many], []
        )
        cap = config.rule_impact_cap("M1")
        assert report.rule_results[0].score_impact == cap
        assert report.score == 100.0 - cap

    def test_finding_impacts_sum_to_the_capped_total(self, config):
        many = make_rule("M1", severities=(Severity.major,) * 10)
        ScoringEngine(config).score_process(ProcessType.injection_molding, [many], [])
        total = sum(f.score_impact for f in many.findings)
        assert total == pytest.approx(many.score_impact, abs=0.01)

    def test_cap_is_per_rule_not_global(self, config):
        rules = [
            make_rule("M1", severities=(Severity.major,) * 50),
            make_rule("M2", severities=(Severity.major,) * 50),
        ]
        report = ScoringEngine(config).score_process(ProcessType.injection_molding, rules, [])
        assert report.score == 100.0 - 2 * config.rule_impact_cap("M1")

    def test_per_rule_override_is_honoured(self, raw_config):
        config = make_config(
            raw_config, per_rule_impact_cap={"default": 15.0, "overrides": {"M2": 40.0}}
        )
        report = ScoringEngine(config).score_process(
            ProcessType.injection_molding,
            [make_rule("M2", severities=(Severity.major,) * 50)],
            [],
        )
        assert report.rule_results[0].score_impact == 40.0


class TestBlockerHandling:
    def test_blocker_makes_the_process_not_manufacturable(self, config):
        report = ScoringEngine(config).score_process(
            ProcessType.injection_molding,
            [make_rule("M1", severities=(Severity.blocker,))],
            [],
        )
        assert report.manufacturable is False
        assert report.blocking_rule_ids == ["M1"]
        assert report.verdict_label == "Not viable"
        assert report.redesign_recommended is True

    def test_cap_mode_holds_the_score_below_the_redesign_threshold(self, config):
        report = ScoringEngine(config).score_process(
            ProcessType.injection_molding,
            [make_rule("M1", severities=(Severity.blocker,))],
            [],
        )
        assert report.score == config.blocker_cap_value
        assert report.score < config.redesign_below

    def test_zero_mode_nullifies_the_score(self, raw_config):
        config = make_config(raw_config, blocker={"mode": "zero"})
        report = ScoringEngine(config).score_process(
            ProcessType.injection_molding,
            [make_rule("M1", severities=(Severity.blocker,))],
            [],
        )
        assert report.score == 0.0
        assert report.manufacturable is False

    def test_deduct_mode_treats_blockers_as_weighted_findings(self, raw_config):
        config = make_config(
            raw_config,
            blocker={"mode": "deduct"},
            severity_weights={"blocker": 30.0, "major": 5.0, "minor": 2.5},
            per_rule_impact_cap={"default": 100.0, "overrides": {}},
        )
        report = ScoringEngine(config).score_process(
            ProcessType.injection_molding,
            [make_rule("M1", severities=(Severity.blocker,))],
            [],
        )
        assert report.score == 70.0
        assert report.manufacturable is False

    def test_only_blockers_cap(self, config):
        report = ScoringEngine(config).score_process(
            ProcessType.injection_molding,
            [make_rule("M1", severities=(Severity.major,) * 3)],
            [],
        )
        assert report.manufacturable is True
        assert report.score > config.blocker_cap_value


class TestNotAssessed:
    def test_not_assessed_costs_nothing(self, config):
        report = ScoringEngine(config).score_process(
            ProcessType.injection_molding,
            [make_rule("M7", status=RuleStatus.not_assessed, severities=())],
            [],
        )
        assert report.score == 100.0
        assert report.not_assessed_rule_ids == ["M7"]

    def test_not_assessed_leaves_the_sub_score_denominator(self, config):
        rules = [
            make_rule("M1", status=RuleStatus.passed, severities=(),
                      sub_score=SubScore.geometry),
            make_rule("M7", status=RuleStatus.not_assessed, severities=(),
                      sub_score=SubScore.tolerance_feature),
        ]
        report = ScoringEngine(config).score_process(ProcessType.injection_molding, rules, [])
        tolerance = next(
            s for s in report.sub_scores if s.sub_score == SubScore.tolerance_feature
        )
        assert tolerance.score is None
        assert tolerance.assessed_rules == 0

    def test_suppressed_rules_also_cost_nothing(self, config):
        report = ScoringEngine(config).score_process(
            ProcessType.printing,
            [make_rule("P1", status=RuleStatus.suppressed, severities=())],
            [],
        )
        assert report.score == 100.0

    def test_confidence_falls_with_coverage_and_assumptions(self, config):
        engine = ScoringEngine(config)
        full = engine.score_process(
            ProcessType.injection_molding,
            [make_rule("M1", status=RuleStatus.passed, severities=())],
            [],
        )
        partial = engine.score_process(
            ProcessType.injection_molding,
            [
                make_rule("M1", status=RuleStatus.passed, severities=()),
                make_rule("M2", status=RuleStatus.not_assessed, severities=()),
            ],
            ["assumed a material", "assumed a finish"],
        )
        assert full.confidence == 1.0
        assert partial.confidence < full.confidence


class TestRollup:
    def test_weighted_mode_changes_the_score(self, raw_config):
        config = make_config(raw_config, rollup={"mode": "weighted"})
        rules = [
            make_rule("M1", severities=(Severity.major,), sub_score=SubScore.geometry),
            make_rule("M4", status=RuleStatus.passed, severities=(),
                      sub_score=SubScore.cost_risk),
        ]
        report = ScoringEngine(config).score_process(
            ProcessType.injection_molding, rules, []
        )
        # geometry 95 @ 0.5, cost_risk 100 @ 0.3 -> renormalised over 0.8 = 96.875,
        # reported to one decimal place.
        assert report.score == pytest.approx(96.9, abs=0.05)

    def test_verdict_bands_follow_config(self, raw_config):
        config = make_config(
            raw_config, verdict_thresholds={"redesign_below": 30.0, "review_below": 50.0}
        )
        engine = ScoringEngine(config)
        healthy = engine.score_process(
            ProcessType.injection_molding,
            [make_rule(status=RuleStatus.passed, severities=())], [],
        )
        poor = engine.score_process(
            ProcessType.injection_molding,
            [make_rule("M1", severities=(Severity.major,) * 20),
             make_rule("M2", severities=(Severity.major,) * 20),
             make_rule("M3", severities=(Severity.major,) * 20),
             make_rule("M5", severities=(Severity.major,) * 20),
             make_rule("M6", severities=(Severity.major,) * 20)],
            [],
        )
        assert healthy.verdict_label == "Manufacturable"
        assert poor.verdict_label == "Redesign recommended"
        assert poor.redesign_recommended is True


class TestProcessRecommendation:
    def _process(self, process, score, manufacturable=True, blocking=()):
        return ProcessReport(
            process=process, manufacturable=manufacturable, score=score,
            blocking_rule_ids=list(blocking),
        )

    def test_prefers_the_higher_scoring_process(self, config):
        recommendation = ScoringEngine(config).recommend_process([
            self._process(ProcessType.injection_molding, 90.0),
            self._process(ProcessType.printing, 60.0),
        ])
        assert recommendation.recommended_process == ProcessType.injection_molding

    def test_a_blocked_process_never_wins(self, config):
        recommendation = ScoringEngine(config).recommend_process([
            self._process(ProcessType.injection_molding, 95.0, False, ["M1"]),
            self._process(ProcessType.printing, 55.0),
        ])
        assert recommendation.recommended_process == ProcessType.printing

    def test_m4_blocker_pushes_toward_printing(self, config):
        """Spec cross-link: an unmouldable undercut boosts 3D printing."""
        recommendation = ScoringEngine(config).recommend_process([
            self._process(ProcessType.injection_molding, 80.0, False, ["M4"]),
            self._process(ProcessType.printing, 70.0),
        ])
        assert recommendation.recommended_process == ProcessType.printing
        assert "undercut" in recommendation.reason.lower()

    def test_reports_when_neither_process_works(self, config):
        recommendation = ScoringEngine(config).recommend_process([
            self._process(ProcessType.injection_molding, 20.0, False, ["M1"]),
            self._process(ProcessType.printing, 20.0, False, ["P2"]),
        ])
        assert recommendation.recommended_process is None
        assert "Neither process" in recommendation.reason

    def test_close_scores_are_called_comparable(self, config):
        recommendation = ScoringEngine(config).recommend_process([
            self._process(ProcessType.injection_molding, 82.0),
            self._process(ProcessType.printing, 80.0),
        ])
        assert "within" in recommendation.reason

    def test_comparison_covers_every_process(self, config):
        recommendation = ScoringEngine(config).recommend_process([
            self._process(ProcessType.injection_molding, 82.0),
            self._process(ProcessType.printing, 40.0),
        ])
        assert set(recommendation.comparison) == {"injection_molding", "printing"}
