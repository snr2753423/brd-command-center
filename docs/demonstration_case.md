# Demonstration case

One case: Lot 4401 at Panhandle North (TX-A), on the synthetic shortage file, with the default settings. Those are the published Rojas 2022 constants, the score calibrated to Rojas, and worst-case planning for unknown fields.

## Inputs

Lot 4401 is synthetic. Animal: 200 head, steers, 540 lb arrival weight, 4 already clinically ill. Management: 4 sources, 520 miles, known unweaned, known unvaccinated. Nutrition: ration still transitioning, 8 inches of bunk per head. Environment: fourth-quarter arrival. The yard weather-stress flag is no, and it is synthetic, not a live feed.

The 45-day morbidity estimate is 16.7%, and P(morbidity ≥ 15%) is 55%. Those are different numbers. The first is the planning estimate. The second says how likely the lot is to land above the published 15% line, given the calibrated cohort-to-cohort spread. Confidence is confident, because transport and health history are present. The largest contributions are arrival weight, source count, and known unweaned status.

TX-A arrival-week capacity, synthetic: 220 staff hours, pen equal to 250 sq ft per head, and treatment slots equal to the standard-care case load. The other seven cohorts are on the same file so the yard limits can bind. Lot 4388 is the incomplete record. It is not this case. Its travel, weaning, and vaccination are unknown, and the app withholds a confident call. Leaving those fields out would score it at 5.6%, which is the same as assuming a 100-mile haul and a weaned, vaccinated history. The plan instead uses the worst case across the unknown states, 18.6%.

## Named baseline rule

Current practice: veterinary review when arrival weight is under 600 lb and source count is at least 2. Every other cohort stays on standard care. The weight and source cutoffs are the operating rule (assumption). They are not the 15% model benchmark. Lot 4390 shows the difference: the model puts it at 16.8%, but it has one source, so the rule leaves it on standard care.

Lot 4401 is under 600 lb and has four sources, so the baseline action is veterinary review. That action requires a veterinarian. It is not a prescription. The $23.60 drug cost is not inside the $151.18 case cost. Both come from Rojas et al. 2022, Table 3.

Applied to every cohort, the same rule does not fit the shortage file. TX-B would need 101 staff hours and has 65, because Lot 4388 is also light and multi-source. The baseline is therefore the comparison point, not a feasible yard plan.

## Alternatives

Each alternative is scored against that rule for Lot 4401. Deaths use 17.2% BRD deaths per case for cattle under 700 lb, derived from published rates. Efficacy other than metaphylaxis is an assumption. Head count is synthetic. Exposure units are synthetic.

| Action | Role | Cases | BRD deaths | Operating loss | Exposure | Staff hours |
|---|---|---|---|---|---|---|
| Veterinary review | Baseline rule | 20.4 | 3.5 | $7,703 | 216 | 110 |
| Standard care | Alternative | 36.7 | 6.3 | $5,550 | 36.7 | 50 |
| Enhanced surveillance | Alternative | 30.8 | 5.3 | $4,960 | 30.8 | 180 |
| Supportive management | Alternative | 26.9 | 4.6 | $4,867 | 26.9 | 80 |

Supportive management has the lowest loss in the table. It does not fit: the shortage yards are full at 250 sq ft per head, and supportive management needs 1.25 times that pen. Pen is a hard constraint. A manager who frees pen space with the TX-A pen slider will see the solver pick it.

## Recommendation with seeded limits

With TX-A at its seeded 220 staff hours, the operating-loss solve selects enhanced surveillance for Lot 4401 and standard care for the other TX-A lot. Surveillance uses 180 hours, and the yard is at its staff cap. Pen is at cap on every yard. Treatment is at cap on TX-B, KS-A, and KS-B.

Against the baseline, surveillance accepts about 10 more cases and 1.8 more expected deaths for about $2,700 less operating loss and about 185 fewer exposure units. Choosing the morbidity or deaths objective instead selects veterinary review. That trade-off is the manager's call, and veterinary review remains a veterinarian's decision.

## Staff cut and projected consequences

The demo cut sets TX-A staff to 90 hours. That is the standard-care floor for the two TX-A lots. Enhanced surveillance no longer fits. The feasible recommendation for Lot 4401 changes to standard care. One hour under 90 is refused, and the message names TX-A staff as the short limit, because the model will not go below standard-care monitoring or leave clinically ill cattle untreated.

For Lot 4401, cases rise from about 30.8 to 36.7, expected BRD deaths from 5.3 to 6.3, and operating loss from $4,960 to $5,550. Veterinary review is not selected: at the published costs it costs more than standard care, and 110 hours do not fit in a 90-hour yard.

For all eight cohorts, the yard totals move from about 103.5 expected cases, 17.1 BRD deaths, $15,954 operating loss, and 103.5 exposure units to about 109.4 cases, 18.1 deaths, $16,545, and 109.4 exposure units. Health is worse. Operating loss is higher, because the surveillance program was saving more case loss than its $1.50 per head. Antimicrobial exposure rises with the extra therapeutic cases. The cut does not add metaphylaxis. Staff, pen, and treatment on the recommended plan stay inside their capacities. The named baseline rule was infeasible before the cut and remains infeasible after it.
