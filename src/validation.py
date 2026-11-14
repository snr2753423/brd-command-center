"""CSV checks. Bad rows are rejected. Missing history is not rewritten into a typical value."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

import pandas as pd

from .schema import (
    COHORT_COLUMNS,
    QUARTER_VALUES,
    RATION_VALUES,
    SEX_VALUES,
    VACCINATION_VALUES,
    WEANING_VALUES,
    Cohort,
)

_ID = re.compile(r"^[A-Za-z0-9_-]+$")
_BLANK = {"", "na", "n/a", "none", "null"}


@dataclass(frozen=True)
class RowIssue:
    row_number: int
    field: str
    message: str


@dataclass(frozen=True)
class ValidationResult:
    file_errors: tuple[str, ...]
    issues: tuple[RowIssue, ...]
    accepted: tuple[Cohort, ...]

    @property
    def ok(self) -> bool:
        return not self.file_errors and not self.issues


def _text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return str(value).strip()


def _is_blank(value: object) -> bool:
    return _text(value).lower() in _BLANK


def validate_cohort_frame(frame: pd.DataFrame, yard_ids: set[str]) -> ValidationResult:
    columns = [str(column).strip() for column in frame.columns]
    missing = [column for column in COHORT_COLUMNS if column not in columns]
    if missing:
        return ValidationResult(
            file_errors=(
                "Missing required column(s): " + ", ".join(missing) + ". The file was rejected.",
            ),
            issues=(),
            accepted=(),
        )

    working = frame.copy()
    working.columns = columns
    issues: list[RowIssue] = []
    parsed: list[tuple[int, Cohort]] = []

    for offset, record in enumerate(working.to_dict(orient="records")):
        row_number = offset + 1
        row_issues: list[RowIssue] = []

        def add(field: str, message: str) -> None:
            row_issues.append(RowIssue(row_number, field, message))

        cohort_id = _text(record["cohort_id"])
        if not cohort_id or not _ID.match(cohort_id):
            add("cohort_id", "cohort_id must be letters, numbers, hyphens, or underscores.")

        name = _text(record["cohort_name"])
        if not name:
            add("cohort_name", "cohort_name is empty.")

        yard_id = _text(record["yard_id"])
        if yard_id not in yard_ids:
            add("yard_id", f"yard_id '{yard_id}' is not one of the four seeded yards.")

        head = _whole(record["head_count"])
        if head is None or head < 1:
            add("head_count", "head_count must be a positive whole number. It is not filled in.")
            head_ok = None
        else:
            head_ok = head

        weight = _number(record["arrival_weight_lb"])
        if weight is None or not 350 <= weight <= 1200:
            add(
                "arrival_weight_lb",
                "arrival_weight_lb must be between 350 and 1200. Missing weight is not filled in.",
            )

        sources = _whole(record["source_count"])
        if sources is None or sources < 1:
            add("source_count", "source_count must be a whole number of at least 1.")

        sex = _enum(record["sex"], SEX_VALUES)
        if sex is None:
            add("sex", "sex must be steer, heifer, mixed, or unknown.")

        travel: float | None
        if _is_blank(record["travel_distance_mi"]) or _text(record["travel_distance_mi"]).lower() == "unknown":
            travel = None
        else:
            travel = _number(record["travel_distance_mi"])
            if travel is None or travel < 0 or travel > 2500:
                add("travel_distance_mi", "travel_distance_mi must be blank (unknown) or between 0 and 2500.")
                travel = None

        weaning = _enum(record["weaning_status"], WEANING_VALUES)
        if weaning is None:
            add("weaning_status", "weaning_status must be known_weaned, known_unweaned, or unknown.")

        vaccination = _enum(record["vaccination_status"], VACCINATION_VALUES)
        if vaccination is None:
            add(
                "vaccination_status",
                "vaccination_status must be known_vaccinated, known_unvaccinated, or unknown.",
            )

        ration = _enum(record["ration_transition_status"], RATION_VALUES)
        if ration is None:
            add("ration_transition_status", "ration_transition_status must be adapted, transitioning, or unknown.")

        bunk: float | None
        if _is_blank(record["bunk_space_in_per_head"]) or _text(record["bunk_space_in_per_head"]).lower() == "unknown":
            bunk = None
        else:
            bunk = _number(record["bunk_space_in_per_head"])
            if bunk is None or bunk < 0 or bunk > 36:
                add("bunk_space_in_per_head", "bunk_space_in_per_head must be blank (unknown) or between 0 and 36.")
                bunk = None

        quarter = _enum(record["arrival_quarter"], QUARTER_VALUES)
        if quarter is None:
            add("arrival_quarter", "arrival_quarter must be Q1, Q2, Q3, Q4, or unknown.")

        ill = _whole(record["clinically_ill_head"])
        if ill is None or ill < 0:
            add("clinically_ill_head", "clinically_ill_head must be a whole number, zero or more.")
        elif head_ok is not None and ill > head_ok:
            add("clinically_ill_head", "clinically_ill_head cannot exceed head_count.")

        issues.extend(row_issues)
        if row_issues:
            continue
        assert head_ok is not None and weight is not None and sources is not None
        assert sex and weaning and vaccination and ration and quarter and ill is not None
        parsed.append(
            (
                row_number,
                Cohort(
                    cohort_id=cohort_id,
                    yard_id=yard_id,
                    cohort_name=name,
                    head_count=head_ok,
                    sex=sex,
                    arrival_weight_lb=weight,
                    source_count=sources,
                    travel_distance_mi=travel,
                    weaning_status=weaning,
                    vaccination_status=vaccination,
                    ration_transition_status=ration,
                    bunk_space_in_per_head=bunk,
                    arrival_quarter=quarter,
                    clinically_ill_head=ill,
                ),
            )
        )

    # A duplicated id rejects every copy. We will not guess which row is the real one.
    counts: dict[str, int] = {}
    for _, cohort in parsed:
        counts[cohort.cohort_id] = counts.get(cohort.cohort_id, 0) + 1
    accepted: list[Cohort] = []
    for row_number, cohort in parsed:
        if counts[cohort.cohort_id] > 1:
            issues.append(
                RowIssue(
                    row_number,
                    "cohort_id",
                    f"cohort_id {cohort.cohort_id} is duplicated. None of the copies were accepted.",
                )
            )
        else:
            accepted.append(cohort)

    # Stable order for messages.
    issues.sort(key=lambda item: (item.row_number, item.field))
    return ValidationResult((), tuple(issues), tuple(accepted))


def _whole(value: object) -> int | None:
    if _is_blank(value) or _text(value).lower() == "unknown":
        return None
    try:
        number = float(_text(value))
    except ValueError:
        return None
    if not math.isfinite(number) or abs(number - round(number)) > 1e-9:
        return None
    return int(round(number))


def _number(value: object) -> float | None:
    if _is_blank(value):
        return None
    try:
        number = float(_text(value))
    except ValueError:
        return None
    if not math.isfinite(number):
        return None
    return number


def _enum(value: object, allowed: tuple[str, ...]) -> str | None:
    if _is_blank(value) or _text(value).lower() == "unknown":
        return "unknown" if "unknown" in allowed else None
    token = _text(value)
    if token in allowed:
        return token
    lowered = token.lower()
    if lowered in allowed:
        return lowered
    upper = token.upper()
    if upper in allowed:
        return upper
    return None
