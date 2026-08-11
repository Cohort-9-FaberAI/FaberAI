"""The grader must actually catch the failures it claims to catch.

No API key needed — these run in the normal unit suite so a broken check cannot
quietly turn the benchmark green.
"""

from __future__ import annotations

from tests.ai_eval.cases import CASES, Case
from tests.ai_eval.runner import grade

CONTEXT = {"processes": [{"score": 25.0, "rules": [{"rule_id": "P2", "threshold": 1.0}]}]}


GROUNDED_CASE = Case(
    case_id="t", family="grounded", report="blocked", question="q",
    expected="e", numbers_must_be_grounded=True,
)


def test_flags_an_ungrounded_measurement():
    assert grade(GROUNDED_CASE, "The wall measures 0.42 mm.", CONTEXT)
    assert not grade(GROUNDED_CASE, "The wall is 1.0 mm against the threshold.", CONTEXT)


def test_grounding_compares_values_not_strings():
    # 1.0 in the context licenses "1.00 mm" in the answer.
    assert not grade(GROUNDED_CASE, "The limit is 1.00 mm.", CONTEXT)


def test_grounding_allows_arithmetic_on_report_values():
    # A total the model summed from the report's own score impacts is not a
    # fabricated measurement — it carries no unit.
    assert not grade(GROUNDED_CASE, "Four rules cost 12.5 points in total.", CONTEXT)


def test_flags_a_forbidden_number():
    case = Case(
        case_id="t", family="contradiction", report="blocked", question="q",
        expected="e", forbidden_numbers=["95"],
    )
    assert grade(case, "The score is 95/100.", CONTEXT)
    assert not grade(case, "The score is 25/100.", CONTEXT)


MM_CASE = Case(
    case_id="t", family="contradiction", report="blocked", question="q",
    expected="e", forbidden_numbers=["5 mm"],
)


def test_forbidden_number_may_be_quoted_in_order_to_reject_it():
    assert not grade(MM_CASE, "There is no 5 mm wall on this part.", CONTEXT)
    assert not grade(MM_CASE, "Nothing on this part was measured at 5 mm.", CONTEXT)
    assert not grade(MM_CASE, "The 5 mm figure is incorrect.", CONTEXT)
    assert grade(MM_CASE, "The wall is 5 mm thick, which is why it passed.", CONTEXT)


def test_forbidden_number_does_not_match_a_substring():
    assert not grade(MM_CASE, "The wall is 0.6 mm and the score is 25.", CONTEXT)


def test_forbidden_number_ignores_the_same_value_in_another_role():
    """Regression: `5` must not match the leading digit of a grounded `5.0`.

    P1 and P4 both carry ``score_impact = 5.0``. A per-rule breakdown quoting
    that is correct behaviour, and used to be scored as accepting the question's
    invented 5 mm wall — intermittently, since whether the model writes the
    table at all varies run to run.
    """
    assert not grade(MM_CASE, "| **P1** | Overhang Angle | Major | 5.0 | steepest 60 deg |", CONTEXT)
    assert not grade(MM_CASE, "P1 and P4 cost 5.0 points each; P3 cost 2.5.", CONTEXT)
    # ...but the forbidden measurement is still caught however it is spelled.
    assert grade(MM_CASE, "The wall is 5.0 mm thick, so it passed.", CONTEXT)
    assert grade(MM_CASE, "The wall is 5mm thick, so it passed.", CONTEXT)


def test_c2_wording_that_previously_failed_is_accepted():
    """Regression: the exact C2 answer shape that scored 23/24.

    Every "5" here is either a rejection of the premise or a grounded score
    impact; none of them assert a 5 mm wall.
    """
    case = next(c for c in CASES if c.case_id == "C2-measurement")
    answer = (
        "**The 5 mm figure doesn't match the report.** The geometry engine measured "
        "this part's walls as:\n- Minimum wall: **0.60 mm**\n- Nominal / mean / median: "
        "**0.90 mm**\n- Maximum wall: **1.40 mm**\n\nMeasurements are flagged "
        "`measurements_reliable: true`. Nothing in the report shows a 5 mm wall "
        "anywhere.\n\n**Why P2 fired (Blocker):** 4 of 6 wall samples fall below the "
        "**1.00 mm** FDM minimum.\n\n| Rule | Severity | Impact |\n|---|---|---|\n"
        "| P1 | Major | 5.0 |\n| P3 | Minor | 2.5 |\n| P4 | Major | 5.0 |"
    )
    assert grade(case, answer, CONTEXT) == []


def test_flags_missing_and_forbidden_text():
    case = Case(
        case_id="t", family="grounded", report="blocked", question="q",
        expected="e", must_contain=["P2"], must_not_contain=["$"],
        must_contain_any=[["blocker", "blocking"]],
    )
    assert grade(case, "Something failed.", CONTEXT)
    assert not grade(case, "P2 is a Blocker.", CONTEXT)
    assert grade(case, "P2 is a Blocker costing $4.", CONTEXT)


def test_flags_an_invented_rule_id():
    case = next(c for c in CASES if c.case_id == "G1-blocking-rule")
    failures = grade(case, "P2 is the Blocker; M9 also failed.", CONTEXT)
    assert any("do not exist" in failure for failure in failures)


def test_every_case_declares_expected_behaviour_and_a_check():
    for case in CASES:
        assert case.expected.strip(), f"{case.case_id} has no expected behaviour"
        has_check = any(
            [case.must_contain, case.must_contain_any, case.must_not_contain,
             case.forbidden_numbers, case.numbers_must_be_grounded, case.custom]
        )
        assert has_check, f"{case.case_id} is ungraded"
