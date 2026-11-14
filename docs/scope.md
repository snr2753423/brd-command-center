# Scope

## Assessment
- Strengths: the prompt's four links (risk, action, consequences, feasibility) are one product, and the optimizer is a visible wow.
- Weaknesses: no public training set; effect sizes must stay labeled assumptions.
- Opportunities: four yards with different bottlenecks make the same cohort get different feasible plans.
- Constraints: Sunday 11:00 PM CST, no paid services, three-minute live demo, three-page brief.
- Direction: one Streamlit app, seeded data, literature-informed risk, PuLP allocation.

## Wow test
The judge reduces staff hours and the recommended action for at least one high-priority cohort changes, with health, cost, and antimicrobial totals updating from the same solve.

## Must-have
1. User opens the resource-shortage scenario. System shows four yards and a ranked cohort with drivers and a confidence flag.
2. User compares that cohort's options with the named current-practice rule (veterinary review only for light, multi-source cohorts; everyone else on standard care). System shows cases, cost, antimicrobial exposure, and resources, each tagged published, synthetic, or assumption. Pen space and treatment throughput are hard limits even when the demo only moves staff hours.
3. User lowers staff hours and re-solves. System returns a feasible plan that respects capacity and welfare floors, or says the problem is infeasible.
4. User opens a cohort with missing transport or health history. System withholds a confident recommendation.
5. User exports a decision summary.

## Cut
- Six fully designed views before the path works. Build the path screens first: overview, cohort, compare, optimizer, export. Evidence/uncertainty can be a panel on those screens.
- Scenario 4 stewardship as its own app. It is one objective weight on the same optimizer.
- Real-data ML, weather feeds, maps, auth, database.

## Storyboard
```text
0:00–0:30  Four yards, one light high-risk arrival, treatment and staff already tight
0:30–1:30  Open that cohort: drivers, missingness, baseline vs three actions
1:30–2:30  Cut staff hours; allocation and totals change (wow)
2:30–3:00  Incomplete record refuses a confident call; export the summary
```

## Hours left
About 52 hours until Sunday, November 15, 2026, 11:00 PM CST. Stated.

## Time split
- First third: the storyboard path clickable, even if plain.
- Middle third: optimizer, uncertainty, and cost tags reliable.
- Last third: rehearsal, brief, demo case, README. No new features.

## Category
AISFS × Merck Animal Health Prompt 1. Not a sponsor API track.

## Next
`feature-expansion`, then `build-hackathon`.
