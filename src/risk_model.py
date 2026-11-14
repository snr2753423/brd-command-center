"""Explainable 45-day morbidity. Separate from P(morbidity above 15%)."""

from __future__ import annotations

import math
from dataclasses import dataclass, replace

from .assumptions import Assumptions
from .schema import Cohort
from .uncertainty import (
    Confidence,
    assess_confidence,
    expit,
    logit,
    p_exceeds,
    probability_interval,
)


@dataclass(frozen=True)
class Driver:
    key: str
    label: str
    domain: str
    status: str  # known | unknown
    value: str | None
    contribution: float | None
    evidence: str
    note: str


@dataclass(frozen=True)
class Scored:
    cohort: Cohort
    weather_stress_flag: bool
    drivers: tuple[Driver, ...]
    logit: float
    sigma: float
    morbidity: float
    p_high_risk: float
    above_benchmark: bool
    confidence: Confidence
    state_low: float
    state_high: float
    interval_low: float
    interval_high: float

    @property
    def confident_call(self) -> bool:
        return self.confidence.confident_call


def _num(value: float | None, digits: int = 1) -> str:
    if value is None:
        return "unknown"
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f"{value:.{digits}f}"


def _driver(
    key: str,
    label: str,
    domain: str,
    status: str,
    value: str | None,
    contribution: float | None,
    note: str,
    evidence: str = "assumption",
) -> Driver:
    return Driver(key, label, domain, status, value, contribution, evidence, note)


def point_drivers(
    cohort: Cohort, weather_stress: bool, assumptions: Assumptions
) -> tuple[list[Driver], float]:
    """Log-odds from known fields only. Unknown fields contribute nothing and are not filled."""
    drivers: list[Driver] = []
    total = logit(assumptions.reference_morbidity)

    drivers.append(
        _driver(
            "head_count",
            "Head count",
            "animal",
            "known",
            str(cohort.head_count),
            None,
            "Scales cases and resources. It does not change the per-head rate.",
            evidence="synthetic",
        )
    )

    sex_effect = assumptions.sex_effect(cohort.sex)
    if sex_effect is None or cohort.sex == "unknown":
        drivers.append(
            _driver(
                "sex",
                "Sex",
                "animal",
                "unknown",
                None,
                None,
                "Unknown. Not set to steer.",
            )
        )
    else:
        drivers.append(
            _driver(
                "sex",
                "Sex",
                "animal",
                "known",
                cohort.sex,
                sex_effect,
                "Known sex. Coefficient is an assumption.",
            )
        )
        total += sex_effect

    weight_effect = assumptions.weight_log_odds_per_lb * (
        cohort.arrival_weight_lb - assumptions.weight_reference_lb
    )
    drivers.append(
        _driver(
            "arrival_weight_lb",
            "Arrival weight",
            "animal",
            "known",
            f"{_num(cohort.arrival_weight_lb, 0)} lb",
            weight_effect,
            f"Per pound versus {assumptions.weight_reference_lb:.0f} lb. Coefficient is an assumption.",
        )
    )
    total += weight_effect

    extra_sources = max(0, cohort.source_count - 1)
    source_effect = assumptions.source_log_odds_per_extra * extra_sources
    drivers.append(
        _driver(
            "source_count",
            "Source count",
            "management",
            "known",
            str(cohort.source_count),
            source_effect,
            "Each source past the first. Coefficient is an assumption.",
        )
    )
    total += source_effect

    if cohort.travel_distance_mi is None:
        drivers.append(
            _driver(
                "travel_distance_mi",
                "Travel distance",
                "management",
                "unknown",
                None,
                None,
                "Unknown. Not set to the 100-mile reference.",
            )
        )
    else:
        distance_effect = assumptions.distance_log_odds_per_mile * (
            cohort.travel_distance_mi - assumptions.distance_reference_mi
        )
        drivers.append(
            _driver(
                "travel_distance_mi",
                "Travel distance",
                "management",
                "known",
                f"{_num(cohort.travel_distance_mi, 0)} mi",
                distance_effect,
                f"Versus {assumptions.distance_reference_mi:.0f} miles. Coefficient is an assumption.",
            )
        )
        total += distance_effect

    if cohort.weaning_status == "unknown":
        drivers.append(
            _driver(
                "weaning_status",
                "Weaning",
                "management",
                "unknown",
                None,
                None,
                "Unknown. Not set to known weaned.",
            )
        )
    else:
        wean_effect = (
            assumptions.weaning_unweaned_log_odds
            if cohort.weaning_status == "known_unweaned"
            else 0.0
        )
        drivers.append(
            _driver(
                "weaning_status",
                "Weaning",
                "management",
                "known",
                cohort.weaning_status,
                wean_effect,
                "Known history. The unweaned coefficient is an assumption.",
            )
        )
        total += wean_effect

    if cohort.vaccination_status == "unknown":
        drivers.append(
            _driver(
                "vaccination_status",
                "Vaccination",
                "management",
                "unknown",
                None,
                None,
                "Unknown. Not set to known vaccinated.",
            )
        )
    else:
        vacc_effect = (
            assumptions.vaccination_unvaccinated_log_odds
            if cohort.vaccination_status == "known_unvaccinated"
            else 0.0
        )
        drivers.append(
            _driver(
                "vaccination_status",
                "Vaccination",
                "management",
                "known",
                cohort.vaccination_status,
                vacc_effect,
                "Known history. The unvaccinated coefficient is an assumption.",
            )
        )
        total += vacc_effect

    if cohort.ration_transition_status == "unknown":
        drivers.append(
            _driver(
                "ration_transition_status",
                "Ration transition",
                "nutrition",
                "unknown",
                None,
                None,
                "Unknown. Not set to adapted.",
            )
        )
    else:
        ration_effect = (
            assumptions.ration_transitioning_log_odds
            if cohort.ration_transition_status == "transitioning"
            else 0.0
        )
        drivers.append(
            _driver(
                "ration_transition_status",
                "Ration transition",
                "nutrition",
                "known",
                cohort.ration_transition_status,
                ration_effect,
                "Known ration state. Coefficient is an assumption.",
            )
        )
        total += ration_effect

    if cohort.bunk_space_in_per_head is None:
        drivers.append(
            _driver(
                "bunk_space_in_per_head",
                "Bunk space",
                "nutrition",
                "unknown",
                None,
                None,
                "Unknown. Not set to 12 inches.",
            )
        )
    else:
        gap = assumptions.bunk_reference_in - cohort.bunk_space_in_per_head
        bunk_effect = assumptions.bunk_log_odds_per_inch_below * max(0.0, gap)
        drivers.append(
            _driver(
                "bunk_space_in_per_head",
                "Bunk space",
                "nutrition",
                "known",
                f"{_num(cohort.bunk_space_in_per_head, 1)} in",
                bunk_effect,
                f"Inches under {assumptions.bunk_reference_in:.0f}. Coefficient is an assumption.",
            )
        )
        total += bunk_effect

    quarter_effect = assumptions.quarter_effect(cohort.arrival_quarter)
    if quarter_effect is None or cohort.arrival_quarter == "unknown":
        drivers.append(
            _driver(
                "arrival_quarter",
                "Arrival quarter",
                "environment",
                "unknown",
                None,
                None,
                "Unknown. Not set to Q2.",
            )
        )
    else:
        drivers.append(
            _driver(
                "arrival_quarter",
                "Arrival quarter",
                "environment",
                "known",
                cohort.arrival_quarter,
                quarter_effect,
                "Season coefficient is an assumption, not a weather feed.",
            )
        )
        total += quarter_effect

    weather_effect = assumptions.weather_log_odds if weather_stress else 0.0
    drivers.append(
        _driver(
            "weather_stress_flag",
            "Yard weather-stress flag",
            "environment",
            "known",
            "yes" if weather_stress else "no",
            weather_effect,
            "Synthetic yard flag. There is no live weather API. Coefficient is an assumption.",
            evidence="synthetic",
        )
    )
    total += weather_effect
    return drivers, total


def _sigma(drivers: list[Driver], assumptions: Assumptions) -> float:
    sigma = assumptions.sigma_base
    for driver in drivers:
        if driver.status == "unknown":
            sigma += assumptions.missing_sigma(driver.key)
    return sigma


def _state_grid(cohort: Cohort, assumptions: Assumptions) -> list[dict[str, object]]:
    axes: list[tuple[str, list[object]]] = []
    if cohort.travel_distance_mi is None:
        axes.append(
            (
                "travel_distance_mi",
                [assumptions.distance_band_low_mi, assumptions.distance_band_high_mi],
            )
        )
    if cohort.weaning_status == "unknown":
        axes.append(("weaning_status", ["known_weaned", "known_unweaned"]))
    if cohort.vaccination_status == "unknown":
        axes.append(("vaccination_status", ["known_vaccinated", "known_unvaccinated"]))
    if cohort.ration_transition_status == "unknown":
        axes.append(("ration_transition_status", ["adapted", "transitioning"]))
    if cohort.bunk_space_in_per_head is None:
        axes.append(
            ("bunk_space_in_per_head", [assumptions.bunk_band_low_in, assumptions.bunk_band_high_in])
        )
    if cohort.sex == "unknown":
        axes.append(("sex", ["steer", "heifer", "mixed"]))
    if cohort.arrival_quarter == "unknown":
        axes.append(("arrival_quarter", ["Q1", "Q2", "Q3", "Q4"]))
    combos: list[dict[str, object]] = [{}]
    for key, options in axes:
        combos = [{**combo, key: option} for combo in combos for option in options]
    return combos


def score_cohort(cohort: Cohort, weather_stress: bool, assumptions: Assumptions) -> Scored:
    drivers, point = point_drivers(cohort, weather_stress, assumptions)
    sigma = _sigma(drivers, assumptions)
    morbidity = expit(point)
    missing = tuple(driver.key for driver in drivers if driver.status == "unknown")
    confidence = assess_confidence(missing)
    state_values = []
    for overrides in _state_grid(cohort, assumptions):
        tweaked = replace(cohort, **overrides)
        _, tweaked_logit = point_drivers(tweaked, weather_stress, assumptions)
        state_values.append(expit(tweaked_logit))
    interval_low, interval_high = probability_interval(point, sigma)
    return Scored(
        cohort=cohort,
        weather_stress_flag=weather_stress,
        drivers=tuple(drivers),
        logit=point,
        sigma=sigma,
        morbidity=morbidity,
        p_high_risk=p_exceeds(point, sigma, assumptions.high_risk_benchmark),
        above_benchmark=morbidity >= assumptions.high_risk_benchmark,
        confidence=confidence,
        state_low=min(state_values),
        state_high=max(state_values),
        interval_low=interval_low,
        interval_high=interval_high,
    )


def why_line(scored: Scored) -> str:
    ranked = [
        driver
        for driver in scored.drivers
        if driver.contribution is not None and driver.key != "head_count"
    ]
    ranked.sort(key=lambda driver: abs(driver.contribution or 0.0), reverse=True)
    parts: list[str] = []
    for driver in ranked[:3]:
        effect = driver.contribution or 0.0
        if effect > 1e-9:
            direction = "raises the estimate"
        elif effect < -1e-9:
            direction = "lowers the estimate"
        else:
            direction = "sits on the reference"
        parts.append(f"{driver.label} {direction}")
    if not parts:
        return "No known rate drivers."
    return "; ".join(parts)


def domain_summary(scored: Scored) -> dict[str, list[Driver]]:
    grouped = {"animal": [], "management": [], "nutrition": [], "environment": []}
    for driver in scored.drivers:
        grouped[driver.domain].append(driver)
    return grouped


def reference_logit(assumptions: Assumptions | None = None) -> float:
    assumptions = assumptions or Assumptions()
    if not 0 < assumptions.reference_morbidity < 1:
        raise ValueError("reference morbidity must sit between 0 and 1")
    return math.log(assumptions.reference_morbidity / (1 - assumptions.reference_morbidity))
