"""Seed yard capacities from the same metrics the optimizer uses.

Shortage yards are full on pen. Staff equals the standard-care floor, except
TX-A, which has exactly enough extra hours to put the priority cohort on
enhanced surveillance. Treatment capacity equals the standard-care case load,
so three yards sit on that limit and a higher-case plan cannot be added.
"""

from __future__ import annotations

import math

from .assumptions import Assumptions
from .economics import metrics_by_action
from .pipeline import build_context
from .risk_model import score_cohort
from .schema import DEMO_YARD_ID, PRIORITY_COHORT_ID, Cohort, Yard


def _pad(value: float) -> float:
    return math.ceil(value * 10000 - 1e-6) / 10000


def _identities() -> list[dict[str, object]]:
    return [
        {
            "yard_id": "TX-A",
            "yard_name": "Panhandle North",
            "region": "Texas Panhandle",
            "weather_stress_flag": False,
            "bottleneck": "staff and treatment",
        },
        {
            "yard_id": "TX-B",
            "yard_name": "Panhandle South",
            "region": "Texas Panhandle",
            "weather_stress_flag": False,
            "bottleneck": "staff",
        },
        {
            "yard_id": "KS-A",
            "yard_name": "High Plains West",
            "region": "western Kansas",
            "weather_stress_flag": True,
            "bottleneck": "staff",
        },
        {
            "yard_id": "KS-B",
            "yard_name": "High Plains East",
            "region": "western Kansas",
            "weather_stress_flag": False,
            "bottleneck": "pen",
        },
    ]


def _metrics(cohorts: list[Cohort], assumptions: Assumptions):
    weather = {str(item["yard_id"]): bool(item["weather_stress_flag"]) for item in _identities()}
    # Score without capacities. Weather is the only yard input the risk model needs.
    scored = {
        cohort.cohort_id: score_cohort(cohort, weather[cohort.yard_id], assumptions) for cohort in cohorts
    }
    return {
        cohort.cohort_id: metrics_by_action(cohort, scored[cohort.cohort_id], assumptions)
        for cohort in cohorts
    }


def build_yards(cohorts: list[Cohort], assumptions: Assumptions, mode: str) -> list[Yard]:
    if mode not in {"shortage", "normal"}:
        raise KeyError(mode)
    table = _metrics(cohorts, assumptions)
    if PRIORITY_COHORT_ID not in table:
        raise KeyError("priority cohort is missing")
    priority_yard = next(cohort.yard_id for cohort in cohorts if cohort.cohort_id == PRIORITY_COHORT_ID)
    if priority_yard != DEMO_YARD_ID:
        raise ValueError("priority cohort must sit in TX-A")

    yards: list[Yard] = []
    for identity in _identities():
        yard_id = str(identity["yard_id"])
        members = [cohort for cohort in cohorts if cohort.yard_id == yard_id]
        standard_staff = sum(table[cohort.cohort_id]["standard_care"].staff_hours for cohort in members)
        surveillance_staff = sum(
            table[cohort.cohort_id]["enhanced_surveillance"].staff_hours for cohort in members
        )
        standard_treatment = sum(
            table[cohort.cohort_id]["standard_care"].treatment_slots for cohort in members
        )
        pen = sum(cohort.head_count * assumptions.sqft_per_head for cohort in members)

        if mode == "shortage":
            if yard_id == DEMO_YARD_ID:
                priority_gap = (
                    table[PRIORITY_COHORT_ID]["enhanced_surveillance"].staff_hours
                    - table[PRIORITY_COHORT_ID]["standard_care"].staff_hours
                )
                staff = _pad(standard_staff + priority_gap)
            else:
                staff = _pad(standard_staff)
            demo_staff = _pad(standard_staff)
            treatment = _pad(standard_treatment)
            pen_capacity = pen
        else:
            staff = _pad(surveillance_staff * 1.25)
            demo_staff = staff
            treatment = _pad(standard_treatment * 1.25)
            pen_capacity = pen * 1.5

        yards.append(
            Yard(
                yard_id=yard_id,
                yard_name=str(identity["yard_name"]),
                region=str(identity["region"]),
                weather_stress_flag=bool(identity["weather_stress_flag"]),
                pen_capacity_sqft=pen_capacity,
                staff_hours=staff,
                demo_staff_hours=demo_staff,
                treatment_slots=treatment,
                bottleneck=str(identity["bottleneck"]) if mode == "shortage" else "relaxed",
            )
        )
    # Touch the pipeline import so a mismatch between score paths fails at generation time.
    build_context(cohorts, yards, assumptions)
    return yards
