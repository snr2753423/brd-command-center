# Demonstration case

One case: Lot 4401 at Panhandle North (TX-A), on the synthetic shortage file. The extras expander stays closed. Figures below are from that file at the published Rojas 2022 constants.

## Inputs

Lot 4401 is synthetic. Animal: 200 head, steers, 540 lb arrival weight, 4 already clinically ill. Management: 4 sources, 520 miles, known unweaned, known unvaccinated. Nutrition: ration still transitioning, 8 inches of bunk per head. Environment: fourth-quarter arrival. The yard weather-stress flag is no, and it is synthetic, not a live feed.

The known-fields 45-day morbidity is 25.9% (assumption coefficients). P(morbidity ≥ 15%) is 98.9%. Those are different numbers. The 15% line is the published Rojas benchmark. Confidence is confident, because transport and health history are present. The largest assumption contributions are arrival weight, source count, the haul, known unweaned status, known unvaccinated status, and the fourth quarter.

TX-A arrival-week capacity, synthetic: 220 staff hours, pen equal to 250 sq ft per head, and treatment slots equal to the standard-care case load. The other seven cohorts are on the same file so the yard limits can bind. Lot 4388 is the incomplete record. It is not this case. Its travel, weaning, and vaccination are unknown, and the app withholds a confident call rather than filling them in. Leaving those fields out would score it at 16.4%, which is the same as assuming a 100-mile haul and a weaned, vaccinated history. The plan instead uses the worst case across the unknown states, 27.1%.

## Named baseline rule

Current practice: veterinary review when arrival weight is under 600 lb and source count is at least 2. Every other cohort stays on standard care. The weight and source cutoffs are the operating rule (assumption). They are not the 15% model benchmark.

Lot 4401 is under 600 lb and has four sources, so the baseline action is veterinary review. That action requires a veterinarian. It is not a prescription. For this lot the baseline projects about 29.4 expected cases, about $9,073 operating loss, about 225 synthetic exposure units, and 110 staff hours. The high exposure is metaphylaxis on the at-risk head plus treatment of the remaining cases. The $23.60 drug cost is not inside the $151.18 case cost. Both come from Rojas et al. 2022, Table 3.

Applied to every cohort, the same rule does not fit the shortage file. TX-B would need 101 staff hours and has 65, because Lot 4388 is also light and multi-source. The baseline is therefore the comparison point, not a feasible yard plan.

## Alternatives

Each alternative is scored against that rule for Lot 4401. Deaths use 17.2% BRD deaths per case for cattle under 700 lb, derived from published rates. Efficacy other than metaphylaxis is an assumption. Head count is synthetic. Exposure units are synthetic.

| Action | Role | Cases | BRD deaths | Operating loss | Exposure | Staff hours |
|---|---|---|---|---|---|---|
| Veterinary review | Baseline rule | 29.4 | 5.1 | $9,073 | 225 | 110 |
| Standard care | Alternative | 54.8 | 9.4 | $8,290 | 54.8 | 50 |
| Enhanced surveillance | Alternative | 45.7 | 7.9 | $7,206 | 45.7 | 180 |
| Supportive management | Alternative | 39.6 | 6.8 | $6,784 | 39.6 | 80 |

Supportive management has the lowest assumed loss in the table. It does not fit: the shortage yards are full at 250 sq ft per head, and supportive management needs 1.25 times that pen. Pen is a hard constraint.

## Staff-cut recommendation

With TX-A at its seeded 220 staff hours, the operating-loss solve selects enhanced surveillance for Lot 4401 and standard care for the other TX-A lot. Surveillance uses the 180 hours. The yard is at its staff cap. Pen is at cap on every yard. Treatment is at cap on TX-B, KS-A, and KS-B.

The demo cut sets TX-A staff to 90 hours. That is the standard-care floor for the two TX-A lots. Enhanced surveillance no longer fits. The feasible recommendation for Lot 4401 changes to standard care. One hour under 90 is refused, because the model will not go below standard-care monitoring or leave clinically ill cattle untreated.

## Projected consequences

The consequences come from the same solve that picks the action.

For Lot 4401, enhanced surveillance at 220 hours projects about 45.7 cases, $7,206, and 45.7 exposure units. Standard care at 90 hours projects about 54.8 cases, $8,290, and 54.8 exposure units. The lot loses the surveillance reduction. Cases rise by about 9, and expected BRD deaths by about 1.6. Staff hours on that lot fall from 180 to 50. Veterinary review is not selected: at these assumed costs it is more expensive than standard care, and 110 hours do not fit in a 90-hour yard.

For all eight cohorts, the yard totals move from about 196.0 expected cases, 30.3 BRD deaths, $29,933 operating loss, and 196.0 exposure units to about 205.2 cases, 31.9 deaths, $31,017, and 205.2 exposure units. Health is worse. Operating loss is higher, because the surveillance program was saving more case-loss than its $1.50 per head. Antimicrobial exposure rises with the extra therapeutic cases. The cut does not add metaphylaxis. Staff, pen, and treatment on the recommended plan stay inside their capacities. The named baseline rule remains infeasible under the cut, and it was already infeasible before the cut.
