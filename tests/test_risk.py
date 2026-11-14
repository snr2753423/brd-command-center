from __future__ import annotations

from src.assumptions import Assumptions
from src.data_loader import load_demo
from src.pipeline import build_context
from src.risk_model import score_cohort
from src.schema import INCOMPLETE_COHORT_ID, PRIORITY_COHORT_ID
from tests.conftest import reference_cohort


def test_reference_profile_is_eight_percent():
    scored = score_cohort(reference_cohort(), weather_stress=False, assumptions=Assumptions())
    assert scored.morbidity == pytest_approx(0.08)
    assert scored.confident_call
    assert scored.confidence.level == "confident"
    assert scored.p_high_risk != pytest_approx(scored.morbidity)
    assert scored.above_benchmark is False


def test_lighter_weight_and_weather_raise_the_estimate():
    assumptions = Assumptions()
    base = score_cohort(reference_cohort(), False, assumptions)
    lighter = score_cohort(reference_cohort(arrival_weight_lb=540), False, assumptions)
    weather = score_cohort(reference_cohort(), True, assumptions)
    more_sources = score_cohort(reference_cohort(source_count=4), False, assumptions)
    assert lighter.morbidity > base.morbidity
    assert weather.morbidity > base.morbidity
    assert more_sources.morbidity > base.morbidity


def test_missing_transport_is_not_imputed():
    assumptions = Assumptions()
    scored = score_cohort(reference_cohort(travel_distance_mi=None), False, assumptions)
    travel = next(driver for driver in scored.drivers if driver.key == "travel_distance_mi")
    assert travel.status == "unknown"
    assert travel.value is None
    assert travel.contribution is None
    assert "not set" in travel.note.lower()
    assert scored.confident_call is False
    assert scored.confidence.level == "withheld"
    assert scored.state_high > scored.state_low
    filled = score_cohort(reference_cohort(travel_distance_mi=800), False, assumptions)
    short = score_cohort(reference_cohort(travel_distance_mi=50), False, assumptions)
    assert filled.morbidity != short.morbidity


def test_missing_health_history_withholds_the_call():
    scored = score_cohort(
        reference_cohort(weaning_status="unknown", vaccination_status="unknown"),
        False,
        Assumptions(),
    )
    assert scored.confident_call is False
    weaning = next(driver for driver in scored.drivers if driver.key == "weaning_status")
    assert weaning.value is None
    assert "not set to known weaned" in weaning.note.lower()


def test_unknown_ration_lowers_confidence_without_a_filled_value():
    scored = score_cohort(
        reference_cohort(ration_transition_status="unknown"),
        False,
        Assumptions(),
    )
    assert scored.confidence.level == "reduced"
    assert scored.confident_call is True
    ration = next(driver for driver in scored.drivers if driver.key == "ration_transition_status")
    assert ration.value is None
    assert ration.domain == "nutrition"


def test_four_domains_are_present():
    scored = score_cohort(reference_cohort(), True, Assumptions())
    domains = {driver.domain for driver in scored.drivers}
    assert domains == {"animal", "management", "nutrition", "environment"}


def test_seeded_priority_and_incomplete_records():
    cohorts, yards = load_demo("shortage")
    context = build_context(cohorts, yards)
    assert context.ranked_ids[0] == PRIORITY_COHORT_ID
    priority = context.scored[PRIORITY_COHORT_ID]
    incomplete = context.scored[INCOMPLETE_COHORT_ID]
    assert priority.confident_call
    assert priority.above_benchmark
    assert priority.morbidity > context.assumptions.high_risk_benchmark
    assert incomplete.confident_call is False
    assert "travel_distance_mi" in incomplete.confidence.critical_missing
    assert "vaccination_status" in incomplete.confidence.critical_missing
    reduced = context.scored["KSB-4604"]
    assert reduced.confidence.level == "reduced"


def pytest_approx(value: float):
    import pytest

    return pytest.approx(value, abs=1e-6)
