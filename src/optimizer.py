"""PuLP allocation. Staff, pen, and treatment are hard limits. Welfare is a floor."""

from __future__ import annotations

from dataclasses import dataclass, replace

import pulp

from .assumptions import Assumptions
from .economics import Metric
from .schema import ACTIONS, OBJECTIVES, Cohort, Yard

_TOL = 1e-5


@dataclass(frozen=True)
class YardUse:
    yard_id: str
    staff: float
    staff_capacity: float
    pen: float
    pen_capacity: float
    treatment: float
    treatment_capacity: float

    @property
    def staff_ratio(self) -> float:
        return self.staff / self.staff_capacity if self.staff_capacity else 0.0

    @property
    def pen_ratio(self) -> float:
        return self.pen / self.pen_capacity if self.pen_capacity else 0.0

    @property
    def treatment_ratio(self) -> float:
        return self.treatment / self.treatment_capacity if self.treatment_capacity else 0.0


@dataclass(frozen=True)
class Totals:
    expected_cases: float
    operating_loss: float
    amu: float
    staff_hours: float
    pen_sqft: float
    treatment_slots: float


@dataclass(frozen=True)
class Evaluation:
    status: str
    message: str
    objective: str
    assignment: dict[str, str]
    by_cohort: dict[str, Metric]
    by_yard: dict[str, YardUse]
    totals: Totals
    violations: tuple[str, ...]

    @property
    def feasible(self) -> bool:
        return self.status == "optimal" and not self.violations


def _totals(metrics: list[Metric]) -> Totals:
    return Totals(
        expected_cases=sum(item.expected_cases for item in metrics),
        operating_loss=sum(item.operating_loss for item in metrics),
        amu=sum(item.amu for item in metrics),
        staff_hours=sum(item.staff_hours for item in metrics),
        pen_sqft=sum(item.pen_sqft for item in metrics),
        treatment_slots=sum(item.treatment_slots for item in metrics),
    )


CAPACITY_FIELDS: tuple[str, ...] = ("staff_hours", "pen_capacity_sqft", "treatment_slots")

CapacityOverrides = dict[str, dict[str, float]]


def _capacities(
    yards: dict[str, Yard],
    staff_hours: dict[str, float] | None,
    capacities: CapacityOverrides | None = None,
) -> dict[str, Yard]:
    """Apply manager overrides. `capacities` maps yard -> {field: value} for any hard limit."""
    if not staff_hours and not capacities:
        return yards
    updated: dict[str, Yard] = {}
    for yard_id, yard in yards.items():
        changes: dict[str, float] = {}
        if staff_hours and yard_id in staff_hours:
            changes["staff_hours"] = float(staff_hours[yard_id])
        for field, value in (capacities or {}).get(yard_id, {}).items():
            if field not in CAPACITY_FIELDS:
                raise KeyError(field)
            changes[field] = float(value)
        updated[yard_id] = replace(yard, **changes) if changes else yard
    return updated


def diagnose_shortfall(
    cohorts: list[Cohort],
    metrics: dict[str, dict[str, Metric]],
    yards: dict[str, Yard],
    staff_hours: dict[str, float] | None = None,
    capacities: CapacityOverrides | None = None,
) -> tuple[str, ...]:
    """Name each yard limit that is below the least any plan could use there."""
    caps = _capacities(yards, staff_hours, capacities)
    short: list[str] = []
    for yard_id, yard in caps.items():
        members = [cohort for cohort in cohorts if cohort.yard_id == yard_id]
        if not members:
            continue
        need_staff = sum(metrics[c.cohort_id]["standard_care"].welfare_staff_floor for c in members)
        need_pen = sum(min(m.pen_sqft for m in metrics[c.cohort_id].values()) for c in members)
        need_treat = sum(min(m.treatment_slots for m in metrics[c.cohort_id].values()) for c in members)
        if need_staff > yard.staff_hours + 1e-4:
            short.append(f"{yard_id} staff needs at least {need_staff:.1f} h for standard care; it has {yard.staff_hours:.1f}.")
        if need_pen > yard.pen_capacity_sqft + 1e-2:
            short.append(f"{yard_id} pen needs at least {need_pen:,.0f} sq ft; it has {yard.pen_capacity_sqft:,.0f}.")
        if need_treat > yard.treatment_slots + 1e-4:
            short.append(
                f"{yard_id} treatment needs at least {need_treat:.1f} slots even on the lowest-case action; "
                f"it has {yard.treatment_slots:.1f}."
            )
    return tuple(short)


def _objective_coef(metric: Metric, objective: str) -> float:
    if objective == "operating_loss":
        return metric.operating_loss
    if objective == "modeled_morbidity":
        return metric.expected_cases
    if objective == "antimicrobial_exposure":
        return metric.amu
    raise KeyError(objective)


def evaluate_assignment(
    assignment: dict[str, str],
    cohorts: list[Cohort],
    metrics: dict[str, dict[str, Metric]],
    yards: dict[str, Yard],
    staff_hours: dict[str, float] | None = None,
    objective: str = "operating_loss",
    capacities: CapacityOverrides | None = None,
) -> Evaluation:
    caps = _capacities(yards, staff_hours, capacities)
    chosen: dict[str, Metric] = {}
    violations: list[str] = []
    for cohort in cohorts:
        action_id = assignment.get(cohort.cohort_id)
        if action_id not in metrics[cohort.cohort_id]:
            violations.append(f"{cohort.cohort_id} has no action.")
            continue
        metric = metrics[cohort.cohort_id][action_id]
        chosen[cohort.cohort_id] = metric
        if metric.staff_hours + _TOL < metric.welfare_staff_floor:
            violations.append(
                f"{cohort.cohort_id} staff hours are under the standard-care welfare floor."
            )
        if metric.treatment_slots + _TOL < cohort.clinically_ill_head:
            violations.append(
                f"{cohort.cohort_id} treatment slots drop cattle that are already clinically ill."
            )

    by_yard: dict[str, YardUse] = {}
    for yard_id, yard in caps.items():
        members = [chosen[c.cohort_id] for c in cohorts if c.yard_id == yard_id and c.cohort_id in chosen]
        use = YardUse(
            yard_id=yard_id,
            staff=sum(item.staff_hours for item in members),
            staff_capacity=yard.staff_hours,
            pen=sum(item.pen_sqft for item in members),
            pen_capacity=yard.pen_capacity_sqft,
            treatment=sum(item.treatment_slots for item in members),
            treatment_capacity=yard.treatment_slots,
        )
        by_yard[yard_id] = use
        if use.staff > use.staff_capacity + 1e-4:
            violations.append(
                f"{yard_id} staff hours {use.staff:.1f} exceed capacity {use.staff_capacity:.1f}."
            )
        if use.pen > use.pen_capacity + 1e-2:
            violations.append(
                f"{yard_id} pen space {use.pen:.0f} sq ft exceeds capacity {use.pen_capacity:.0f}."
            )
        if use.treatment > use.treatment_capacity + 1e-4:
            violations.append(
                f"{yard_id} treatment slots {use.treatment:.1f} exceed capacity {use.treatment_capacity:.1f}."
            )

    status = "optimal" if not violations else "infeasible"
    if violations:
        message = "Current assignment breaks a limit. " + " ".join(violations)
    else:
        message = "Feasible. Staff, pen, treatment, and the welfare floor all hold."
    return Evaluation(
        status=status,
        message=message,
        objective=objective,
        assignment=dict(assignment),
        by_cohort=chosen,
        by_yard=by_yard,
        totals=_totals(list(chosen.values())) if chosen else Totals(0, 0, 0, 0, 0, 0),
        violations=tuple(violations),
    )


def solve(
    cohorts: list[Cohort],
    metrics: dict[str, dict[str, Metric]],
    yards: dict[str, Yard],
    objective: str = "operating_loss",
    staff_hours: dict[str, float] | None = None,
    assumptions: Assumptions | None = None,
    capacities: CapacityOverrides | None = None,
) -> Evaluation:
    if objective not in OBJECTIVES:
        raise KeyError(objective)
    del assumptions  # capacities already sit on the yards; assumptions built the metrics
    caps = _capacities(yards, staff_hours, capacities)
    if not cohorts:
        return Evaluation(
            status="infeasible",
            message="No cohorts to allocate.",
            objective=objective,
            assignment={},
            by_cohort={},
            by_yard={},
            totals=Totals(0, 0, 0, 0, 0, 0),
            violations=("No cohorts to allocate.",),
        )

    problem = pulp.LpProblem("brd_allocation", pulp.LpMinimize)
    variables: dict[tuple[str, str], pulp.LpVariable] = {}
    for cohort in cohorts:
        available = []
        for action_id in ACTIONS:
            metric = metrics[cohort.cohort_id][action_id]
            if metric.staff_hours + _TOL < metric.welfare_staff_floor:
                continue
            if metric.treatment_slots + _TOL < cohort.clinically_ill_head:
                continue
            name = f"x_{cohort.cohort_id}_{action_id}".replace("-", "_")
            variables[(cohort.cohort_id, action_id)] = pulp.LpVariable(name, cat="Binary")
            available.append(action_id)
        if not available:
            return _infeasible(objective, "A cohort has no action that meets the welfare floor.")
        problem += (
            pulp.lpSum(variables[(cohort.cohort_id, action_id)] for action_id in available) == 1,
            f"one_{cohort.cohort_id}".replace("-", "_"),
        )

    def chosen_sum(cohort_id: str, getter):
        return pulp.lpSum(
            variables[(cohort_id, action_id)] * getter(metrics[cohort_id][action_id])
            for action_id in ACTIONS
            if (cohort_id, action_id) in variables
        )

    for cohort in cohorts:
        cid = cohort.cohort_id
        floor = metrics[cid]["standard_care"].welfare_staff_floor
        problem += (
            chosen_sum(cid, lambda metric: metric.staff_hours) >= floor,
            f"welfare_staff_{cid}".replace("-", "_"),
        )
        problem += (
            chosen_sum(cid, lambda metric: metric.treatment_slots) >= cohort.clinically_ill_head,
            f"welfare_treat_{cid}".replace("-", "_"),
        )

    for yard_id, yard in caps.items():
        members = [cohort for cohort in cohorts if cohort.yard_id == yard_id]
        if not members:
            continue
        problem += (
            pulp.lpSum(chosen_sum(cohort.cohort_id, lambda metric: metric.staff_hours) for cohort in members)
            <= yard.staff_hours + _TOL,
            f"staff_{yard_id}".replace("-", "_"),
        )
        problem += (
            pulp.lpSum(chosen_sum(cohort.cohort_id, lambda metric: metric.pen_sqft) for cohort in members)
            <= yard.pen_capacity_sqft + _TOL,
            f"pen_{yard_id}".replace("-", "_"),
        )
        problem += (
            pulp.lpSum(
                chosen_sum(cohort.cohort_id, lambda metric: metric.treatment_slots) for cohort in members
            )
            <= yard.treatment_slots + _TOL,
            f"treat_{yard_id}".replace("-", "_"),
        )

    problem += pulp.lpSum(
        variables[(cohort.cohort_id, action_id)]
        * _objective_coef(metrics[cohort.cohort_id][action_id], objective)
        for cohort in cohorts
        for action_id in ACTIONS
        if (cohort.cohort_id, action_id) in variables
    )

    status = problem.solve(pulp.PULP_CBC_CMD(msg=False))
    if pulp.LpStatus[status] != "Optimal":
        short = diagnose_shortfall(cohorts, metrics, yards, staff_hours, capacities)
        detail = " ".join(short) if short else "Each limit can be met alone, but not all of them together."
        return _infeasible(
            objective,
            "No feasible plan. Staff hours, pen space, or treatment throughput cannot cover "
            "the welfare floor: standard-care monitoring, and treatment of cattle that are "
            "already clinically ill. The model will not drop that care. " + detail,
        )

    assignment: dict[str, str] = {}
    for cohort in cohorts:
        picked = [
            action_id
            for action_id in ACTIONS
            if (cohort.cohort_id, action_id) in variables
            and (pulp.value(variables[(cohort.cohort_id, action_id)]) or 0) > 0.5
        ]
        if len(picked) != 1:
            return _infeasible(objective, "The solver did not return one action per cohort.")
        assignment[cohort.cohort_id] = picked[0]

    evaluation = evaluate_assignment(
        assignment, cohorts, metrics, yards, staff_hours=staff_hours, objective=objective, capacities=capacities
    )
    if evaluation.violations:
        return _infeasible(objective, evaluation.message)
    return evaluation


def _infeasible(objective: str, message: str) -> Evaluation:
    return Evaluation(
        status="infeasible",
        message=message,
        objective=objective,
        assignment={},
        by_cohort={},
        by_yard={},
        totals=Totals(0, 0, 0, 0, 0, 0),
        violations=(message,),
    )
