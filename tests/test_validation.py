from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.data_loader import DATA, load_demo
from src.schema import COHORT_COLUMNS
from src.validation import validate_cohort_frame

YARDS = {"TX-A", "TX-B", "KS-A", "KS-B"}


def _read(name: str) -> pd.DataFrame:
    return pd.read_csv(DATA / name, dtype=str, keep_default_na=False)


def test_bad_rows_are_rejected_and_one_good_row_remains():
    result = validate_cohort_frame(_read("upload_bad_rows.csv"), YARDS)
    assert not result.file_errors
    accepted = {cohort.cohort_id for cohort in result.accepted}
    assert accepted == {"UPLOAD-1"}
    fields = {issue.field for issue in result.issues}
    assert {"head_count", "sex", "arrival_weight_lb", "yard_id", "arrival_quarter"} <= fields
    assert any("duplicated" in issue.message for issue in result.issues)
    assert any(issue.field == "travel_distance_mi" for issue in result.issues)
    assert any(issue.field == "clinically_ill_head" for issue in result.issues)
    assert any(issue.field == "bunk_space_in_per_head" for issue in result.issues)


def test_missing_column_rejects_the_file():
    result = validate_cohort_frame(_read("upload_missing_column.csv"), YARDS)
    assert result.file_errors
    assert result.accepted == ()
    assert "head_count" in result.file_errors[0]


def test_blank_history_is_unknown_not_a_default():
    row = {column: "" for column in COHORT_COLUMNS}
    row.update(
        {
            "cohort_id": "UNK-1",
            "yard_id": "KS-A",
            "cohort_name": "Unknown history",
            "head_count": "80",
            "sex": "steer",
            "arrival_weight_lb": "640",
            "source_count": "2",
            "travel_distance_mi": "",
            "weaning_status": "unknown",
            "vaccination_status": "",
            "ration_transition_status": "adapted",
            "bunk_space_in_per_head": "",
            "arrival_quarter": "Q4",
            "clinically_ill_head": "1",
        }
    )
    result = validate_cohort_frame(pd.DataFrame([row]), YARDS)
    assert result.file_errors == ()
    assert result.issues == ()
    cohort = result.accepted[0]
    assert cohort.travel_distance_mi is None
    assert cohort.weaning_status == "unknown"
    assert cohort.vaccination_status == "unknown"
    assert cohort.bunk_space_in_per_head is None


def test_seeded_files_cover_the_four_domains():
    frame = _read("cohorts.csv")
    for column in (
        "head_count",
        "sex",
        "arrival_weight_lb",
        "source_count",
        "travel_distance_mi",
        "weaning_status",
        "vaccination_status",
        "ration_transition_status",
        "bunk_space_in_per_head",
        "arrival_quarter",
    ):
        assert column in frame.columns
    yards = _read("yards_shortage.csv")
    assert "weather_stress_flag" in yards.columns
    assert set(yards["yard_id"]) == YARDS
    cohorts, loaded = load_demo("shortage")
    assert len(cohorts) == 8
    assert len(loaded) == 4


def test_generator_matches_committed_files(tmp_path: Path):
    from data.generate_demo_data import write_demo

    write_demo(tmp_path)
    for name in (
        "cohorts.csv",
        "yards_shortage.csv",
        "yards_normal.csv",
        "upload_bad_rows.csv",
        "upload_missing_column.csv",
    ):
        assert (tmp_path / name).read_text() == (DATA / name).read_text()
