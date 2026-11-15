from __future__ import annotations

from dataclasses import replace

import pytest

from src.assumptions import Assumptions
from src.economics import action_metrics
from src.risk_model import score_cohort
from tests.conftest import reference_cohort


def test_literature_constants_stay_labeled_defaults():
    assumptions = Assumptions()
    assert assumptions.high_risk_benchmark == 0.15
    assert assumptions.metaphylaxis_cost_per_head == 23.60
    assert assumptions.morbidity_cost_per_case == 151.18
    assert assumptions.metaphylaxis_efficacy == 0.50


def test_no_double_counted_costs():
    assumptions = Assumptions()
    cohort = reference_cohort(head_count=200, clinically_ill_head=4, arrival_weight_lb=540)
    scored = score_cohort(cohort, False, assumptions)
    metric = action_metrics(cohort, scored, "vet_review", assumptions)

    at_risk = cohort.head_count - cohort.clinically_ill_head
    assert metric.metaphylaxis_head == at_risk
    assert metric.program_cost == pytest.approx(at_risk * 23.60)
    assert metric.morbidity_cost == pytest.approx(metric.expected_cases * 151.18)
    assert metric.operating_loss == pytest.approx(metric.program_cost + metric.morbidity_cost)
    assert metric.morbidity_cost / metric.expected_cases == pytest.approx(151.18)
    # Already-ill cattle stay in the case count and are not also billed as metaphylaxis.
    residual = at_risk * scored.morbidity * (1 - assumptions.metaphylaxis_efficacy)
    assert metric.expected_cases == pytest.approx(cohort.clinically_ill_head + residual)

    standard = action_metrics(cohort, scored, "standard_care", assumptions)
    assert standard.program_cost == 0
    assert standard.morbidity_cost == pytest.approx(standard.expected_cases * 151.18)
    surveillance = action_metrics(cohort, scored, "enhanced_surveillance", assumptions)
    assert surveillance.program_cost == pytest.approx(cohort.head_count * 1.50)
    assert surveillance.program_cost != pytest.approx(cohort.head_count * 23.60)

    richer = replace(assumptions, morbidity_cost_per_case=400)
    richer_metric = action_metrics(cohort, scored, "vet_review", richer)
    assert richer_metric.program_cost == pytest.approx(metric.program_cost)
    assert richer_metric.morbidity_cost > metric.morbidity_cost

    dearer_drug = replace(assumptions, metaphylaxis_cost_per_head=40)
    dearer_metric = action_metrics(cohort, scored, "vet_review", dearer_drug)
    assert dearer_metric.morbidity_cost == pytest.approx(metric.morbidity_cost)
    assert dearer_metric.program_cost > metric.program_cost


def test_efficacy_does_not_erase_clinical_cases():
    assumptions = Assumptions()
    cohort = reference_cohort(head_count=100, clinically_ill_head=5)
    scored = score_cohort(cohort, False, assumptions)
    vet = action_metrics(cohort, scored, "vet_review", assumptions)
    assert vet.expected_cases == pytest.approx(5 + 95 * scored.morbidity * 0.5)
    assert vet.treatment_slots >= cohort.clinically_ill_head
    assert vet.veterinary_review_required


def test_deaths_follow_cases_and_weight_class(assumptions):
    from src.assumptions import case_fatality
    from src.risk_model import score_cohort
    from tests.conftest import reference_cohort

    light = case_fatality(540, assumptions)
    heavy = case_fatality(760, assumptions)
    assert light > heavy > 0
    # 2.3% x 65% x 72.5% / 6.3%
    assert light == pytest.approx(0.023 * 0.65 * 0.725 / 0.063)

    cohort = reference_cohort(arrival_weight_lb=540, head_count=200, clinically_ill_head=4)
    scored = score_cohort(cohort, False, assumptions)
    standard = action_metrics(cohort, scored, "standard_care", assumptions)
    vet = action_metrics(cohort, scored, "vet_review", assumptions)
    assert standard.expected_deaths == pytest.approx(standard.expected_cases * light)
    assert vet.expected_deaths < standard.expected_deaths
    # Deaths are reported, not priced: operating loss does not change with them.
    assert standard.operating_loss == pytest.approx(standard.morbidity_cost + standard.program_cost)


def test_mortality_objective_solves_within_limits():
    from src.data_loader import load_demo
    from src.optimizer import solve
    from src.pipeline import build_context

    cohorts, yards = load_demo("shortage")
    context = build_context(cohorts, yards)
    result = solve(context.cohorts, context.metrics, context.yards, objective="modeled_mortality")
    assert result.feasible
    cost = solve(context.cohorts, context.metrics, context.yards)
    assert result.totals.expected_deaths <= cost.totals.expected_deaths + 1e-9
