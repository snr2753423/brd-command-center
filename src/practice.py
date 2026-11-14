"""Named current-practice rule.

Veterinary review only when the cohort is already tagged high-risk by light
arrival weight and multiple sources. Every other cohort stays on standard care.
"""

from __future__ import annotations

from .assumptions import Assumptions
from .schema import ACTION_LABEL, Cohort


def is_rule_high_risk(cohort: Cohort, assumptions: Assumptions | None = None) -> bool:
    assumptions = assumptions or Assumptions()
    light = cohort.arrival_weight_lb < assumptions.light_weight_lb
    multi = cohort.source_count >= assumptions.multiple_source_min
    return light and multi


def current_practice_action(cohort: Cohort, assumptions: Assumptions | None = None) -> str:
    if is_rule_high_risk(cohort, assumptions):
        return "vet_review"
    return "standard_care"


def rule_text(assumptions: Assumptions | None = None) -> str:
    assumptions = assumptions or Assumptions()
    weight = f"{assumptions.light_weight_lb:.0f}"
    sources = assumptions.multiple_source_min
    return (
        f"Current practice: veterinary review for cohorts tagged high-risk by "
        f"arrival weight under {weight} lb and at least {sources} sources. "
        "Every other cohort stays on standard care."
    )


def action_label(action_id: str) -> str:
    return ACTION_LABEL[action_id]
