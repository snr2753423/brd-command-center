"""Consequences for one cohort and one action.

Operating loss = morbidity cost + program cost.
Morbidity cost is the case-loss constant times expected cases.
Program cost is the action's own supply or metaphylaxis invoice.
Those dollars are never added into each other a second time.
Staff hours are a capacity constraint, not a second labor bill.
"""

from __future__ import annotations

from dataclasses import dataclass

from .assumptions import Assumptions, case_fatality, efficacy_for
from .risk_model import Scored
from .schema import ACTIONS, Cohort


@dataclass(frozen=True)
class Metric:
    cohort_id: str
    action_id: str
    morbidity: float
    confident_call: bool
    expected_cases: float
    morbidity_cost: float
    program_cost: float
    operating_loss: float
    amu: float
    staff_hours: float
    pen_sqft: float
    treatment_slots: float
    welfare_staff_floor: float
    veterinary_review_required: bool
    metaphylaxis_head: float
    at_risk_head: int
    expected_deaths: float


def action_metrics(
    cohort: Cohort, scored: Scored, action_id: str, assumptions: Assumptions
) -> Metric:
    if action_id not in ACTIONS:
        raise KeyError(action_id)
    if cohort.clinically_ill_head > cohort.head_count:
        raise ValueError("clinically ill head cannot exceed head count")

    efficacy = min(max(efficacy_for(action_id, assumptions), 0.0), 0.95)
    at_risk = cohort.head_count - cohort.clinically_ill_head
    # Cattle already clinically ill stay cases. Efficacy applies only to the rest.
    # Planning morbidity: worst case across unknown states unless the manager picks another basis.
    residual = at_risk * scored.planning_morbidity * (1.0 - efficacy)
    expected_cases = cohort.clinically_ill_head + residual
    morbidity_cost = expected_cases * assumptions.morbidity_cost_per_case
    # Deaths follow cases. Not priced: the $151.18 lost value already covers a sick animal.
    expected_deaths = expected_cases * case_fatality(cohort.arrival_weight_lb, assumptions)

    metaphylaxis_head = 0.0
    if action_id == "vet_review":
        metaphylaxis_head = float(at_risk)
        program_cost = metaphylaxis_head * assumptions.metaphylaxis_cost_per_head
        amu = (
            metaphylaxis_head * assumptions.metaphylaxis_exposure_per_head
            + expected_cases * assumptions.therapeutic_exposure_per_case
        )
    elif action_id == "enhanced_surveillance":
        program_cost = cohort.head_count * assumptions.surveillance_program_cost_per_head
        amu = expected_cases * assumptions.therapeutic_exposure_per_case
    elif action_id == "supportive_management":
        program_cost = cohort.head_count * assumptions.supportive_program_cost_per_head
        amu = expected_cases * assumptions.therapeutic_exposure_per_case
    else:
        program_cost = 0.0
        amu = expected_cases * assumptions.therapeutic_exposure_per_case

    staff_hours = cohort.head_count * assumptions.staff_rate(action_id)
    welfare_floor = cohort.head_count * assumptions.staff_rate("standard_care")
    pen_sqft = cohort.head_count * assumptions.sqft_per_head * assumptions.pen_factor_for(action_id)
    treatment_slots = expected_cases

    return Metric(
        cohort_id=cohort.cohort_id,
        action_id=action_id,
        morbidity=scored.planning_morbidity,
        confident_call=scored.confident_call,
        expected_cases=expected_cases,
        morbidity_cost=morbidity_cost,
        program_cost=program_cost,
        operating_loss=morbidity_cost + program_cost,
        amu=amu,
        staff_hours=staff_hours,
        pen_sqft=pen_sqft,
        treatment_slots=treatment_slots,
        welfare_staff_floor=welfare_floor,
        veterinary_review_required=action_id == "vet_review",
        metaphylaxis_head=metaphylaxis_head,
        at_risk_head=at_risk,
        expected_deaths=expected_deaths,
    )


def metrics_by_action(
    cohort: Cohort, scored: Scored, assumptions: Assumptions
) -> dict[str, Metric]:
    return {action_id: action_metrics(cohort, scored, action_id, assumptions) for action_id in ACTIONS}


@dataclass(frozen=True)
class CompareRow:
    action_id: str
    is_current_practice: bool
    metric: Metric
    delta_cases: float
    delta_loss: float
    delta_amu: float
    delta_staff: float
    delta_deaths: float


def compare_to_practice(
    cohort: Cohort,
    scored: Scored,
    assumptions: Assumptions,
    practice_action: str,
) -> list[CompareRow]:
    table = metrics_by_action(cohort, scored, assumptions)
    baseline = table[practice_action]
    ordered = [practice_action] + [action_id for action_id in ACTIONS if action_id != practice_action]
    rows: list[CompareRow] = []
    for action_id in ordered:
        metric = table[action_id]
        rows.append(
            CompareRow(
                action_id=action_id,
                is_current_practice=action_id == practice_action,
                metric=metric,
                delta_cases=metric.expected_cases - baseline.expected_cases,
                delta_loss=metric.operating_loss - baseline.operating_loss,
                delta_amu=metric.amu - baseline.amu,
                delta_staff=metric.staff_hours - baseline.staff_hours,
                delta_deaths=metric.expected_deaths - baseline.expected_deaths,
            )
        )
    return rows
