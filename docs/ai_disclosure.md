# AI-tool and external-resource disclosure

## AI tools

- **Cursor (AI coding agent)** drafted the first version of this app, the synthetic generator, the tests, and these documents.
- **Claude Code (Anthropic)** made a later revision. It checked the cost and efficacy constants against the source papers and corrected their citations. It routed uploaded cohorts into the optimizer, added per-yard capacity controls, changed how unknown fields are planned, added a mortality estimate, calibrated the baseline to Rojas et al. 2022 summary statistics, and exported the technical brief to PDF.

A person set the product decisions: cohort as the decision unit, the named current-practice rule, the three hard constraints, and which published constants to use. The team reviewed the AI output and is responsible for the claims, citations, and results. No AI tool fitted a model to real outcomes, retrieved Rojas cattle-level records, or called a paid API or a weather service.

## External resources

The papers listed under References in `docs/technical_brief.md`, all from the challenge resource folder. Python packages are listed in `requirements.txt`. No restricted data is included.

## What is and is not a measurement

- **Published.** From Rojas et al. 2022: the 15% first-treatment morbidity cutoff, and from its Table 3 the $151.18 morbid-animal cost, the $23.60 metaphylaxis cost per animal, and 50% metaphylaxis efficacy. This app does not claim that paper's AUC, or any AUC, as its own accuracy.
- **Synthetic.** Cohorts, yard capacities, and weather-stress flags are generated demo rows. They are not records from a yard.
- **Assumption.** Risk coefficients, the reference profile, the other effect sizes, and program costs. They are not validated accuracy.

The optimizer is a local PuLP solve. Tests check the arithmetic, the missing-data rule, and the constraints. They do not validate predictive performance. Veterinary review is a flag for a veterinarian. The app does not prescribe, and it is not a substitute for clinical judgment.
