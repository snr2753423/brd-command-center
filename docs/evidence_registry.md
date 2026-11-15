# Evidence registry

Every number on the storyboard is tagged published, derived, synthetic, or assumption. Full citations are in `docs/technical_brief.md` under References. Nothing here is a validated accuracy claim. The score is calibrated to Rojas et al. 2022 summary statistics, and that is not a measured accuracy.

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
| Risk coefficients | see `src/assumptions.py` | Assumption | Signs follow published risk-factor direction: lighter arrival weight, more sources, longer haul, unweaned, unvaccinated, ration transition, tighter bunk, fall and winter quarters, weather stress. Relative sizes are assumptions, not published coefficients. One calibrated multiplier (2.08) scales all of them so the score separates high- from low-risk cohorts at AUC 0.735, the midpoint of Rojas's 0.682–0.789. |
| Reference profile | 750 lb, steer, 1 source, 100 miles, known weaned, known vaccinated, adapted ration, 12 in bunk, Q2, no weather stress; 1.09% morbidity | Assumption profile; derived rate | The intercept, calibrated so a 1,733-cohort synthetic population averages Rojas's 6.30%. Leaving an unknown field out of the score equals giving it this profile's value, so cohorts with unknowns are planned on the worst case of their unknown-state range instead. |
| Unexplained spread | logit SD 1.12 | Derived | Calibrated so 10.85% of the synthetic population lands at or above 15%, as in Rojas. Drives P(morbidity ≥ 15%) and the 90% band. |
| Calibration checks | high-risk mean 25.3% (Rojas 27.1%); low-risk mean 3.99% (Rojas 3.77%) | Derived | Not fitted. `data/calibration_summary.csv`, `data/calibrate_to_rojas.py`. |
| Calibration population field mix | see `src/calibration.py` `FIELD_MIX` | Assumption | Rojas does not publish field distributions. |
| Cost stress value | $450 per case | Assumption | Not a published cost. Above the roughly $413 break-even at which veterinary review overtakes surveillance for Lot 4401. |
| Unknown-state bounds | 50 and 800 miles; 6 and 18 inches of bunk | Assumption | Shown as a range when a field is unknown. Not written back onto the row. |
| All-cause death rate | 2.3% placed under 700 lb; 1.2% at 700 lb or more | Published | USDA APHIS NAHMS, *Antimicrobial Use and Stewardship on U.S. Feedlots, 2017* (2019), table A.6, cattle placed in 2016. |
| BRD share of feedlot deaths | 50–80%; midpoint 65% used | Published range, midpoint assumption | Weber et al. 2024 poster, citing Edwards 1996 and Kelly and Janzen 1986. |
| BRD cases in the first 45 days | 65–80%; midpoint 72.5% used | Published range, midpoint assumption | Adekunle and Kaniyamattam 2026. |
| Mean 45-day BRD morbidity | 6.3% | Published | Rojas et al. 2022, 1,733 cohorts. |
| BRD deaths per case | 17.2% under 700 lb; 9.0% at 700 lb or more | Derived | Death rate × BRD share × first-45-day share ÷ mean 45-day morbidity. Assumes deaths follow cases, so preventing a case prevents its share of deaths. Reported, not priced, because $151.18 already covers a sick animal's lost value. |
| Head counts, yards, capacities, weather-stress flags | the demo CSVs | Synthetic | Four yards. No live weather API. |
| Antimicrobial units | 1 per expected case, plus 1 per metaphylaxis head | Synthetic | Exposure units, not dollars. |
| Staff rates | 0.25 / 0.40 / 0.55 / 0.90 h per head | Assumption | Standard care, supportive management, veterinary review, enhanced surveillance. Standard care is the welfare floor. |
| Pen | 250 sq ft per head, 1.25× if supportive | Assumption | Shortage yards are full at 1.0×, so supportive management does not fit. |

## What is refused

- Training on synthetic labels and reporting accuracy.
- Calling the Rojas benchmark our measured performance.
- Filling an unknown haul, weaning, or vaccination with a normal value. The plan uses the worst case of the unknown-state range by default.
- Auto-prescribing. Veterinary review is a flag for a veterinarian.
