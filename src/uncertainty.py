"""Confidence and intervals. Missing fields stay unknown."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .schema import CRITICAL_FIELDS


def logit(probability: float) -> float:
    p = min(max(probability, 1e-9), 1 - 1e-9)
    return math.log(p / (1 - p))


def expit(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)
    z = math.exp(value)
    return z / (1.0 + z)


def normal_cdf(z: float) -> float:
    scaled = float(np.asarray(z, dtype=float)) / math.sqrt(2.0)
    return float(np.clip(0.5 * (1.0 + math.erf(scaled)), 0.0, 1.0))


def p_exceeds(point_logit: float, sigma: float, benchmark: float) -> float:
    """P(true morbidity >= benchmark) if the logit is normal around the point."""
    if sigma <= 0:
        return 1.0 if expit(point_logit) >= benchmark else 0.0
    z = (point_logit - logit(benchmark)) / sigma
    return normal_cdf(z)


def probability_interval(point_logit: float, sigma: float, z_width: float = 1.64) -> tuple[float, float]:
    low = expit(point_logit - z_width * sigma)
    high = expit(point_logit + z_width * sigma)
    return low, high


@dataclass(frozen=True)
class Confidence:
    level: str  # confident | reduced | withheld
    confident_call: bool
    missing_fields: tuple[str, ...]
    critical_missing: tuple[str, ...]


def assess_confidence(missing_fields: tuple[str, ...]) -> Confidence:
    missing = tuple(missing_fields)
    critical = tuple(field for field in missing if field in CRITICAL_FIELDS)
    if critical:
        return Confidence("withheld", False, missing, critical)
    if missing:
        return Confidence("reduced", True, missing, ())
    return Confidence("confident", True, (), ())
