"""Plain-text decision summary. Not a prescription."""

from __future__ import annotations

from .assumptions import UNKNOWN_PLANNING_LABEL, Assumptions, case_fatality
from .format import money, num, pct
from .optimizer import Evaluation
from .pipeline import Context
from .practice import action_label, rule_text
from .schema import ACTION_LABEL, OBJECTIVE_LABEL


def decision_summary(
    context: Context,
    recommended: Evaluation,
    practice: Evaluation,
    scenario: str,
    staff_note: str,
) -> str:
    assumptions: Assumptions = context.assumptions
    lines: list[str] = [
        "BRD Command Center — decision summary",
        "SYNTHETIC DATA. Not a prescription. Published constants are cited inputs, not validated accuracy.",
        "",
        f"Scenario: {scenario}",
        f"Objective: {OBJECTIVE_LABEL.get(recommended.objective, recommended.objective)}",
        staff_note,
        "",
        rule_text(assumptions),
        "",
        "Assumptions",
        f"- High-risk benchmark {pct(assumptions.high_risk_benchmark)} (published, Rojas et al. 2022)",
        f"- Morbidity cost {money(assumptions.morbidity_cost_per_case)} per expected case (published, Rojas 2022 Table 3)",
        f"- Metaphylaxis {money(assumptions.metaphylaxis_cost_per_head)} per at-risk head (published, Rojas 2022 Table 3)",
        f"- Metaphylaxis efficacy {pct(assumptions.metaphylaxis_efficacy)} (published, Rojas 2022 Table 3)",
        f"- Enhanced surveillance efficacy {pct(assumptions.surveillance_efficacy)} (assumption)",
        f"- Supportive management efficacy {pct(assumptions.supportive_efficacy)} (assumption)",
        f"- Unknown fields planned at: {UNKNOWN_PLANNING_LABEL[assumptions.unknown_planning]}",
        f"- BRD deaths per case {pct(case_fatality(600, assumptions))} under "
        f"{assumptions.death_weight_split_lb:.0f} lb, {pct(case_fatality(800, assumptions))} at or above "
        "(derived from USDA 2019 death rates, the BRD share of deaths, and Rojas 2022 mean morbidity)",
        "- Medication actions require veterinary review. This file does not prescribe.",
        "",
        f"Recommended plan: {recommended.status}.",
        recommended.message,
        "",
    ]

    if practice.violations:
        lines.append("Current practice breaks a limit:")
        lines.extend(f"- {item}" for item in practice.violations)
    else:
        lines.append("Current practice fits the same limits.")
    lines.append("")

    if recommended.feasible:
        lines.extend(
            [
                "Totals (recommended vs current practice)",
                f"- Expected cases: {num(recommended.totals.expected_cases)} vs {num(practice.totals.expected_cases)}",
                f"- Operating loss: {money(recommended.totals.operating_loss)} vs {money(practice.totals.operating_loss)}",
                f"- Antimicrobial exposure: {num(recommended.totals.amu)} vs {num(practice.totals.amu)} synthetic units",
                f"- Expected BRD deaths: {num(recommended.totals.expected_deaths)} vs {num(practice.totals.expected_deaths)}",
                "",
                "Cohorts",
            ]
        )
        for cohort_id in context.ranked_ids:
            cohort = next(item for item in context.cohorts if item.cohort_id == cohort_id)
            scored = context.scored[cohort_id]
            metric = recommended.by_cohort[cohort_id]
            practice_action = context.practice[cohort_id]
            if scored.confident_call:
                call = f"confidence {scored.confidence.level}"
            else:
                missing = ", ".join(scored.confidence.critical_missing)
                call = f"No confident recommendation. Missing: {missing}"
            vet = "yes" if metric.veterinary_review_required else "no"
            lines.append(
                f"- {cohort.cohort_id} {cohort.cohort_name} | {action_label(metric.action_id)} | "
                f"current practice {ACTION_LABEL[practice_action]} | {call} | "
                f"planning morbidity {pct(metric.morbidity)} | "
                f"cases {num(metric.expected_cases)} | deaths {num(metric.expected_deaths)} | "
                f"loss {money(metric.operating_loss)} | "
                f"exposure {num(metric.amu)} | staff {num(metric.staff_hours)} h | "
                f"veterinary review required: {vet}"
            )
        lines.extend(["", "Yard limits"])
        for yard_id in sorted(recommended.by_yard):
            use = recommended.by_yard[yard_id]
            lines.append(
                f"- {yard_id} staff {num(use.staff)}/{num(use.staff_capacity)} h | "
                f"pen {num(use.pen, 0)}/{num(use.pen_capacity, 0)} sq ft | "
                f"treatment {num(use.treatment)}/{num(use.treatment_capacity)} slots"
            )
    else:
        lines.append("No recommended allocation is included, because the solve is infeasible.")

    lines.extend(
        [
            "",
            "A cohort with unknown fields is planned on its unknown-state range, not on a",
            "filled-in typical value. Missing transport, weaning, or vaccination still withholds",
            "a confident call. Deaths are derived from published rates and follow cases.",
            "Weather-stress flags are synthetic yard fields. There is no live weather API.",
        ]
    )
    return "\n".join(lines) + "\n"
