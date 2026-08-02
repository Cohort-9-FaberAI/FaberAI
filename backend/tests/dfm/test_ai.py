"""AI integration layer.

The property under test throughout: the AI consumes a finished report and never
produces one. It must not run geometry, must not re-evaluate a rule, and must
answer the same facts whether or not an LLM is available.
"""

from __future__ import annotations

import json

import pytest

from app.services.ai import (
    LLMClient,
    LLMNotConfigured,
    LLMRequestError,
    QuestionIntent,
    answer_dfm_question,
    build_ai_context,
    classify_intent,
)
from app.services.ai.service import AIServiceError, AnswerMode
from dfm import DFMInputs, run_dfm_analysis
from dfm.models import ProcessType, RuleStatus, Severity
from app.services.ai.context_builder import MAX_PRINT_ORIENTATION_CANDIDATES


@pytest.fixture()
def blocked_report(stl_geometry):
    """A printing report with a P2 Blocker — the 'not manufacturable' case."""
    return run_dfm_analysis(stl_geometry, DFMInputs(process=ProcessType.printing))


@pytest.fixture()
def clean_report(step_geometry):
    return run_dfm_analysis(step_geometry, DFMInputs(material="ABS"))


class StubLLM(LLMClient):
    """Records the messages it is asked to send and returns a fixed answer."""

    def __init__(self, response="The part fails P2.", error=None):
        super().__init__(base_url="https://stub.test/v1", api_key="test-key",
                         model="stub-model")
        self.response = response
        self.error = error
        self.messages = None

    def complete(self, messages):
        self.messages = messages
        if self.error:
            raise self.error
        return self.response


class TestIntentClassification:
    @pytest.mark.parametrize("question,expected", [
        ("Why is this part not manufacturable?", QuestionIntent.not_manufacturable),
        ("Which rules failed?", QuestionIntent.failed_rules),
        ("How can the design be improved?", QuestionIntent.improve),
        ("Why is one manufacturing process preferred?", QuestionIntent.process_choice),
        ("Should I use injection moulding or 3D printing?", QuestionIntent.process_choice),
        ("What is my score?", QuestionIntent.score),
        ("Why wasn't the tolerance check run?", QuestionIntent.not_assessed),
        ("Hello", QuestionIntent.small_talk),
        ("Tell me about this part", QuestionIntent.overview),
        ("", QuestionIntent.overview),
    ])
    def test_maps_the_product_questions(self, question, expected):
        assert classify_intent(question) == expected


class TestDeterministicAnswers:
    """The four questions the product promises to answer, with no LLM."""

    def test_why_not_manufacturable_names_the_blocking_rule(self, blocked_report):
        answer = answer_dfm_question(blocked_report, "Why is this part not manufacturable?")
        assert answer.mode == AnswerMode.deterministic
        assert "P2" in answer.answer
        assert "P2" in answer.referenced_rules

    def test_says_so_plainly_when_the_part_is_fine(self, clean_report):
        answer = answer_dfm_question(clean_report, "Why is this part not manufacturable?")
        assert "is** manufacturable" in answer.answer or "is manufacturable" in answer.answer

    def test_greeting_does_not_dump_the_report(self, clean_report):
        answer = answer_dfm_question(clean_report, "Hello")
        assert answer.mode == AnswerMode.deterministic
        assert "Hello" in answer.answer
        assert "Which rules failed" in answer.answer
        assert not answer.referenced_rules

    def test_non_blocked_failed_rules_are_explained_as_needs_review(self, clean_report):
        report = clean_report.model_copy(deep=True)
        rule = report.processes[0].rule_results[0]
        rule.status = RuleStatus.failed
        rule.severity = Severity.major
        rule.score_impact = 5.0
        rule.summary = "Synthetic major issue."
        rule.findings = []
        report.processes[0].score = 95.0
        answer = answer_dfm_question(report, "Why is this part not manufacturable?")
        assert "needs review" in answer.answer.lower()
        assert "Blocker" in answer.answer

    def test_which_rules_failed_lists_ids_severities_and_impact(self, blocked_report):
        answer = answer_dfm_question(blocked_report, "Which rules failed?")
        assert "P1" in answer.answer and "P2" in answer.answer
        assert "pts" in answer.answer

    def test_how_to_improve_returns_recommendations(self, blocked_report):
        answer = answer_dfm_question(blocked_report, "How can the design be improved?")
        assert "thicken" in answer.answer.lower() or "reorient" in answer.answer.lower()
        assert answer.referenced_rules

    def test_process_preference_quotes_the_recommendation(self, clean_report):
        answer = answer_dfm_question(
            clean_report, "Why is one manufacturing process preferred?"
        )
        assert clean_report.recommendation.reason in answer.answer

    def test_score_question_breaks_down_the_deductions(self, blocked_report):
        answer = answer_dfm_question(blocked_report, "Why is my score so low?")
        assert "/100" in answer.answer
        assert "Not assessed" in answer.answer

    def test_not_assessed_answer_states_no_penalty(self, step_geometry):
        report = run_dfm_analysis(step_geometry)
        answer = answer_dfm_question(report, "Why was the tolerance check not assessed?")
        assert "M7" in answer.answer
        assert "did not" in answer.answer.lower() or "excluded" in answer.answer.lower()

    def test_empty_question_is_rejected(self, clean_report):
        with pytest.raises(AIServiceError):
            answer_dfm_question(clean_report, "   ")

    def test_answers_are_reproducible(self, blocked_report):
        first = answer_dfm_question(blocked_report, "Which rules failed?")
        second = answer_dfm_question(blocked_report, "Which rules failed?")
        assert first.answer == second.answer


class TestLLMPath:
    def test_uses_the_llm_when_configured(self, blocked_report):
        client = StubLLM(response="P2 blocks this part: walls are 0.6 mm.")
        answer = answer_dfm_question(
            blocked_report, "Why is this not manufacturable?", client=client
        )
        assert answer.mode == AnswerMode.llm
        assert answer.model == "stub-model"
        assert answer.answer.startswith("P2 blocks")

    def test_prompt_carries_the_report_not_the_geometry_arrays(
        self, blocked_report, step_geometry
    ):
        client = StubLLM()
        answer_dfm_question(
            blocked_report, "Why?", geometry=step_geometry, client=client
        )
        user_message = client.messages[1]["content"]
        assert "P2" in user_message
        # Aggregate facts and array *counts* travel; the per-face, per-edge and
        # per-sample arrays themselves never do — they would blow the context
        # window and invite the model to re-derive the rule engine's results.
        for per_element_field in ("ray_length", "opposite_face_id", "surface_type",
                                  "face_angles", "moment_of_inertia"):
            assert per_element_field not in user_message

    def test_system_prompt_forbids_recomputation(self, blocked_report):
        client = StubLLM()
        answer_dfm_question(blocked_report, "Why?", client=client)
        system = client.messages[0]["content"]
        assert "Never compute or estimate geometry" in system
        assert "Never re-decide a verdict" in system
        assert "untrusted text" in system

    def test_falls_back_when_the_provider_fails(self, blocked_report):
        client = StubLLM(error=LLMRequestError("connection reset"))
        answer = answer_dfm_question(blocked_report, "Which rules failed?", client=client)
        assert answer.mode == AnswerMode.deterministic
        assert "connection reset" in answer.degraded_reason
        assert "P2" in answer.answer

    def test_falls_back_on_an_empty_completion(self, blocked_report):
        answer = answer_dfm_question(
            blocked_report, "Which rules failed?", client=StubLLM(response="")
        )
        assert answer.mode == AnswerMode.deterministic

    def test_unconfigured_client_answers_deterministically(self, blocked_report, monkeypatch):
        monkeypatch.delenv("FABERAI_AI_API_KEY", raising=False)
        monkeypatch.delenv("FABERAI_AI_BASE_URL", raising=False)
        answer = answer_dfm_question(blocked_report, "Which rules failed?", client=LLMClient())
        assert answer.mode == AnswerMode.deterministic
        assert answer.degraded_reason is None

    def test_unconfigured_client_raises_on_direct_use(self, monkeypatch):
        monkeypatch.delenv("FABERAI_AI_API_KEY", raising=False)
        with pytest.raises(LLMNotConfigured):
            LLMClient(base_url="", api_key="").complete([])

    def test_rule_ids_are_extracted_from_the_generated_answer(self, blocked_report):
        client = StubLLM(response="The blocking rule is P2; P4 also failed.")
        answer = answer_dfm_question(blocked_report, "Why?", client=client)
        assert set(answer.referenced_rules) == {"P2", "P4"}


class TestContextBuilder:
    def test_context_is_json_serialisable(self, blocked_report):
        context = build_ai_context(blocked_report)
        assert json.loads(json.dumps(context, default=str))

    def test_includes_every_rule_with_its_status(self, blocked_report):
        context = build_ai_context(blocked_report)
        rules = context["processes"][0]["rules"]
        assert {r["rule_id"] for r in rules} == {"P1", "P2", "P3", "P4", "P5", "P6"}
        assert all("status" in r for r in rules)

    def test_carries_thresholds_so_numbers_need_not_be_invented(self, blocked_report):
        context = build_ai_context(blocked_report)
        p2 = next(r for r in context["processes"][0]["rules"] if r["rule_id"] == "P2")
        assert p2["thresholds_used"]["min_wall_mm"] == 1.0

    def test_explains_why_a_rule_was_not_assessed(self, step_geometry):
        report = run_dfm_analysis(step_geometry)
        context = build_ai_context(report)
        molding = next(
            p for p in context["processes"] if p["process"] == "injection_molding"
        )
        m7 = next(r for r in molding["rules"] if r["rule_id"] == "M7")
        assert m7["status"] == "not_assessed"
        assert "not_assessed_reason" in m7

    def test_truncates_long_finding_lists(self, step_geometry):
        from app.services.ai.context_builder import MAX_FINDINGS_PER_RULE

        orientation = step_geometry["print_orientations"]["orientations"][0]
        orientation["face_angles"] = {face_id: 90.0 for face_id in range(1, 40)}
        step_geometry["faces"] = [
            {"id": face_id, "area": 100.0, "centroid": {"x": 0, "y": 0, "z": 0},
             "normal": {"x": 1, "y": 0, "z": 0}, "surface_type": "plane"}
            for face_id in range(1, 40)
        ]
        report = run_dfm_analysis(
            step_geometry, DFMInputs(process=ProcessType.injection_molding)
        )
        context = build_ai_context(report)
        m3 = next(r for r in context["processes"][0]["rules"] if r["rule_id"] == "M3")
        assert len(m3["findings"]) <= MAX_FINDINGS_PER_RULE
        assert "findings_truncated" in m3

    def test_geometry_facts_stay_aggregate(self, blocked_report, stl_geometry):
        context = build_ai_context(blocked_report, stl_geometry)
        facts = context["geometry_facts"]
        assert facts["wall_thickness"]["minimum_wall"] == 0.6
        assert "faces" not in facts
        assert "wall_samples" not in facts
        assert facts["feature_counts"]["cavities"] == 1

    def test_context_declares_the_boundary_it_enforces(self, blocked_report):
        context = build_ai_context(blocked_report)
        policy = context["context_policy"]
        assert policy["source"] == "completed_dfm_report"
        assert policy["raw_geometry_arrays_included"] is False
        assert "must not compute geometry" in " ".join(policy["rules"])

    def test_print_orientation_context_is_bounded(self, blocked_report, stl_geometry):
        stl_geometry["print_orientations"] = {
            "recommended": "z",
            "orientations": [
                {"axis_label": f"axis-{i}", "overhang_ratio": i / 10}
                for i in range(MAX_PRINT_ORIENTATION_CANDIDATES + 3)
            ],
        }
        context = build_ai_context(blocked_report, stl_geometry)
        orientations = context["geometry_facts"]["print_orientations"]
        assert len(orientations["candidates"]) == MAX_PRINT_ORIENTATION_CANDIDATES
        assert orientations["candidate_count"] == MAX_PRINT_ORIENTATION_CANDIDATES + 3

    def test_records_the_assumptions_a_verdict_rests_on(self, blocked_report):
        context = build_ai_context(blocked_report)
        assert any("FDM" in a for a in context["processes"][0]["assumptions"])
