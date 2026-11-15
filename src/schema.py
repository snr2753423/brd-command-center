"""Shared records, column names, and action labels."""

from __future__ import annotations

from dataclasses import dataclass

COHORT_COLUMNS: tuple[str, ...] = (
    "cohort_id",
    "yard_id",
    "cohort_name",
    "head_count",
    "sex",
    "arrival_weight_lb",
    "source_count",
    "travel_distance_mi",
    "weaning_status",
    "vaccination_status",
    "ration_transition_status",
    "bunk_space_in_per_head",
    "arrival_quarter",
    "clinically_ill_head",
)

YARD_COLUMNS: tuple[str, ...] = (
    "yard_id",
    "yard_name",
    "region",
    "weather_stress_flag",
    "pen_capacity_sqft",
    "staff_hours",
    "demo_staff_hours",
    "treatment_slots",
    "bottleneck",
)

ACTIONS: tuple[str, ...] = (
    "standard_care",
    "enhanced_surveillance",
    "supportive_management",
    "vet_review",
)

ACTION_LABEL: dict[str, str] = {
    "standard_care": "Standard care",
    "enhanced_surveillance": "Enhanced surveillance",
    "supportive_management": "Supportive management",
    "vet_review": "Veterinary review",
}

OBJECTIVES: tuple[str, ...] = (
    "operating_loss",
    "modeled_morbidity",
    "antimicrobial_exposure",
    "modeled_mortality",
)

OBJECTIVE_LABEL: dict[str, str] = {
    "operating_loss": "Operating loss",
    "modeled_morbidity": "Modeled morbidity",
    "antimicrobial_exposure": "Antimicrobial exposure",
    "modeled_mortality": "Expected BRD deaths",
}

PRIORITY_COHORT_ID = "TXA-4401"
INCOMPLETE_COHORT_ID = "TXB-4388"
DEMO_YARD_ID = "TX-A"

SEX_VALUES = ("steer", "heifer", "mixed", "unknown")
WEANING_VALUES = ("known_weaned", "known_unweaned", "unknown")
VACCINATION_VALUES = ("known_vaccinated", "known_unvaccinated", "unknown")
RATION_VALUES = ("adapted", "transitioning", "unknown")
QUARTER_VALUES = ("Q1", "Q2", "Q3", "Q4", "unknown")

CRITICAL_FIELDS = ("travel_distance_mi", "weaning_status", "vaccination_status")


@dataclass(frozen=True)
class Cohort:
    cohort_id: str
    yard_id: str
    cohort_name: str
    head_count: int
    sex: str
    arrival_weight_lb: float
    source_count: int
    travel_distance_mi: float | None
    weaning_status: str
    vaccination_status: str
    ration_transition_status: str
    bunk_space_in_per_head: float | None
    arrival_quarter: str
    clinically_ill_head: int


@dataclass(frozen=True)
class Yard:
    yard_id: str
    yard_name: str
    region: str
    weather_stress_flag: bool
    pen_capacity_sqft: float
    staff_hours: float
    demo_staff_hours: float
    treatment_slots: float
    bottleneck: str
