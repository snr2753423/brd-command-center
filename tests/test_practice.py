from __future__ import annotations

from src.assumptions import Assumptions
from src.economics import compare_to_practice
from src.pipeline import build_context
from src.practice import current_practice_action, is_rule_high_risk
from src.data_loader import load_demo
from src.risk_model import score_cohort
from src.schema import PRIORITY_COHORT_ID
from tests.conftest import reference_cohort


def test_rule_is_light_and_multi_source_only():
    assumptions = Assumptions()
    light_multi = reference_cohort(arrival_weight_lb=540, source_count=3)
    light_single = reference_cohort(arrival_weight_lb=540, source_count=1)
    heavy_multi = reference_cohort(arrival_weight_lb=820, source_count=4)
    boundary = reference_cohort(arrival_weight_lb=600, source_count=4)
    assert is_rule_high_risk(light_multi, assumptions)
    assert current_practice_action(light_multi, assumptions) == "vet_review"
    assert current_practice_action(light_single, assumptions) == "standard_care"
    assert current_practice_action(heavy_multi, assumptions) == "standard_care"
    assert current_practice_action(boundary, assumptions) == "standard_care"


def test_seeded_priority_is_compared_with_the_rule():
    cohorts, yards = load_demo("shortage")
    context = build_context(cohorts, yards)
    assert context.practice[PRIORITY_COHORT_ID] == "vet_review"
    assert context.practice["TXA-4402"] == "standard_care"
    assert context.practice["TXB-4390"] == "standard_care"
    priority = next(cohort for cohort in cohorts if cohort.cohort_id == PRIORITY_COHORT_ID)
    rows = compare_to_practice(
        priority,
        context.scored[PRIORITY_COHORT_ID],
        context.assumptions,
        context.practice[PRIORITY_COHORT_ID],
    )
    assert rows[0].is_current_practice
    assert rows[0].action_id == "vet_review"
    assert rows[0].delta_cases == 0
    assert rows[0].delta_loss == 0
    assert sum(1 for row in rows if row.is_current_practice) == 1
    assert len(rows) == 4
    assert {row.action_id for row in rows} == {
        "standard_care",
        "enhanced_surveillance",
        "supportive_management",
        "vet_review",
    }


def test_model_benchmark_can_disagree_with_the_rule():
    cohorts, yards = load_demo("shortage")
    context = build_context(cohorts, yards)
    scored = context.scored["TXB-4390"]
    cohort = next(item for item in cohorts if item.cohort_id == "TXB-4390")
    assert scored.above_benchmark
    assert current_practice_action(cohort) == "standard_care"
    # The known-fields score is not the high-risk probability.
    assert scored.morbidity != scored.p_high_risk
