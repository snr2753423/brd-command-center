"""Load the committed demo CSVs."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .schema import COHORT_COLUMNS, YARD_COLUMNS, Cohort, Yard
from .validation import validate_cohort_frame

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

_TRUE = {"1", "true", "yes", "y"}
_FALSE = {"0", "false", "no", "n"}


def load_demo(scenario: str = "shortage", root: Path | None = None) -> tuple[list[Cohort], list[Yard]]:
    if scenario not in {"shortage", "normal"}:
        raise KeyError(scenario)
    base = root or DATA
    yard_name = "yards_shortage.csv" if scenario == "shortage" else "yards_normal.csv"
    yards = load_yards(base / yard_name)
    cohorts = load_cohorts(base / "cohorts.csv", {yard.yard_id for yard in yards})
    return cohorts, yards


def load_yards(path: Path) -> list[Yard]:
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    columns = [str(column).strip() for column in frame.columns]
    missing = [column for column in YARD_COLUMNS if column not in columns]
    if missing:
        raise ValueError(f"{path.name} is missing {', '.join(missing)}")
    frame.columns = columns
    yards: list[Yard] = []
    for record in frame.to_dict(orient="records"):
        flag = str(record["weather_stress_flag"]).strip().lower()
        if flag in _TRUE:
            weather = True
        elif flag in _FALSE:
            weather = False
        else:
            raise ValueError(f"Bad weather_stress_flag on {record['yard_id']}")
        yards.append(
            Yard(
                yard_id=str(record["yard_id"]).strip(),
                yard_name=str(record["yard_name"]).strip(),
                region=str(record["region"]).strip(),
                weather_stress_flag=weather,
                pen_capacity_sqft=float(record["pen_capacity_sqft"]),
                staff_hours=float(record["staff_hours"]),
                demo_staff_hours=float(record["demo_staff_hours"]),
                treatment_slots=float(record["treatment_slots"]),
                bottleneck=str(record["bottleneck"]).strip(),
            )
        )
    return yards


def load_cohorts(path: Path, yard_ids: set[str]) -> list[Cohort]:
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    # Keep file order as row numbers: reset so row 1 is the first data line.
    frame = frame.reset_index(drop=True)
    result = validate_cohort_frame(frame, yard_ids)
    if result.file_errors or result.issues:
        detail = list(result.file_errors) + [
            f"row {issue.row_number} {issue.field}: {issue.message}" for issue in result.issues
        ]
        raise ValueError(f"{path.name} failed validation: " + "; ".join(detail))
    return list(result.accepted)


def cohort_row(cohort: Cohort) -> dict[str, str]:
    def cell(value: object) -> str:
        if value is None:
            return ""
        return str(value)

    return {column: cell(getattr(cohort, column)) for column in COHORT_COLUMNS}
