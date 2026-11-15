# Evidence registry

Every number on the storyboard is one of three tags. Full citations are in `docs/technical_brief.md` under References. Nothing here is a validated accuracy claim, and this app does not report an AUC.

| Item | Value | Tag | How it is used |
|---|---|---|---|
| High-risk benchmark | 15% first-treatment morbidity | Published | Rojas et al. 2022, *Pathogens* 11:442: cohorts at or above 15% BRD morbidity in the first 45 days on feed are high risk. A cohort at or above this line is model-high-risk. This is not P(high-risk), and it is not the current-practice rule. Cattle-level Rojas records are not in this app. |
| Metaphylaxis cost | $23.60 per at-risk head | Published | Rojas et al. 2022, Table 3, "cost of single metaphylactic treatment per animal" (from USDA NAHMS Feedlot 2011). Charged only on veterinary review, only for head that are not already clinically ill. Not added into the case-loss constant. |
| Morbidity cost | $151.18 per expected case | Published | Rojas et al. 2022, Table 3, "cost of morbid animal": lost value of a sick animal versus a healthy one. Treated as case loss. The default objective uses it. The extras control can move it to $400, which is not a published cost. |
| Metaphylaxis efficacy | 50% | Published | Rojas et al. 2022, Table 3, citing Avra et al. 2017. A modeling input in that paper, not a trial estimate. Applied only to cattle that are not already clinically ill, and only if the plan selects veterinary review. Not a claim that a protocol was validated here. |
| Surveillance efficacy | 18% | Assumption | Not the 50% metaphylaxis constant. |
| Surveillance program cost | $1.50 per head | Assumption | Supplies. Staff time is a capacity constraint, not a second labor bill. |
| Supportive efficacy | 30% | Assumption | Blocked on the shortage yards by the pen limit. |
| Supportive program cost | $4.00 per head | Assumption | Ration and support supplies. |
| Risk coefficients | see `src/assumptions.py` | Assumption | Signs follow published risk-factor direction: lighter arrival weight, more sources, longer haul, unweaned, unvaccinated, ration transition, tighter bunk, fall and winter quarters, weather stress. Magnitudes are not published coefficients. The zero point is an 8% reference profile. |
| Reference profile | 750 lb, steer, 1 source, 100 miles, known weaned, known vaccinated, adapted ration, 12 in bunk, Q2, no weather stress | Assumption | The intercept only. Missing fields are not set to this profile. |
| Unknown-state bounds | 50 and 800 miles; 6 and 18 inches of bunk | Assumption | Shown as a range when a field is unknown. Not written back onto the row. |
| Head counts, yards, capacities, weather-stress flags | the demo CSVs | Synthetic | Four yards. No live weather API. |
| Antimicrobial units | 1 per expected case, plus 1 per metaphylaxis head | Synthetic | Exposure units, not dollars. |
| Staff rates | 0.25 / 0.40 / 0.55 / 0.90 h per head | Assumption | Standard care, supportive management, veterinary review, enhanced surveillance. Standard care is the welfare floor. |
| Pen | 250 sq ft per head, 1.25× if supportive | Assumption | Shortage yards are full at 1.0×, so supportive management does not fit. |

## What is refused

- Training on synthetic labels and reporting accuracy.
- Calling the Rojas benchmark our measured performance.
- Filling an unknown haul, weaning, or vaccination with a normal value.
- Auto-prescribing. Veterinary review is a flag for a veterinarian.
