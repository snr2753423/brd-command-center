"""Write the demo CSVs next to this script and the data dictionary.

Run from anywhere:

    python data/generate_demo_data.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dataclasses import replace  # noqa: E402

from src.assumptions import Assumptions  # noqa: E402
from src.capacities import build_yards  # noqa: E402
from src.data_loader import cohort_row, load_demo  # noqa: E402
from src.optimizer import evaluate_assignment, solve  # noqa: E402
from src.pipeline import build_context  # noqa: E402
from src.practice import current_practice_action  # noqa: E402
from src.schema import (  # noqa: E402
    COHORT_COLUMNS,
    DEMO_YARD_ID,
    PRIORITY_COHORT_ID,
    YARD_COLUMNS,
    Cohort,
    Yard,
)

HERE = Path(__file__).resolve().parent


def demo_cohorts() -> list[Cohort]:
    return [
        Cohort(
            "TXA-4401",
            "TX-A",
            "Lot 4401",
            200,
            "steer",
            540,
            4,
            520,
            "known_unweaned",
            "known_unvaccinated",
            "transitioning",
            8,
            "Q4",
            4,
        ),
        Cohort(
            "TXA-4402",
            "TX-A",
            "Lot 4402",
            160,
            "steer",
            760,
            1,
            120,
            "known_weaned",
            "known_vaccinated",
            "adapted",
            12,
            "Q2",
            1,
        ),
        Cohort(
            "TXB-4388",
            "TX-B",
            "Lot 4388",
            120,
            "mixed",
            550,
            3,
            None,
            "unknown",
            "unknown",
            "unknown",
            10,
            "Q4",
            2,
        ),
        Cohort(
            "TXB-4390",
            "TX-B",
            "Lot 4390",
            140,
            "heifer",
            480,
            1,
            800,
            "known_unweaned",
            "known_unvaccinated",
            "transitioning",
            8,
            "Q4",
            2,
        ),
        Cohort(
            "KSA-4502",
            "KS-A",
            "Lot 4502",
            150,
            "steer",
            700,
            2,
            300,
            "known_weaned",
            "known_vaccinated",
            "adapted",
            11,
            "Q1",
            1,
        ),
        Cohort(
            "KSA-4508",
            "KS-A",
            "Lot 4508",
            100,
            "steer",
            800,
            1,
            90,
            "known_weaned",
            "known_vaccinated",
            "adapted",
            13,
            "Q2",
            0,
        ),
        Cohort(
            "KSB-4601",
            "KS-B",
            "Lot 4601",
            220,
            "mixed",
            690,
            2,
            250,
            "known_weaned",
            "known_vaccinated",
            "transitioning",
            10,
            "Q3",
            3,
        ),
        Cohort(
            "KSB-4604",
            "KS-B",
            "Lot 4604",
            90,
            "heifer",
            610,
            1,
            180,
            "known_weaned",
            "known_vaccinated",
            "unknown",
            12,
            "Q4",
            1,
        ),
    ]


def _write_csv(path: Path, fieldnames: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _yard_row(yard: Yard) -> dict[str, str]:
    return {
        "yard_id": yard.yard_id,
        "yard_name": yard.yard_name,
        "region": yard.region,
        "weather_stress_flag": "true" if yard.weather_stress_flag else "false",
        "pen_capacity_sqft": f"{yard.pen_capacity_sqft:.4f}",
        "staff_hours": f"{yard.staff_hours:.4f}",
        "demo_staff_hours": f"{yard.demo_staff_hours:.4f}",
        "treatment_slots": f"{yard.treatment_slots:.4f}",
        "bottleneck": yard.bottleneck,
    }


def _bad_rows() -> list[dict[str, str]]:
    base = {column: "" for column in COHORT_COLUMNS}

    def row(**kwargs: str) -> dict[str, str]:
        item = dict(base)
        item.update(kwargs)
        return item

    good = row(
        cohort_id="UPLOAD-1",
        yard_id="TX-A",
        cohort_name="Upload good",
        head_count="100",
        sex="steer",
        arrival_weight_lb="700",
        source_count="1",
        travel_distance_mi="100",
        weaning_status="known_weaned",
        vaccination_status="known_vaccinated",
        ration_transition_status="adapted",
        bunk_space_in_per_head="12",
        arrival_quarter="Q2",
        clinically_ill_head="0",
    )
    duplicate = row(**{**good, "cohort_id": "UPLOAD-DUP", "cohort_name": "Dup A"})
    duplicate_again = row(**{**good, "cohort_id": "UPLOAD-DUP", "cohort_name": "Dup B"})
    return [
        good,
        row(**{**good, "cohort_id": "BAD-HEAD", "cohort_name": "Bad head", "head_count": "-5"}),
        row(**{**good, "cohort_id": "BAD-SEX", "cohort_name": "Bad sex", "sex": "bull"}),
        row(**{**good, "cohort_id": "BAD-WT", "cohort_name": "Bad weight", "arrival_weight_lb": ""}),
        row(**{**good, "cohort_id": "BAD-YARD", "cohort_name": "Bad yard", "yard_id": "ZZ-9"}),
        row(**{**good, "cohort_id": "BAD-Q", "cohort_name": "Bad quarter", "arrival_quarter": "Q5"}),
        row(**{**good, "cohort_id": "BAD-MI", "cohort_name": "Bad miles", "travel_distance_mi": "-20"}),
        row(
            **{
                **good,
                "cohort_id": "BAD-ILL",
                "cohort_name": "Bad ill",
                "head_count": "10",
                "clinically_ill_head": "50",
            }
        ),
        row(**{**good, "cohort_id": "BAD-BUNK", "cohort_name": "Bad bunk", "bunk_space_in_per_head": "-2"}),
        duplicate,
        duplicate_again,
    ]


def _missing_column_rows() -> tuple[list[str], list[dict[str, str]]]:
    fields = [column for column in COHORT_COLUMNS if column != "head_count"]
    row = {column: "" for column in fields}
    row.update(
        {
            "cohort_id": "NO-HEAD",
            "yard_id": "TX-A",
            "cohort_name": "Missing head column",
            "sex": "steer",
            "arrival_weight_lb": "700",
            "source_count": "1",
            "arrival_quarter": "Q2",
            "clinically_ill_head": "0",
        }
    )
    return fields, [row]


def _valid_sample_rows() -> list[dict[str, str]]:
    """Synthetic, de-identified yard-style cohorts that must all pass validation.

    IDs are distinct from the seeded demo lots so \"Add to plan\" does not collide.
    """

    def row(**fields: str) -> dict[str, str]:
        return {column: fields.get(column, "") for column in COHORT_COLUMNS}

    return [
        row(
            cohort_id="SAMPLE-TXA-1",
            yard_id="TX-A",
            cohort_name="Sample Panhandle North A",
            head_count="90",
            sex="steer",
            arrival_weight_lb="680",
            source_count="2",
            travel_distance_mi="210",
            weaning_status="known_weaned",
            vaccination_status="known_vaccinated",
            ration_transition_status="adapted",
            bunk_space_in_per_head="12",
            arrival_quarter="Q3",
            clinically_ill_head="1",
        ),
        row(
            cohort_id="SAMPLE-TXB-1",
            yard_id="TX-B",
            cohort_name="Sample Panhandle South A",
            head_count="75",
            sex="heifer",
            arrival_weight_lb="520",
            source_count="3",
            travel_distance_mi="640",
            weaning_status="known_unweaned",
            vaccination_status="known_unvaccinated",
            ration_transition_status="transitioning",
            bunk_space_in_per_head="9",
            arrival_quarter="Q4",
            clinically_ill_head="2",
        ),
        row(
            cohort_id="SAMPLE-KSA-1",
            yard_id="KS-A",
            cohort_name="Sample High Plains West A",
            head_count="110",
            sex="mixed",
            arrival_weight_lb="710",
            source_count="1",
            travel_distance_mi="",
            weaning_status="unknown",
            vaccination_status="",
            ration_transition_status="adapted",
            bunk_space_in_per_head="",
            arrival_quarter="Q2",
            clinically_ill_head="0",
        ),
        row(
            cohort_id="SAMPLE-KSB-1",
            yard_id="KS-B",
            cohort_name="Sample High Plains East A",
            head_count="95",
            sex="steer",
            arrival_weight_lb="790",
            source_count="1",
            travel_distance_mi="85",
            weaning_status="known_weaned",
            vaccination_status="known_vaccinated",
            ration_transition_status="adapted",
            bunk_space_in_per_head="14",
            arrival_quarter="Q1",
            clinically_ill_head="0",
        ),
    ]


def write_demo(directory: Path | None = None) -> None:
    directory = directory or HERE
    directory.mkdir(parents=True, exist_ok=True)
    assumptions = Assumptions()
    cohorts = demo_cohorts()
    shortage = build_yards(cohorts, assumptions, "shortage")
    normal = build_yards(cohorts, assumptions, "normal")
    _write_csv(directory / "cohorts.csv", COHORT_COLUMNS, [cohort_row(cohort) for cohort in cohorts])
    _write_csv(directory / "yards_shortage.csv", YARD_COLUMNS, [_yard_row(yard) for yard in shortage])
    _write_csv(directory / "yards_normal.csv", YARD_COLUMNS, [_yard_row(yard) for yard in normal])
    _write_csv(directory / "upload_bad_rows.csv", COHORT_COLUMNS, _bad_rows())
    fields, rows = _missing_column_rows()
    _write_csv(directory / "upload_missing_column.csv", tuple(fields), rows)
    _write_csv(directory / "upload_valid_sample.csv", COHORT_COLUMNS, _valid_sample_rows())


def _print_story(directory: Path) -> None:
    assumptions = Assumptions()
    cohorts, yards = load_demo("shortage", directory)
    context = build_context(cohorts, yards, assumptions)
    print("rank cohort morbidity confident practice burden")
    for cohort_id in context.ranked_ids:
        scored = context.scored[cohort_id]
        burden = context.metrics[cohort_id]["standard_care"].expected_cases
        print(
            f"  {cohort_id} {scored.planning_morbidity:.3f} {scored.confidence.level} "
            f"{context.practice[cohort_id]} cases {burden:.1f} "
            f"P(high) {scored.p_high_risk:.3f}"
        )
    full = solve(context.cohorts, context.metrics, context.yards)
    cut_hours = context.yards[DEMO_YARD_ID].demo_staff_hours
    cut = solve(
        context.cohorts,
        context.metrics,
        context.yards,
        staff_hours={DEMO_YARD_ID: cut_hours},
    )
    print(
        f"seeded staff {context.yards[DEMO_YARD_ID].staff_hours:.4f} "
        f"cut {cut_hours:.4f}"
    )
    print("full", full.status, {k: full.assignment[k] for k in context.ranked_ids})
    print("cut ", cut.status, {k: cut.assignment[k] for k in context.ranked_ids} if cut.assignment else cut.message)
    if full.feasible and cut.feasible:
        print(
            f"cases {full.totals.expected_cases:.2f} -> {cut.totals.expected_cases:.2f}  "
            f"loss {full.totals.operating_loss:.0f} -> {cut.totals.operating_loss:.0f}  "
            f"amu {full.totals.amu:.2f} -> {cut.totals.amu:.2f}  "
            f"deaths {full.totals.expected_deaths:.2f} -> {cut.totals.expected_deaths:.2f}"
        )
        for yard_id, use in full.by_yard.items():
            print(
                f"  {yard_id} staff {use.staff_ratio:.3f} pen {use.pen_ratio:.3f} "
                f"tx {use.treatment_ratio:.3f}"
            )
    practice = {
        cohort.cohort_id: current_practice_action(cohort, assumptions) for cohort in context.cohorts
    }
    practice_eval = evaluate_assignment(practice, context.cohorts, context.metrics, context.yards)
    print("practice", practice_eval.status)
    for item in practice_eval.violations:
        print(" ", item)

    stressed = replace(
        assumptions, morbidity_cost_per_case=assumptions.flip_morbidity_cost_per_case
    )
    stressed_context = build_context(cohorts, yards, stressed)
    flipped = solve(stressed_context.cohorts, stressed_context.metrics, stressed_context.yards)
    print(
        "flip",
        flipped.status,
        flipped.assignment.get(PRIORITY_COHORT_ID),
        "morbidity objective",
        solve(
            context.cohorts,
            context.metrics,
            context.yards,
            objective="modeled_morbidity",
        ).assignment.get(PRIORITY_COHORT_ID),
    )
    normal_cohorts, normal_yards = load_demo("normal", directory)
    normal_context = build_context(normal_cohorts, normal_yards, assumptions)
    relaxed = solve(normal_context.cohorts, normal_context.metrics, normal_context.yards)
    print("normal priority", relaxed.status, relaxed.assignment.get(PRIORITY_COHORT_ID))


def main() -> None:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE
    write_demo(out)
    _print_story(out)


if __name__ == "__main__":
    main()
