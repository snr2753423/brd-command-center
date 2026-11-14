from __future__ import annotations

from dataclasses import replace

import pytest

from src.assumptions import Assumptions
from src.schema import Cohort


@pytest.fixture
def assumptions() -> Assumptions:
    return Assumptions()


def reference_cohort(**overrides: object) -> Cohort:
    base = dict(
        cohort_id="REF",
        yard_id="TX-A",
        cohort_name="Reference",
        head_count=100,
        sex="steer",
        arrival_weight_lb=750.0,
        source_count=1,
        travel_distance_mi=100.0,
        weaning_status="known_weaned",
        vaccination_status="known_vaccinated",
        ration_transition_status="adapted",
        bunk_space_in_per_head=12.0,
        arrival_quarter="Q2",
        clinically_ill_head=0,
    )
    base.update(overrides)
    return Cohort(**base)


def with_cost(assumptions: Assumptions, morbidity_cost: float) -> Assumptions:
    return replace(assumptions, morbidity_cost_per_case=morbidity_cost)
