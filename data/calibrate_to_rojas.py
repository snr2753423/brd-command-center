"""Refit the risk score to Rojas et al. 2022 summary statistics and write the evidence files.

Run from anywhere (about 30 seconds):

    python data/calibrate_to_rojas.py

Writes, next to this script:
- calibration_summary.csv: Rojas targets beside the synthetic population, and each value's role.
- calibration_population.csv: the 1,733 synthetic cohorts with predicted and simulated morbidity.

It prints the fitted intercept, spread, and coefficient scale, and whether they match the
values stored in src/assumptions.py. Copy them there if they do not.
"""

from __future__ import annotations

import csv
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.assumptions import Assumptions  # noqa: E402
from src.calibration import FIELD_MIX, evaluate, fit, summary_rows, synthetic_population  # noqa: E402

HERE = Path(__file__).resolve().parent


def main() -> None:
    assumptions = Assumptions()
    population = synthetic_population(assumptions)
    fitted = fit(population)
    print(f"reference_morbidity = {fitted.reference_morbidity:.5f}")
    print(f"sigma_base          = {fitted.spread:.4f}")
    print(f"risk_scale          = {fitted.scale:.4f}")

    stored = evaluate(population, assumptions.reference_morbidity, assumptions.sigma_base, assumptions.risk_scale)
    close = (
        abs(stored.reference_morbidity - fitted.reference_morbidity) < 5e-4
        and abs(stored.spread - fitted.spread) < 0.02
        and abs(assumptions.risk_scale - fitted.scale) < 0.02
    )
    print("src/assumptions.py matches the fit." if close else "Update src/assumptions.py with the values above.")

    rows = summary_rows(stored)
    with (HERE / "calibration_summary.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    for row in rows:
        print(f"  {row['Statistic']}: Rojas {row['Rojas et al. 2022']}, synthetic {row['Synthetic population']}")

    columns = list(asdict(population.cohorts[0])) + ["weather_stress_flag", "predicted_morbidity", "simulated_morbidity"]
    with (HERE / "calibration_population.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for index, cohort in enumerate(population.cohorts):
            record = asdict(cohort)
            record["weather_stress_flag"] = "true" if population.weather[index] else "false"
            record["predicted_morbidity"] = f"{stored.predicted[index]:.5f}"
            record["simulated_morbidity"] = f"{stored.realized[index]:.5f}"
            writer.writerow(record)
    print("Field mix (assumption):")
    for key, value in FIELD_MIX.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
