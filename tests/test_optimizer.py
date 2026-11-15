from __future__ import annotations

from dataclasses import replace

import pytest

from src.data_loader import load_demo
from src.optimizer import solve
from src.pipeline import build_context
from src.practice import current_practice_action
from src.optimizer import evaluate_assignment
from src.schema import DEMO_YARD_ID, PRIORITY_COHORT_ID


def _shortage():
    cohorts, yards = load_demo("shortage")
    return build_context(cohorts, yards)


def test_seeded_plan_respects_staff_pen_treatment_and_welfare():
    context = _shortage()
    result = solve(context.cohorts, context.metrics, context.yards)
    assert result.status == "optimal"
    assert result.assignment[PRIORITY_COHORT_ID] == "enhanced_surveillance"
    seen = set()
    for cohort in context.cohorts:
        action = result.assignment[cohort.cohort_id]
        assert action in context.metrics[cohort.cohort_id]
        seen.add(cohort.cohort_id)
        metric = result.by_cohort[cohort.cohort_id]
        assert metric.staff_hours + 1e-6 >= metric.welfare_staff_floor
        assert metric.treatment_slots + 1e-6 >= cohort.clinically_ill_head
    assert seen == set(result.assignment)
    for use in result.by_yard.values():
        assert use.staff <= use.staff_capacity + 1e-4
        assert use.pen <= use.pen_capacity + 1e-2
        assert use.treatment <= use.treatment_capacity + 1e-4
        assert use.pen_ratio == pytest.approx(1.0, abs=1e-6)
        assert use.staff_ratio >= 0.999
    for yard_id in ("TX-B", "KS-A", "KS-B"):
        assert result.by_yard[yard_id].treatment_ratio >= 0.999


def test_staff_cut_changes_the_priority_action_and_totals():
    context = _shortage()
    seeded_hours = context.yards[DEMO_YARD_ID].staff_hours
    cut_hours = context.yards[DEMO_YARD_ID].demo_staff_hours
    assert cut_hours < seeded_hours
    full = solve(context.cohorts, context.metrics, context.yards)
    cut = solve(
        context.cohorts,
        context.metrics,
        context.yards,
        staff_hours={DEMO_YARD_ID: cut_hours},
    )
    assert full.feasible and cut.feasible
    assert full.assignment[PRIORITY_COHORT_ID] == "enhanced_surveillance"
    assert cut.assignment[PRIORITY_COHORT_ID] == "standard_care"
    assert cut.totals.expected_cases > full.totals.expected_cases
    assert cut.totals.operating_loss > full.totals.operating_loss
    assert cut.totals.amu > full.totals.amu
    # One hour under the standard-care floor is refused.
    refused = solve(
        context.cohorts,
        context.metrics,
        context.yards,
        staff_hours={DEMO_YARD_ID: cut_hours - 1},
    )
    assert refused.status == "infeasible"


def test_pen_and_treatment_are_hard_limits():
    context = _shortage()
    yards = dict(context.yards)
    txa = yards[DEMO_YARD_ID]
    yards[DEMO_YARD_ID] = replace(txa, pen_capacity_sqft=txa.pen_capacity_sqft - 1)
    assert solve(context.cohorts, context.metrics, yards).status == "infeasible"

    yards = dict(context.yards)
    txb = yards["TX-B"]
    yards["TX-B"] = replace(txb, treatment_slots=txb.treatment_slots * 0.5)
    assert solve(context.cohorts, context.metrics, yards).status == "infeasible"

    blocked = solve(
        context.cohorts,
        context.metrics,
        {yard_id: replace(yard, treatment_slots=0) for yard_id, yard in context.yards.items()},
    )
    assert blocked.status == "infeasible"


def test_relaxed_pen_selects_supportive_management():
    cohorts, yards = load_demo("normal")
    context = build_context(cohorts, yards)
    result = solve(context.cohorts, context.metrics, context.yards)
    assert result.status == "optimal"
    assert result.assignment[PRIORITY_COHORT_ID] == "supportive_management"


def test_current_practice_breaks_txb_staff():
    context = _shortage()
    assignment = {
        cohort.cohort_id: current_practice_action(cohort, context.assumptions)
        for cohort in context.cohorts
    }
    evaluation = evaluate_assignment(assignment, context.cohorts, context.metrics, context.yards)
    assert evaluation.feasible is False
    assert any("TX-B staff" in item for item in evaluation.violations)


def test_three_objectives_and_the_cost_flip():
    context = _shortage()
    cost = solve(context.cohorts, context.metrics, context.yards, objective="operating_loss")
    morbidity = solve(
        context.cohorts, context.metrics, context.yards, objective="modeled_morbidity"
    )
    exposure = solve(
        context.cohorts, context.metrics, context.yards, objective="antimicrobial_exposure"
    )
    assert cost.assignment[PRIORITY_COHORT_ID] == "enhanced_surveillance"
    assert morbidity.assignment[PRIORITY_COHORT_ID] == "vet_review"
    assert morbidity.totals.expected_cases < cost.totals.expected_cases
    assert exposure.totals.amu <= cost.totals.amu + 1e-6
    assert exposure.totals.amu < morbidity.totals.amu - 1

    stressed = replace(
        context.assumptions,
        morbidity_cost_per_case=context.assumptions.flip_morbidity_cost_per_case,
    )
    flipped_context = build_context(context.cohorts, list(context.yards.values()), stressed)
    flipped = solve(flipped_context.cohorts, flipped_context.metrics, flipped_context.yards)
    assert flipped.feasible
    assert flipped.assignment[PRIORITY_COHORT_ID] == "vet_review"
    assert flipped.by_cohort[PRIORITY_COHORT_ID].veterinary_review_required


def test_any_yard_limit_can_be_overridden_and_shortfall_is_named():
    context = _shortage()
    kas = context.yards["KS-B"]
    tight_pen = solve(
        context.cohorts,
        context.metrics,
        context.yards,
        capacities={"KS-B": {"pen_capacity_sqft": kas.pen_capacity_sqft - 250}},
    )
    assert not tight_pen.feasible
    assert "KS-B pen needs at least" in tight_pen.message

    tight_treat = solve(
        context.cohorts,
        context.metrics,
        context.yards,
        capacities={"KS-A": {"treatment_slots": 1.0}},
    )
    assert not tight_treat.feasible
    assert "KS-A treatment needs at least" in tight_treat.message

    roomy = solve(
        context.cohorts,
        context.metrics,
        context.yards,
        capacities={"KS-B": {"pen_capacity_sqft": kas.pen_capacity_sqft * 2, "staff_hours": 400.0}},
    )
    assert roomy.feasible
    assert roomy.by_yard["KS-B"].pen_capacity == pytest.approx(kas.pen_capacity_sqft * 2)
    assert roomy.by_yard["KS-B"].staff_capacity == pytest.approx(400.0)


def test_unknown_capacity_field_is_rejected():
    context = _shortage()
    with pytest.raises(KeyError):
        solve(context.cohorts, context.metrics, context.yards, capacities={"TX-A": {"bunks": 1.0}})
