# Data dictionary

The generator `data/generate_demo_data.py` writes the files in this folder. Cohort rows are synthetic. Blank cells and the token `unknown` are unknown. They are not filled with a typical value.

## Cohort file — `cohorts.csv`

| Column | Domain | Required | Unit | Allowed values | Unknown |
|---|---|---|---|---|---|
| cohort_id | identity | yes | — | letters, numbers, `_`, `-` | reject the row |
| yard_id | identity | yes | — | TX-A, TX-B, KS-A, KS-B | reject the row |
| cohort_name | identity | yes | — | non-empty text | reject the row |
| head_count | animal | yes | head | integer ≥ 1 | reject the row; a cohort without a count is not invented |
| sex | animal | yes | — | steer, heifer, mixed, unknown | `unknown` or blank lowers confidence |
| arrival_weight_lb | animal | yes | pounds | 350–1200 | reject the row |
| source_count | management | yes | count | integer ≥ 1 | reject the row; the current-practice rule needs it |
| travel_distance_mi | management | no | miles | 0–2500, or blank | blank or `unknown` withholds a confident call |
| weaning_status | management | no | — | known_weaned, known_unweaned, unknown | `unknown` or blank withholds a confident call |
| vaccination_status | management | no | — | known_vaccinated, known_unvaccinated, unknown | `unknown` or blank withholds a confident call |
| ration_transition_status | nutrition | no | — | adapted, transitioning, unknown | `unknown` or blank lowers confidence |
| bunk_space_in_per_head | nutrition | no | inches | 0–36, or blank | blank or `unknown` lowers confidence |
| arrival_quarter | environment | no | quarter | Q1, Q2, Q3, Q4, unknown | `unknown` or blank lowers confidence |
| clinically_ill_head | welfare | yes | head | integer ≥ 0 and ≤ head_count | reject the row |

`clinically_ill_head` is not a fifth risk domain. It is the welfare floor: those cattle stay in the case count, and treatment capacity must cover them.

## Yard files — `yards_shortage.csv`, `yards_normal.csv`

| Column | Meaning | Tag |
|---|---|---|
| yard_id | TX-A, TX-B, KS-A, KS-B | synthetic |
| yard_name | Panhandle North, Panhandle South, High Plains West, High Plains East | synthetic |
| region | Texas Panhandle or western Kansas | synthetic |
| weather_stress_flag | yard-level yes/no. Not a live weather feed | synthetic |
| pen_capacity_sqft | hard pen limit for the cohorts on yard | synthetic |
| staff_hours | hard arrival-week staff limit | synthetic |
| demo_staff_hours | TX-A value used by the staff-cut button. Equals the standard-care floor | synthetic |
| treatment_slots | hard treatment limit, in expected cases | synthetic |
| bottleneck | which limit the story points at. Every yard still has all three hard limits | synthetic |

Shortage capacities are derived by `src/capacities.py` from the same action metrics the optimizer uses. Pen equals head count times 250 sq ft. Staff equals standard-care hours, except TX-A, which has exactly the extra hours for enhanced surveillance on Lot 4401. Treatment equals the standard-care case load. The normal file relaxes those limits.

## Other files this generator writes

| File | Role |
|---|---|
| `upload_valid_sample.csv` | four synthetic, de-identified cohorts that must all pass validation (dry-run until a real yard CSV exists) |
| `upload_bad_rows.csv` | one valid row and rows the upload check must reject |
| `upload_missing_column.csv` | file-level reject: `head_count` is absent |
| `calibration_summary.csv` | Rojas et al. 2022 targets beside the calibrated synthetic population, from `calibrate_to_rojas.py` |
| `calibration_population.csv` | the 1,733 synthetic calibration cohorts with predicted and simulated 45-day morbidity |

## Rules that read these fields

- Current practice: veterinary review if arrival weight is under 600 lb and source count is at least 2. Otherwise standard care. Weight of exactly 600 lb is not light.
- Confident call: withheld if travel, weaning, or vaccination is unknown. Reduced if another field is unknown. Confident if none are.
- Planning morbidity: a cohort with every field known is planned on its own estimate. Leaving an unknown field out of the score would equal giving it the reference value, so a cohort with unknowns is planned on the worst case across its unknown states by default (the manager can switch to the midpoint or the reference profile). The range is not written back onto the row.
- Deaths: expected cases times BRD deaths per case for the weight class (under 700 lb or not), derived from published rates. See the evidence registry.

## Evidence tags

Published (Rojas et al. 2022): the 15% high-risk benchmark, the $151.18 morbid-animal cost, the $23.60 metaphylaxis cost, and 50% metaphylaxis efficacy. Assumption: risk coefficients, the other efficacies, and program costs. Synthetic: these rows, capacities, and weather-stress flags.
