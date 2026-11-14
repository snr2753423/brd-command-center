# Expansion

Story: a manager turns incomplete arrival records into a resource-feasible 45-day cattle-health plan and sees the trade-offs.

| Feature | Why | Effort | Tool | UI | Verdict |
|---------|-----|--------|------|----|---------|
| Assumption slider that flips the recommended action | Proves the plan is sensitive, not hardcoded | M | none | yes | approve |
| Side-by-side cost / morbidity / antimicrobial objective | Shows stewardship is a choice, not a slogan | M | PuLP | yes | approve |
| Tornado chart of every coefficient | Depth with no new decision | L | Plotly | yes | reject |
| Day-N reassessment workflow | Second product | L | none | yes | reject |
| Yard map | Decoration | M | none | yes | reject |

## Approved
1. Assumption slider (intervention effect or morbidity cost) that can flip the selected action — fallback: a documented preset pair of assumption values the demo switches between.
2. Three labeled objectives on the same optimizer (operating loss, modeled morbidity, antimicrobial exposure) — fallback: one cost objective plus a table of the other two metrics, still computed from the chosen plan.

## Rejected
- Tornado chart of every coefficient — the flip already shows sensitivity.
- Day-N reassessment — not on the three-minute path.
- Yard map — no decision changes.

## Not built
- Weather API, individual-animal drill-down, PDF typesetting beyond a markdown/text export.
