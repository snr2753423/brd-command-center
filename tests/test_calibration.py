from __future__ import annotations

import pytest

from src.assumptions import Assumptions
from src.calibration import AUC_TARGET, ROJAS, committed_fit


@pytest.fixture(scope="module")
def stored():
    return committed_fit(Assumptions())


def test_stored_values_hit_the_fitted_rojas_targets(stored):
    assert stored.mean_morbidity == pytest.approx(ROJAS["mean_morbidity"], abs=0.002)
    assert stored.high_risk_share == pytest.approx(ROJAS["high_risk_share"], abs=0.005)
    assert stored.auc == pytest.approx(AUC_TARGET, abs=0.01)
    assert ROJAS["auc_low"] <= stored.auc <= ROJAS["auc_high"]


def test_unfitted_checks_land_near_rojas(stored):
    # Not fitted. Within a few points of the published group means.
    assert stored.high_risk_mean == pytest.approx(ROJAS["high_risk_mean"], abs=0.03)
    assert stored.low_risk_mean == pytest.approx(ROJAS["low_risk_mean"], abs=0.005)


def test_population_matches_rojas_size(stored):
    assert len(stored.realized) == ROJAS["cohorts"]
