"""Adjustable planning assumptions.

Published constants come from Rojas et al. 2022 (Pathogens 11:442): the 15%
high-risk cutoff, and Table 3's $23.60 metaphylaxis cost per animal, $151.18
cost of a morbid animal, and 50% metaphylaxis efficacy. They are cited inputs,
not accuracy this package measured, and this package does not report an AUC.
Everything else here is an adjustable assumption.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Assumptions:
    # Published: Rojas et al. 2022, 15% BRD morbidity in the first 45 days on feed.
    high_risk_benchmark: float = 0.15

    # Published: Rojas et al. 2022, Table 3 (cost of morbid animal; cost of a single
    # metaphylactic treatment per animal, from USDA NAHMS 2011; efficacy set at 0.5).
    # Dollars are not mixed: case loss is not the drug invoice.
    morbidity_cost_per_case: float = 151.18
    metaphylaxis_cost_per_head: float = 23.60
    metaphylaxis_efficacy: float = 0.50

    # Effect sizes and supply costs for the other actions. Assumptions.
    surveillance_efficacy: float = 0.18
    supportive_efficacy: float = 0.30
    standard_efficacy: float = 0.0
    surveillance_program_cost_per_head: float = 1.50
    supportive_program_cost_per_head: float = 4.00

    # Synthetic exposure units. Metaphylaxis and later treatment are separate.
    therapeutic_exposure_per_case: float = 1.0
    metaphylaxis_exposure_per_head: float = 1.0

    # Arrival-week labor hours per head. Synthetic rates. Standard is the floor.
    staff_hours_per_head: tuple[tuple[str, float], ...] = (
        ("standard_care", 0.25),
        ("supportive_management", 0.40),
        ("vet_review", 0.55),
        ("enhanced_surveillance", 0.90),
    )

    # Supportive management needs more pen. Other actions sit at the base density.
    sqft_per_head: float = 250.0
    pen_factor: tuple[tuple[str, float], ...] = (
        ("standard_care", 1.0),
        ("enhanced_surveillance", 1.0),
        ("vet_review", 1.0),
        ("supportive_management", 1.25),
    )

    # Current-practice rule. Not the same thing as the 15% model benchmark.
    light_weight_lb: float = 600.0
    multiple_source_min: int = 2

    # Log-odds deviations from the reference profile. Magnitudes are assumptions.
    # Reference-profile morbidity (the intercept). Calibrated so a synthetic population of
    # 1,733 cohorts averages Rojas et al. 2022's 6.30% (see src/calibration.py,
    # data/calibrate_to_rojas.py). The reference profile is a low-risk arrival.
    reference_morbidity: float = 0.01092
    weight_reference_lb: float = 750.0
    weight_log_odds_per_lb: float = -0.0016
    sex_log_odds: tuple[tuple[str, float], ...] = (
        ("steer", 0.0),
        ("heifer", 0.08),
        ("mixed", 0.12),
    )
    source_log_odds_per_extra: float = 0.09
    distance_reference_mi: float = 100.0
    distance_log_odds_per_mile: float = 0.00035
    weaning_unweaned_log_odds: float = 0.16
    vaccination_unvaccinated_log_odds: float = 0.14
    ration_transitioning_log_odds: float = 0.10
    bunk_reference_in: float = 12.0
    bunk_log_odds_per_inch_below: float = 0.025
    quarter_log_odds: tuple[tuple[str, float], ...] = (
        ("Q1", 0.10),
        ("Q2", 0.0),
        ("Q3", 0.04),
        ("Q4", 0.14),
    )
    weather_log_odds: float = 0.12
    # Multiplier on every coefficient above. Calibrated so the score separates high- from
    # low-risk cohorts at AUC 0.735, the midpoint of Rojas's published 0.682-0.789.
    risk_scale: float = 2.0807

    # Unexplained cohort-to-cohort spread on the logit scale. Calibrated so 10.85% of the
    # synthetic population lands at or above 15%, as in Rojas et al. 2022. Used for
    # P(morbidity >= 15%) and the 90% band. Unknown fields widen it further.
    sigma_base: float = 1.1159
    sigma_missing: tuple[tuple[str, float], ...] = (
        ("travel_distance_mi", 0.35),
        ("weaning_status", 0.28),
        ("vaccination_status", 0.28),
        ("ration_transition_status", 0.12),
        ("bunk_space_in_per_head", 0.10),
        ("sex", 0.08),
        ("arrival_quarter", 0.10),
    )

    # How a cohort with unknown fields is planned. Dropping an unknown field's term
    # is the same as giving it the reference value, so the default plans on the
    # worst case across the unknown states instead. Options: worst_case, midpoint, reference.
    unknown_planning: str = "worst_case"

    # Mortality. Published inputs, derived case fatality (see case_fatality below).
    # USDA APHIS NAHMS Feedlot 2017 (2019 report), table A.6: share of cattle that died,
    # placed under 700 lb versus 700 lb or more.
    death_rate_light: float = 0.023
    death_rate_heavy: float = 0.012
    death_weight_split_lb: float = 700.0
    # BRD causes 50-80% of feedlot deaths (Weber et al. 2024, citing Edwards 1996). Midpoint.
    brd_share_of_deaths: float = 0.65
    # 65-80% of BRD cases occur in the first 45 days on feed (Adekunle and Kaniyamattam 2026). Midpoint.
    brd_first45_share: float = 0.725
    # Mean 45-day BRD morbidity across 1,733 cohorts (Rojas et al. 2022).
    population_morbidity_45d: float = 0.063

    # Bounds used only to show the range across unknown states. Not imputed values.
    distance_band_low_mi: float = 50.0
    distance_band_high_mi: float = 800.0
    bunk_band_low_in: float = 6.0
    bunk_band_high_in: float = 18.0

    # Preset pair for the assumption control. Default, then a stress value that
    # can flip the selected action. The stress value is not a published cost.
    flip_morbidity_cost_per_case: float = 450.0

    def staff_rate(self, action_id: str) -> float:
        return dict(self.staff_hours_per_head)[action_id]

    def pen_factor_for(self, action_id: str) -> float:
        return dict(self.pen_factor)[action_id]

    def sex_effect(self, sex: str) -> float | None:
        table = dict(self.sex_log_odds)
        if sex not in table:
            return None
        return table[sex]

    def quarter_effect(self, quarter: str) -> float | None:
        table = dict(self.quarter_log_odds)
        if quarter not in table:
            return None
        return table[quarter]

    def missing_sigma(self, key: str) -> float:
        return dict(self.sigma_missing).get(key, 0.0)


UNKNOWN_PLANNING_LABEL: dict[str, str] = {
    "worst_case": "Worst case of the unknown-state range",
    "midpoint": "Midpoint of the unknown-state range",
    "reference": "Reference profile (same as filling unknowns with reference values)",
}


def case_fatality(arrival_weight_lb: float, assumptions: Assumptions) -> float:
    """BRD deaths per 45-day BRD case, by placement weight class.

    Per head, BRD deaths over the feeding period are the all-cause death rate times
    the BRD share of deaths. The first-45-day share of those, divided by the mean
    45-day morbidity, gives deaths per case. Deaths are assumed to follow cases, so an
    action that prevents cases prevents the matching deaths. Derived, not measured.
    """
    rate = (
        assumptions.death_rate_light
        if arrival_weight_lb < assumptions.death_weight_split_lb
        else assumptions.death_rate_heavy
    )
    return (
        rate
        * assumptions.brd_share_of_deaths
        * assumptions.brd_first45_share
        / assumptions.population_morbidity_45d
    )


def efficacy_for(action_id: str, assumptions: Assumptions) -> float:
    if action_id == "vet_review":
        return assumptions.metaphylaxis_efficacy
    if action_id == "enhanced_surveillance":
        return assumptions.surveillance_efficacy
    if action_id == "supportive_management":
        return assumptions.supportive_efficacy
    if action_id == "standard_care":
        return assumptions.standard_efficacy
    raise KeyError(action_id)
