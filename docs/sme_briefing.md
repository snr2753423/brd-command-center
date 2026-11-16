# SME assumption briefing

Short pack for a veterinarian or feedlot SME to stress-test planning assumptions and the named current-practice rule. Numbers and tags match `docs/evidence_registry.md`, `src/assumptions.py`, and `src/practice.py`. Demo data are synthetic. This document does not invent clinical claims.

## What the tool does

Local decision aid for a feedlot manager across four synthetic yards. Decision unit: **arrival cohort**, first **45 days on feed**.

- Estimates 45-day BRD morbidity and shows uncertainty when history is incomplete.
- Compares four actions against a named current-practice baseline: standard care, enhanced surveillance, supportive management, veterinary review.
- Scores cases, BRD deaths, operating loss, antimicrobial exposure units, and resource use.
- Builds a feasible plan under hard staff, pen, and treatment limits without cutting welfare floors (standard-care monitoring; treat cattle already clinically ill).
- Tags every number published, derived, synthetic, or assumption.

## What the tool does not do

- Does not prescribe or withhold medication. Veterinary review is a flag for a veterinarian, not a prescription.
- Does not claim measured predictive accuracy on real cattle. Calibration matches Rojas et al. 2022 summary statistics on a synthetic population.
- Does not impute missing haul, weaning, or vaccination as normal. Default plans on the worst case of the unknown-state range and withholds a confident call.
- Does not score individual animals, reassess day-by-day, call live weather APIs, or ship private yard CSVs.

## Current-practice rule (plain language)

Veterinary review only when **arrival weight is under 600 lb** and the cohort has **at least two sources**. Every other cohort stays on **standard care**.

That rule is the comparison baseline. It is **not** the model’s ≥15% first-45-day morbidity line (Rojas et al. 2022). Example: a cohort can sit above 15% with one source and still stay on standard care under the rule. The 600 lb and ≥2-source cutoffs are **assumptions** (`src/practice.py`).

## Assumptions tagged for review

| ID | Item | Default | Tag |
|----|------|---------|-----|
| A1 | Light-weight cutoff (practice rule) | 600 lb | Assumption |
| A2 | Multiple-source minimum (practice rule) | ≥ 2 | Assumption |
| A3 | Surveillance efficacy | 18% | Assumption |
| A4 | Surveillance program cost | $1.50 / head | Assumption |
| A5 | Supportive efficacy | 30% | Assumption |
| A6 | Supportive program cost | $4.00 / head | Assumption |
| A7 | Standard-care incremental efficacy | 0% | Assumption |
| A8 | Relative risk-coefficient magnitudes | see `src/assumptions.py` | Assumption (signs follow published risk-factor direction) |
| A9 | Global risk scale | ~2.08 | Assumption (calibration lever, not measured accuracy) |
| A10 | Reference arrival profile | 750 lb, 1 source, 100 mi, … | Assumption profile |
| A11 | Calibration population field mix | `FIELD_MIX` in `src/calibration.py` | Assumption |
| A12 | Unknown-field planning mode | Worst case | Assumption (policy) |
| A13 | Unknown haul band | 50–800 mi | Assumption |
| A14 | Unknown bunk band | 6–18 in / head | Assumption |
| A15 | Extra uncertainty when fields missing | per-field logit SD adds | Assumption |
| A16 | Staff hours / head | 0.25 / 0.40 / 0.55 / 0.90 | Assumption |
| A17 | Pen density | 250 sq ft / head; 1.25× supportive | Assumption |
| A18 | Stress morbidity cost | $450 / case | Assumption (not published) |
| A19 | Antimicrobial exposure units | 1 / case + 1 / metaphylaxis head | Synthetic |
| A20 | BRD share of deaths (midpoint) | 65% of 50–80% range | Midpoint assumption |
| A21 | BRD cases in first 45 days (midpoint) | 72.5% of 65–80% range | Midpoint assumption |

Published anchors (context, not free parameters): 15% high-risk line; $151.18 case loss; $23.60 metaphylaxis cost; 50% metaphylaxis efficacy; 6.3% mean 45-day morbidity (Rojas et al. 2022); USDA NAHMS death rates. Derived deaths-per-case and unexplained spread: see `docs/evidence_registry.md`.

## Suggested review questions

1. Is light weight + multi-source how your yards actually send cohorts to vet review / metaphylaxis consideration?
2. Should 600 lb or ≥2 sources change, or should other gates (already-ill head, weaning, vaccination) force review?
3. When capacity is short, what is the real fallback ranking among standard care, surveillance, supportive, and review?
4. Which risk fields are over- or under-weighted relative to triage practice?
5. Is worst-case planning for missing history the right posture?
6. Are 18% / 30% non-metaphylaxis efficacies and $1.50 / $4.00 program costs defensible as planning assumptions?
7. Are staff-hour and pen rates in a believable arrival-week range?
8. Does any wording sound like a prescription or a validated accuracy claim?

## What useful feedback looks like

```text
ID or topic:
Verdict: keep / change / remove / needs citation
If change: proposed value or plain-language rule
Why: short operational or clinical reason
Evidence: cite, yard SOP, or “expert judgment — no cite”
Confidence: high / medium / low
```

Most useful: a one-sentence rewrite of the current-practice rule, a reject list of assumptions that must not be shown as known, and wording fixes that avoid clinical overclaim.

## Related docs

- `docs/evidence_registry.md` — every number and tag
- `docs/decision-record.md` — product decisions, including the named baseline
- `docs/demonstration_case.md` — Lot 4401 worked example
- `docs/technical_brief.md` — methods and limits
- `src/practice.py` / `src/assumptions.py` — executable defaults
