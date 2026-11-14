# Decision record

| # | Decision | Choice | Rationale | Consequence |
|---|----------|--------|-----------|-------------|
| 1 | Product and user | BRD Command Center for a feedlot manager across four Texas Panhandle and western Kansas yards | Prompt asks for post-arrival cattle-health decisions, not a classifier | Medication stays under veterinary review; the manager compares options |
| 2 | Hours left | About 52 hours until Sunday, November 15, 2026, 11:00 PM CST | Stated deadline | Core path Friday night; extras only after it runs |
| 3 | Decision unit | Arrival cohort, not individual animals | Rojas 2022 is cohort-level and 45-day; group decisions match feedlot practice | UI and optimizer are cohort rows |
| 4 | Named API | none named | No paid access allowed | Local Python only: Streamlit, pandas, PuLP, Plotly |
| 5 | Wow moment | Tightening staff or treatment capacity live re-allocates the plan and updates health, cost, and antimicrobial totals | Judges must see feasibility, not a static chart | Optimizer is on the demo path, not a later extra |
| 6 | Evidence | Three tags: published, synthetic, adjustable assumption | Prompt requires provenance and forbids treating synthetic fit as validation | Every number in the UI carries a tag |
| 7 | Domains | Animal: head count, sex, arrival weight. Management: source count, travel distance, weaning and vaccination as known or unknown. Nutrition: ration-transition status and bunk space per head. Environment: arrival quarter plus a yard-level weather-stress flag | Prompt requires all four domains; a live weather API stays cut | Missing values stay unknown and lower confidence |
| 8 | Baseline | Current practice is a named rule: veterinary review for cohorts already tagged high-risk by light arrival weight and multiple sources; every other cohort stays on standard care | Judges must see a comparison to today's approach | Every alternative is scored against that rule |
| 9 | Constraints | Staff hours, pen space, and treatment throughput are hard limits in the optimizer and in the seeded yards | A staff-only story misses pen and treatment feasibility | The demo wow is still the staff cut; pen and treatment can already be binding |

## Named API
none named

## Demo
Judge loads the shortage scenario, sees why one cohort is prioritized, compares it with current practice, cuts staff hours, watches the feasible plan change, hits one incomplete-record cohort that refuses a confident call, and exports the decision summary. About three minutes.

## Must-have
- Seeded four-yard demo from a committed generator, with binding staff, pen, and treatment limits
- Explainable 45-day morbidity estimate, separate from P(high-risk), with missing-data uncertainty
- Named current-practice rule versus alternatives (health, cost, antimicrobial exposure)
- Live constraint optimizer with welfare floors and veterinary-review flags
- CSV upload that rejects bad files
- Downloadable decision summary
- Data dictionary, the generator script, the demo files it writes, evidence registry, technical brief (3 pages), demonstration case, AI disclosure

## Cut
- Training a model on synthetic labels and reporting accuracy
- Live weather APIs, maps, and extra intervention types
- Day-N reassessment beyond a labeled field split
- Auto-prescribing or withholding care from clinically sick cattle
- Auth, database, paid APIs, microservices

## Risks
- Streamlit can look plain; polish only the screens the storyboard opens
- Intervention effect sizes are assumptions; the UI must say so
- Rojas cattle-level data are not public; do not claim their AUC

## Accepted unknowns
| Unknown | Owner | Resolve during |
|---------|-------|----------------|
| Teammate count beyond the user directing agents | builder | the build |
| Exact GitHub repo name | builder | the build |

## Rejected
- Individual-animal primary unit
- ML-only dashboard
- Hardcoded recommendation charts

## Completion criteria
- Clean install from README with no paid key
- Changing staff hours changes the selected actions and the projected totals
- Missing history lowers confidence instead of inventing a normal value
- Optimizer never exceeds capacity or a welfare floor
- pytest covers risk math, cost accounting, and constraint feasibility
