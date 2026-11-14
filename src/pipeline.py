"""Join cohorts, yards, scores, and action metrics."""

from __future__ import annotations

from dataclasses import dataclass

from .assumptions import Assumptions
from .economics import Metric, metrics_by_action
from .practice import current_practice_action
from .risk_model import Scored, score_cohort
from .schema import Cohort, Yard


@dataclass(frozen=True)
class Context:
    cohorts: list[Cohort]
    yards: dict[str, Yard]
    assumptions: Assumptions
    scored: dict[str, Scored]
    metrics: dict[str, dict[str, Metric]]
    practice: dict[str, str]
    ranked_ids: list[str]


def build_context(
    cohorts: list[Cohort], yards: list[Yard] | dict[str, Yard], assumptions: Assumptions | None = None
) -> Context:
    assumptions = assumptions or Assumptions()
    yard_map = yards if isinstance(yards, dict) else {yard.yard_id: yard for yard in yards}
    missing = sorted({cohort.yard_id for cohort in cohorts} - set(yard_map))
    if missing:
        raise KeyError(f"Cohorts reference unknown yards: {', '.join(missing)}")

    scored: dict[str, Scored] = {}
    metrics: dict[str, dict[str, Metric]] = {}
    practice: dict[str, str] = {}
    for cohort in cohorts:
        yard = yard_map[cohort.yard_id]
        score = score_cohort(cohort, yard.weather_stress_flag, assumptions)
        scored[cohort.cohort_id] = score
        metrics[cohort.cohort_id] = metrics_by_action(cohort, score, assumptions)
        practice[cohort.cohort_id] = current_practice_action(cohort, assumptions)

    ranked = sorted(
        cohorts,
        key=lambda cohort: (
            -metrics[cohort.cohort_id]["standard_care"].expected_cases,
            cohort.cohort_id,
        ),
    )
    return Context(
        cohorts=list(cohorts),
        yards=yard_map,
        assumptions=assumptions,
        scored=scored,
        metrics=metrics,
        practice=practice,
        ranked_ids=[cohort.cohort_id for cohort in ranked],
    )
