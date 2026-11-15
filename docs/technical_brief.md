# Technical brief

## Decision problem

A feedlot manager has to place each arrival cohort on one action for the next 45 days when staff hours, pen space, and treatment throughput are already tight. The user is that manager, across four synthetic yards in the Texas Panhandle and western Kansas. The decision unit is the arrival cohort, not the individual animal. The product compares options. It does not classify cattle, and it does not prescribe. Any action that contemplates metaphylaxis is labeled veterinary review and stays with a veterinarian.

The arrival record covers four domains. Animal: head count, sex, arrival weight. Management: source count, travel distance, weaning, and vaccination, each known or unknown. Nutrition: ration-transition status and bunk space per head. Environment: arrival quarter, plus a yard-level weather-stress flag. That flag is a stored field. There is no weather API.

## Provenance

Every figure in the demo carries one of three tags.

- **Published.** From Rojas et al. 2022: the 15% first-treatment morbidity cutoff, and from its Table 3 the $151.18 cost of a morbid animal, the $23.60 metaphylaxis cost per animal, and 50% metaphylaxis efficacy.
- **Synthetic.** The eight cohorts, four yards, capacities, and weather-stress flags written by `data/generate_demo_data.py`.
- **Assumption.** Risk coefficients, the non-metaphylaxis effect sizes, program costs, and exposure units.

The generator, the CSVs, and `data/data_dictionary.md` are in the same folder. Unknown cells stay unknown. Travel, weaning, or vaccination left unknown withholds a confident call. A missing head count or arrival weight rejects the row, because those fields define the cohort. The score never writes the reference profile back into a blank cell.

## Evidence

The only published number used as a threshold is 15% first-treatment morbidity (Rojas et al. 2022). A cohort whose known-fields point estimate is at or above that line is model-high-risk. That flag is not the probability P(morbidity ≥ 15%), and it is not the yard's current-practice rule. Rojas cattle-level records are not in this app. This app does not report an AUC, and it does not claim the Rojas model's accuracy as its own.

Directional findings in the feedlot BRD literature (Adekunle et al. 2026; Adekunle and Kaniyamattam 2026; Rojas et al. 2022; USDA 2019) motivate which fields enter the score: lighter arrival weight, more sources, a longer haul, lack of weaning or vaccination, a ration still in transition, tighter bunk space, and a colder arrival quarter. Those directions are the published part. The log-odds weights are assumptions. The yard weather-stress flag is synthetic, and its coefficient is an assumption.

## Assumptions

The known-fields score is a logistic curve around an 8% reference profile (750 lb, steer, one source, 100 miles, known weaned, known vaccinated, adapted ration, 12 inches of bunk, second quarter, no weather stress). That 8% is the intercept, not a value pasted into missing history. When a critical field is unknown, the screen shows a range across stated bounds (50 and 800 miles; weaned or not; vaccinated or not). Those bounds are assumptions. They are not a filled-in normal haul or a filled-in health history.

Expected cases equal cattle already clinically ill, plus the remaining head times the known-fields morbidity times one minus efficacy. Efficacy does not remove cattle that are already sick. Operating loss equals morbidity cost plus program cost, and those dollars are not mixed:

- Morbidity cost is $151.18 per expected case (published, Rojas 2022 Table 3).
- Metaphylaxis, and only on veterinary review, is $23.60 per head that is not already clinically ill (published, Rojas 2022 Table 3).
- Metaphylaxis efficacy is 50% on those at-risk head (published, Rojas 2022 Table 3, citing Avra et al. 2017). It is a modeling input, not a result measured in this demo.
- Enhanced surveillance is an 18% efficacy assumption and $1.50 per head. Supportive management is a 30% efficacy assumption and $4.00 per head.
- Antimicrobial exposure is a synthetic unit: one per expected case, plus one per metaphylaxis head. It is not a dollar.

Staff time is a capacity constraint, not a second labor bill. Rates are assumptions: 0.25, 0.40, 0.55, and 0.90 hours per head for standard care, supportive management, veterinary review, and enhanced surveillance. Pen is an assumption of 250 square feet per head, or 1.25 times that for supportive management. The resource window is the arrival week. That window is an assumption. The morbidity figure remains a 45-day estimate.

Current practice is a named rule, separate from the model. Veterinary review when arrival weight is under 600 lb and source count is at least 2. Every other cohort stays on standard care. The 600 lb and two-source cutoffs are the operating rule, tagged assumption.

## Evaluation

Evaluation here is a check that the arithmetic and the solver do what they say. It is not a test of predictive accuracy. `pytest` reports 29 passed, covering:

- Risk math. A lighter weight raises the estimate. A missing haul is stored as unknown, not as 100 miles. Morbidity and P(above 15%) are different numbers. Lot 4388, missing travel, weaning, and vaccination, gets no confident call.
- Cost accounting. For veterinary review, program cost is at-risk head times $23.60, morbidity cost is expected cases times $151.18, and operating loss is the sum of those two. Changing one constant does not change the other.
- Constraint feasibility. A solved plan stays inside staff, pen, and treatment on every yard. One hour under the standard-care floor is infeasible. Cattle already clinically ill are not dropped. The seeded staff cut changes Lot 4401's action and the yard totals.

No model was trained on these synthetic labels. No accuracy, sensitivity, or AUC is reported.

## Trade-offs

On the shortage file, pen is full, so supportive management does not fit even though, for Lot 4401, its assumed operating loss is lower than surveillance. Staff is full. TX-A has 220 hours, exactly enough for enhanced surveillance on Lot 4401 (180 hours) and standard care on the other TX-A lot. That is the operating-loss choice at the published constants: about 45.7 expected cases, about $7,206, and about 45.7 exposure units for that lot. The named baseline, veterinary review, has fewer cases (about 29.4) but a higher operating loss (about $9,073) and much higher exposure (about 225 units), and it requires a veterinarian. Applied to the whole file, that rule is already infeasible: TX-B would need 101 staff hours and has 65.

Cutting TX-A staff to 90 hours, the standard-care floor, removes surveillance. The feasible recommendation for Lot 4401 becomes standard care. Yard totals move from about 182.3 cases, $27,858, and 182.3 exposure units to about 191.4 cases, $28,941, and 191.4 exposure units. Health is worse, operating loss is higher, and antimicrobial exposure rises because more cases mean more therapeutic exposure. The plan does not add metaphylaxis to make up the difference. Pen and treatment stay inside their caps. One hour under 90 is refused.

A separate control can set the case-loss constant to $400. That value is an assumption, not a published cost. At $400, operating loss can select veterinary review for Lot 4401. Minimizing modeled morbidity selects veterinary review at $151.18. Minimizing exposure does not. All three objectives use the same constraints. The veterinary-review flag still means a veterinarian decides.

## Limitations

The cohorts, capacities, and weather-stress flags are synthetic. They are not a validation set, and they are not a claim about any real yard. Effect sizes and dollar constants are assumptions. The 15% line is a published benchmark only. This app does not claim Rojas AUC, or any AUC, as its accuracy. It does not see individual animals, does not call a weather service, and does not store records. It will not withhold care from cattle that are already clinically ill, and it will not turn veterinary review into a prescription.

## References

This section is outside the three-page body.

- Rojas, H.A.; White, B.J.; Amrine, D.E.; Larson, R.L. Predicting Bovine Respiratory Disease Risk in Feedlot Cattle in the First 45 Days Post Arrival. *Pathogens* 2022, 11, 442. https://doi.org/10.3390/pathogens11040442. Used for the 15% cutoff and Table 3 constants. Cattle-level records are not used, and its AUC (0.68 to 0.79) is not claimed here.
- Avra, T.D.; Abell, K.M.; Shane, D.D.; Theurer, M.E.; Larson, R.L.; White, B.J. A Retrospective Analysis of Risk Factors Associated with Bovine Respiratory Disease Treatment Failure in Feedlot Cattle. *J. Anim. Sci.* 2017, 95, 1521–1527. Cited by Rojas for 50% metaphylaxis efficacy.
- Adekunle, A.; Gaines, A.; Estefano, N.; Lenin, D.; Hole, P.; Khandelwal, R.; Cooke, R.; Kaniyamattam, K. Mapping Variability in Bovine Respiratory Disease Risk Factors in Beef Production Systems: A Scoping Review. *Animals* 2026, 16, 1726. https://doi.org/10.3390/ani16111726. Risk-factor directions.
- Adekunle, A.; Kaniyamattam, K. Bovine Respiratory Disease: Epidemiological Drivers, Transmission Dynamics, and Economic Implications in Beef Production Systems. *Agriculture* 2026, 16, 311. https://doi.org/10.3390/agriculture16030311. Risk-factor directions and the timing of BRD cases.
- Johnson, K.K.; Pendell, D.L. Market Impacts of Reducing the Prevalence of Bovine Respiratory Disease in United States Beef Cattle Feedlots. *Front. Vet. Sci.* 2017, 4, 189. https://doi.org/10.3389/fvets.2017.00189. Context for the $23.60 NAHMS treatment cost.
- Weber, K.M.D.; Schroeder, T.C.; Renter, D.G.; Pendell, D.L.; Tonsor, G.T. Evaluation of Bovine Respiratory Disease Morbidity in the Feedlot and its Effect on Net Return Distributions. AAEA Annual Meeting poster, 2024. Context for weight-dependent losses.
- USDA APHIS. *Antimicrobial Use and Stewardship on U.S. Feedlots, 2017.* NAHMS, May 2019. Risk factors feedlots use to decide group treatment.
