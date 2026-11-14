from __future__ import annotations

from src.data_loader import load_demo
from src.optimizer import evaluate_assignment, solve
from src.pipeline import build_context
from src.practice import current_practice_action
from src.reporting import decision_summary
from src.schema import INCOMPLETE_COHORT_ID, PRIORITY_COHORT_ID


def test_summary_names_the_plan_and_the_withheld_call():
    cohorts, yards = load_demo("shortage")
    context = build_context(cohorts, yards)
    recommended = solve(context.cohorts, context.metrics, context.yards)
    practice = evaluate_assignment(
        {cohort.cohort_id: current_practice_action(cohort) for cohort in cohorts},
        context.cohorts,
        context.metrics,
        context.yards,
    )
    text = decision_summary(
        context,
        recommended,
        practice,
        scenario="shortage",
        staff_note="TX-A staff hours in this solve: 220",
    )
    assert "SYNTHETIC DATA" in text
    assert PRIORITY_COHORT_ID in text
    assert "Enhanced surveillance" in text
    assert "No confident recommendation" in text
    assert INCOMPLETE_COHORT_ID in text
    assert "veterinary review required: yes" in text or "Veterinary review" in text
    assert "Not a prescription" in text
