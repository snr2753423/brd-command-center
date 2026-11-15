"""Calibrate the risk score's intercept and spread to Rojas et al. 2022 summary statistics.

Rojas et al. 2022 report, for 1,733 commercial feedlot cohorts (188,118 head, mean
cohort size 109): mean 45-day BRD morbidity 6.30%; 10.85% of cohorts at or above the
15% high-risk cutoff; mean morbidity 27.07% in high-risk and 3.77% in low-risk cohorts.

The cattle-level data are not public, so this module builds a synthetic population of
1,733 cohorts with every field known (Rojas excluded cohorts with missing fields). The
field mix is an assumption, listed in `FIELD_MIX`. Each cohort's realized morbidity is
simulated animal by animal from its score plus unexplained cohort-to-cohort variation.

Three parameters are fitted to three targets:
- the reference-profile morbidity (the intercept) to the 6.30% mean,
- the unexplained spread (logit-scale SD) to the 10.85% high-risk share, and
- one multiplier on every driver coefficient so the score separates high- from low-risk
  cohorts about as well as Rojas's published models did (AUC 0.682 to 0.789; the
  midpoint 0.735 is the target). That is an assumption about how informative the
  arrival fields are, not an accuracy this package measured.
The high-risk and low-risk means are not fitted. They are the check.

This is a calibration of a synthetic score to published summary statistics. It is not a
validation, and it says nothing about accuracy on real cohorts.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace

import numpy as np

from .assumptions import Assumptions
from .risk_model import point_drivers
from .schema import Cohort
from .uncertainty import expit, logit

ROJAS = {
    "cohorts": 1733,
    "mean_cohort_size": 109,
    "mean_morbidity": 0.0630,
    "high_risk_share": 0.1085,
    "high_risk_mean": 0.2707,
    "low_risk_mean": 0.0377,
    "auc_low": 0.682,
    "auc_high": 0.789,
}
AUC_TARGET = round((ROJAS["auc_low"] + ROJAS["auc_high"]) / 2.0, 4)

# Assumed field mix for the synthetic population. Not published distributions.
FIELD_MIX = {
    "arrival_weight_lb": "normal(720, 120), clipped 400-1050",
    "sex": "steer 55%, heifer 35%, mixed 10%",
    "source_count": "1 + Poisson(1.0), at most 8",
    "travel_distance_mi": "lognormal, median 300, clipped 20-1500",
    "weaning_status": "known weaned 60%, known unweaned 40%",
    "vaccination_status": "known vaccinated 60%, known unvaccinated 40%",
    "ration_transition_status": "adapted 50%, transitioning 50%",
    "bunk_space_in_per_head": "normal(12, 2.5), clipped 6-20",
    "arrival_quarter": "uniform Q1-Q4",
    "weather_stress_flag": "yes 25%",
    "head_count": "gamma(shape 4, mean 109), at least 20",
}

SEED = 20221


@dataclass(frozen=True)
class Population:
    cohorts: tuple[Cohort, ...]
    weather: np.ndarray  # bool per cohort
    offsets: np.ndarray  # logit offset from the reference profile, per cohort
    sizes: np.ndarray  # head per cohort
    z: np.ndarray  # standard normal per cohort, for unexplained variation
    uniforms: np.ndarray  # one per animal, for realized cases
    starts: np.ndarray  # index of each cohort's first animal in `uniforms`


@dataclass(frozen=True)
class Fit:
    reference_morbidity: float
    spread: float
    scale: float
    auc: float
    mean_morbidity: float
    high_risk_share: float
    high_risk_mean: float
    low_risk_mean: float
    predicted: np.ndarray
    realized: np.ndarray


def synthetic_population(assumptions: Assumptions | None = None, seed: int = SEED) -> Population:
    assumptions = assumptions or Assumptions()
    rng = np.random.default_rng(seed)
    count = ROJAS["cohorts"]
    weights = np.clip(rng.normal(720, 120, count), 400, 1050)
    sexes = rng.choice(["steer", "heifer", "mixed"], size=count, p=[0.55, 0.35, 0.10])
    sources = np.minimum(1 + rng.poisson(1.0, count), 8)
    miles = np.clip(rng.lognormal(math.log(300), 0.7, count), 20, 1500)
    weaned = rng.random(count) < 0.60
    vaccinated = rng.random(count) < 0.60
    transitioning = rng.random(count) < 0.50
    bunk = np.clip(rng.normal(12, 2.5, count), 6, 20)
    quarters = rng.choice(["Q1", "Q2", "Q3", "Q4"], size=count)
    weather = rng.random(count) < 0.25
    sizes = np.maximum(np.rint(rng.gamma(4.0, ROJAS["mean_cohort_size"] / 4.0, count)), 20).astype(int)

    cohorts = []
    offsets = np.empty(count)
    # Unscaled offsets: the scale is applied in `evaluate`.
    assumptions = replace(assumptions, risk_scale=1.0)
    reference = logit(assumptions.reference_morbidity)
    for index in range(count):
        cohort = Cohort(
            cohort_id=f"SYN-{index + 1:04d}",
            yard_id="SYN",
            cohort_name=f"Synthetic {index + 1}",
            head_count=int(sizes[index]),
            sex=str(sexes[index]),
            arrival_weight_lb=float(round(weights[index])),
            source_count=int(sources[index]),
            travel_distance_mi=float(round(miles[index])),
            weaning_status="known_weaned" if weaned[index] else "known_unweaned",
            vaccination_status="known_vaccinated" if vaccinated[index] else "known_unvaccinated",
            ration_transition_status="transitioning" if transitioning[index] else "adapted",
            bunk_space_in_per_head=float(round(bunk[index], 1)),
            arrival_quarter=str(quarters[index]),
            clinically_ill_head=0,
        )
        cohorts.append(cohort)
        _, total = point_drivers(cohort, bool(weather[index]), assumptions)
        offsets[index] = total - reference

    z = rng.standard_normal(count)
    uniforms = rng.random(int(sizes.sum()))
    starts = np.concatenate([[0], np.cumsum(sizes)[:-1]])
    return Population(tuple(cohorts), weather, offsets, sizes, z, uniforms, starts)


def _auc(scores: np.ndarray, positive: np.ndarray) -> float:
    """Mann-Whitney AUC of the predicted score against realized high-risk class."""
    pos, neg = int(positive.sum()), int((~positive).sum())
    if pos == 0 or neg == 0:
        return float("nan")
    order = scores.argsort(kind="mergesort")
    ranks = np.empty(len(scores))
    ranks[order] = np.arange(1, len(scores) + 1)
    return float((ranks[positive].sum() - pos * (pos + 1) / 2.0) / (pos * neg))


def evaluate(
    population: Population,
    reference_morbidity: float,
    spread: float,
    scale: float = 1.0,
    benchmark: float = 0.15,
) -> Fit:
    base = logit(reference_morbidity)
    predicted_logit = base + scale * population.offsets
    predicted = 1.0 / (1.0 + np.exp(-predicted_logit))
    true_rate = 1.0 / (1.0 + np.exp(-(predicted_logit + spread * population.z)))
    per_animal = np.repeat(true_rate, population.sizes)
    cases = np.add.reduceat((population.uniforms < per_animal).astype(float), population.starts)
    realized = cases / population.sizes
    high = realized >= benchmark
    return Fit(
        reference_morbidity=reference_morbidity,
        spread=spread,
        scale=scale,
        auc=_auc(predicted, high),
        mean_morbidity=float(realized.mean()),
        high_risk_share=float(high.mean()),
        high_risk_mean=float(realized[high].mean()) if high.any() else float("nan"),
        low_risk_mean=float(realized[~high].mean()),
        predicted=predicted,
        realized=realized,
    )


def _match_mean(population: Population, spread: float, scale: float, target: float) -> float:
    low, high = logit(0.0005), logit(0.30)
    for _ in range(30):
        middle = (low + high) / 2.0
        if evaluate(population, expit(middle), spread, scale).mean_morbidity < target:
            low = middle
        else:
            high = middle
    return expit((low + high) / 2.0)


def _match_share(population: Population, scale: float) -> Fit:
    """Intercept for the mean and spread for the high-risk share, at a given scale."""
    low, high = 0.0, 2.5
    for _ in range(22):
        middle = (low + high) / 2.0
        reference = _match_mean(population, middle, scale, ROJAS["mean_morbidity"])
        if evaluate(population, reference, middle, scale).high_risk_share < ROJAS["high_risk_share"]:
            low = middle
        else:
            high = middle
    spread = (low + high) / 2.0
    reference = _match_mean(population, spread, scale, ROJAS["mean_morbidity"])
    return evaluate(population, reference, spread, scale)


def fit(population: Population | None = None) -> Fit:
    """Fit intercept, spread, and coefficient scale to the mean, high-risk share, and AUC."""
    population = population or synthetic_population()
    low, high = 0.5, 8.0
    for _ in range(18):
        middle = (low + high) / 2.0
        if _match_share(population, middle).auc < AUC_TARGET:
            low = middle
        else:
            high = middle
    return _match_share(population, (low + high) / 2.0)


def committed_fit(assumptions: Assumptions | None = None) -> Fit:
    """Evaluate the population at the values stored in `Assumptions`."""
    assumptions = assumptions or Assumptions()
    # Offsets do not depend on the intercept, so any reference value builds the same population.
    population = synthetic_population(assumptions)
    return evaluate(population, assumptions.reference_morbidity, assumptions.sigma_base, assumptions.risk_scale)


def summary_rows(result: Fit) -> list[dict[str, str]]:
    def pct(value: float) -> str:
        return f"{value * 100:.2f}%"

    return [
        {"Statistic": "Mean 45-day morbidity", "Rojas et al. 2022": pct(ROJAS["mean_morbidity"]),
         "Synthetic population": pct(result.mean_morbidity), "Role": "fitted (intercept)"},
        {"Statistic": "Cohorts at or above 15%", "Rojas et al. 2022": pct(ROJAS["high_risk_share"]),
         "Synthetic population": pct(result.high_risk_share), "Role": "fitted (spread)"},
        {"Statistic": "Mean morbidity, high-risk cohorts", "Rojas et al. 2022": pct(ROJAS["high_risk_mean"]),
         "Synthetic population": pct(result.high_risk_mean), "Role": "check, not fitted"},
        {"Statistic": "Mean morbidity, low-risk cohorts", "Rojas et al. 2022": pct(ROJAS["low_risk_mean"]),
         "Synthetic population": pct(result.low_risk_mean), "Role": "check, not fitted"},
        {"Statistic": "Score separation (AUC)", "Rojas et al. 2022": f"{ROJAS['auc_low']:.3f}-{ROJAS['auc_high']:.3f}",
         "Synthetic population": f"{result.auc:.3f}", "Role": "fitted (coefficient scale), assumption"},
    ]
