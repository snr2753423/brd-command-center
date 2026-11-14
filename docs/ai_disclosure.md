# AI-tool disclosure

An AI coding assistant in Cursor drafted this app, the synthetic generator, the tests, and these documents. A person set the product decisions: cohort as the decision unit, the named current-practice rule, the three hard constraints, and the literature constants. The assistant did not fit a model to outcomes, did not retrieve Rojas cattle-level records, and did not call a paid API or a weather service.

What the assistant produced is not a measurement.

- **Published.** The 15% first-treatment morbidity benchmark is the Rojas et al. 2022 threshold named in the decision record. This app does not claim that paper's AUC, or any AUC, as its own accuracy.
- **Synthetic.** Cohorts, yard capacities, and weather-stress flags are generated demo rows. They are not records from a yard.
- **Assumption.** Risk coefficients, the 8% reference profile, effect sizes, the $23.60 metaphylaxis cost, the $151.18 case cost, and the 50% efficacy are labeled assumptions. They are not validated accuracy.

The optimizer is a local PuLP solve. Tests check the arithmetic, the missing-data rule, and the constraints. They do not validate predictive performance. Veterinary review is a flag for a veterinarian. The app does not prescribe, and it is not a substitute for clinical judgment.
