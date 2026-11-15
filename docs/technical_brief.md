# Technical brief

## Decision problem

A feedlot manager has to place each arrival cohort on one action for the first 45 days, while staff hours, pen space, and treatment throughput are already tight. The user is that manager, across four synthetic yards in the Texas Panhandle and western Kansas. The decision unit is the arrival cohort, as in Rojas et al. 2022, because arrival decisions are made for groups. The tool compares four actions: standard care, enhanced surveillance, supportive management, and veterinary review. It does not prescribe. Veterinary review flags a cohort for a veterinarian to consider metaphylaxis.

The arrival record covers four domains. Animal: head count, sex, arrival weight, and head already clinically ill. Management: source count, travel distance, weaning, and vaccination, each known or unknown. Nutrition: ration-transition status and bunk space per head. Environment: arrival quarter and a yard-level weather-stress flag. The flag is a stored field. There is no weather API.

## Data and provenance

Every figure carries one of four tags.

- **Published.** From Rojas et al. 2022: the 15% high-risk cutoff for 45-day BRD morbidity, the mean morbidity (6.30%), the high-risk share (10.85%), and the AUC range (0.682–0.789) of its models. From its Table 3: $151.18 cost of a morbid animal, $23.60 metaphylaxis cost per animal, and 50% metaphylaxis efficacy. From USDA (2019): death rates of 2.3% for cattle placed under 700 lb and 1.2% for heavier cattle.
- **Derived.** BRD deaths per case, and the calibrated intercept, spread, and coefficient scale of the risk score.
- **Synthetic.** The eight demo cohorts, four yards, capacities, and weather-stress flags (`data/generate_demo_data.py`). The 1,733-cohort calibration population (`data/calibrate_to_rojas.py`).
- **Assumption.** Relative coefficient sizes, the non-metaphylaxis effect sizes, program costs, staff and pen rates, exposure units, and the calibration population's field mix.

No dataset was provided, and Rojas cattle-level records are not public. All rows are synthetic and shareable. Unknown cells stay unknown. A missing head count or arrival weight rejects the row, because those fields define the cohort. A missing haul, weaning, or vaccination status withholds a confident call.

## Evidence and calibration

Published risk-factor directions decide which fields enter the score (Adekunle et al. 2026; Adekunle and Kaniyamattam 2026; Rojas et al. 2022; USDA 2019): lighter weight, more sources, a longer haul, unweaned or unvaccinated cattle, a ration still in transition, tight bunk space, colder quarters, and weather stress all raise risk. The score is a logistic model of these fields around a low-risk reference profile (750 lb steers, one source, 100 miles, weaned, vaccinated, adapted ration, 12 in bunk, Q2).

The relative weights are assumptions. Their overall level was calibrated to Rojas. `src/calibration.py` builds 1,733 fully recorded synthetic cohorts (mean size 109) with an assumed field mix. It simulates each cohort's 45-day morbidity head by head, then fits three values to three published targets:

- **Intercept**, matched to the 6.30% mean. Fitted value: a 1.09% reference profile.
- **Unexplained spread**, matched to the 10.85% high-risk share. Fitted value: logit SD 1.12.
- **Coefficient scale**, matched so the score separates high- from low-risk cohorts at AUC 0.735, the midpoint of Rojas's range. Fitted value: 2.08.

The two group means are not fitted, so they serve as the check. High-risk cohorts average 25.3% (Rojas 27.1%) and low-risk cohorts 3.99% (Rojas 3.77%). This is calibration to published summaries, not validation. Matching Rojas's AUC is an assumption about how informative arrival fields are, not an accuracy measured here. The unexplained spread feeds P(morbidity ≥ 15%), so each cohort shows both a planning estimate and the probability it lands above the line.

## Missing information

Leaving an unknown field out of a logistic sum is the same as giving it the reference value. The tool therefore does not plan on that figure. A cohort with unknowns is planned on the worst case across its unknown states (haul 50 or 800 miles; weaned or not; vaccinated or not). A sidebar control switches to the midpoint, or to the reference profile, which is labeled as filling in unknowns. Lot 4388 would score 5.6% with its unknowns left out. It is planned at 18.6%, and the app refuses a confident call.

## Consequences and assumptions

- **Expected cases** are the head already ill, plus the remaining head times planning morbidity times one minus efficacy.
- **Operating loss** is $151.18 per expected case plus the action's own program cost. Metaphylaxis ($23.60 per at-risk head) applies only on veterinary review. Surveillance costs $1.50 per head and supportive management $4.00 per head; their efficacies (18% and 30%) are assumptions.
- **BRD deaths** are cases times deaths per case. Deaths per case are 17.2% for cattle under 700 lb and 9.0% for heavier cattle. They are derived from the USDA death rates, BRD's 50–80% share of feedlot deaths (Weber et al. 2024), the 65–80% of cases that occur in the first 45 days (Adekunle and Kaniyamattam 2026), and the 6.3% mean morbidity. Deaths are reported, not priced, because $151.18 already covers a sick animal's lost value.
- **Antimicrobial exposure** is a synthetic unit: one per case plus one per metaphylaxis head.

Staff hours (0.25, 0.40, 0.55, and 0.90 h per head) and pen (250 sq ft per head; 1.25× for supportive management) are hard per-yard limits in an integer program (PuLP/CBC). Treatment throughput is a third limit. Standard-care monitoring and treatment of already-ill cattle are welfare floors the solver cannot cut. The objective is operating loss, modeled morbidity, antimicrobial exposure, or expected deaths. Current practice is a named rule: veterinary review when a cohort is under 600 lb and from at least two sources, and standard care otherwise.

## Dashboard

The Streamlit app runs locally with no paid service and has five screens.

- **Overview.** Ranks cohorts and shows each yard's limits. Managers can upload a CSV; it is validated and can be added to the plan or replace the seeded cohorts.
- **Cohort.** Shows drivers by domain, the planning estimate, P(≥ 15%), the 90% band, the unknown-state range, and a refusal when history is missing.
- **Compare.** Sets every action against the current-practice rule on cases, deaths, loss, exposure, and resources.
- **Optimizer.** Re-solves live as any of twelve yard-limit sliders, the objective, the case cost, or the unknown-field basis changes. It reports which cohorts changed action.
- **Export.** Writes a text decision summary that says which limits the manager set and flags every veterinary-review cohort.

## Evaluation

`pytest` reports 40 passed. The tests check the risk math, worst-case planning, cost accounting (no dollar counted twice), deaths following cases, all three hard limits and both welfare floors, the shortage diagnosis, the staff cut, the cost flip, uploads entering the plan, and that the stored calibration still hits the Rojas targets. These tests check that the arithmetic and the solver do what they claim. They do not test predictive accuracy on real cattle.

## Trade-offs (demonstration case)

Lot 4401 (200 head, 540 lb, four sources, 520 miles, unweaned, unvaccinated) plans at 16.7%, with P(≥ 15%) of 55%. Current practice sends it to veterinary review: 20.4 cases, 3.5 deaths, $7,703, and 216 exposure units. The solver picks enhanced surveillance: 30.8 cases, 5.3 deaths, $4,960, and 31 exposure units. That choice trades about ten more cases and two more deaths for $2,700 less operating loss and 85% less antimicrobial exposure. Minimizing morbidity or deaths instead selects veterinary review. Supportive management would lose less money still, but the shortage pens are full.

Applied to the whole file, the current-practice rule does not fit: TX-B would need 101 staff hours and has 65. Cutting TX-A staff from 220 to 90 hours moves Lot 4401 to standard care. Yard totals then move from 103.5 to 109.4 cases, from 17.1 to 18.1 BRD deaths, and from $15,954 to $16,545. Below 90 hours the plan is refused, and the error names the yard and limit that is short. At a $450 case cost (a stress value, not published), operating loss also selects veterinary review.

## Limitations

The cohorts, capacities, and calibration population are synthetic. They are not records from any yard and not a validation set. The coefficient pattern, the non-metaphylaxis effects, and the calibration population's field mix are assumptions. The deaths per case are derived and likely conservative for light, high-risk cattle. The tool works at cohort level, has no individual-animal or day-by-day reassessment, and uses no live weather. It never withholds treatment from cattle already ill, and it never turns veterinary review into a prescription.

## References

This section is outside the three-page body.

- Rojas, H.A.; White, B.J.; Amrine, D.E.; Larson, R.L. Predicting Bovine Respiratory Disease Risk in Feedlot Cattle in the First 45 Days Post Arrival. *Pathogens* 2022, 11, 442. https://doi.org/10.3390/pathogens11040442. The 15% cutoff, the summary statistics used for calibration, and the Table 3 constants. Cattle-level records are not used.
- Avra, T.D.; Abell, K.M.; Shane, D.D.; Theurer, M.E.; Larson, R.L.; White, B.J. A Retrospective Analysis of Risk Factors Associated with Bovine Respiratory Disease Treatment Failure in Feedlot Cattle. *J. Anim. Sci.* 2017, 95, 1521–1527. Cited by Rojas for 50% metaphylaxis efficacy.
- Adekunle, A.; Gaines, A.; Estefano, N.; Lenin, D.; Hole, P.; Khandelwal, R.; Cooke, R.; Kaniyamattam, K. Mapping Variability in Bovine Respiratory Disease Risk Factors in Beef Production Systems: A Scoping Review. *Animals* 2026, 16, 1726. https://doi.org/10.3390/ani16111726. Risk-factor directions.
- Adekunle, A.; Kaniyamattam, K. Bovine Respiratory Disease: Epidemiological Drivers, Transmission Dynamics, and Economic Implications in Beef Production Systems. *Agriculture* 2026, 16, 311. https://doi.org/10.3390/agriculture16030311. Risk-factor directions and the timing of BRD cases.
- Johnson, K.K.; Pendell, D.L. Market Impacts of Reducing the Prevalence of Bovine Respiratory Disease in United States Beef Cattle Feedlots. *Front. Vet. Sci.* 2017, 4, 189. https://doi.org/10.3389/fvets.2017.00189. Context for the $23.60 NAHMS treatment cost.
- Weber, K.M.D.; Schroeder, T.C.; Renter, D.G.; Pendell, D.L.; Tonsor, G.T. Evaluation of Bovine Respiratory Disease Morbidity in the Feedlot and its Effect on Net Return Distributions. AAEA Annual Meeting poster, 2024. BRD share of feedlot deaths.
- USDA APHIS. *Antimicrobial Use and Stewardship on U.S. Feedlots, 2017.* NAHMS, May 2019. Death rates by placement weight; risk factors feedlots use for group treatment.
