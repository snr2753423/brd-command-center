# BRD Command Center

A decision aid for feedlot managers handling bovine respiratory disease (BRD) in the first 45 days after arrival. It scores each arrival cohort's BRD risk and shows how uncertain that score is. It compares treatment options against the yard's current practice on cases, deaths, cost, and antimicrobial use. It then builds a plan that fits each yard's staff, pen, and treatment limits. Medication decisions stay with a veterinarian.

- **Competition:** AISFS × Merck Animal Health Interdisciplinary Hackathon 2026, hosted by the AISFS Club (Artificial Intelligence for Sustainable Livestock Systems), Texas A&M University
- **Track:** Problem 1, BRD Decision Aid
- **Team:** Srivanth Rudrangi, Vignesh Nagarajan, Krish Hariharan
- **Tech stack:** Python 3.11+, Streamlit, pandas, NumPy, PuLP (CBC solver), Plotly, pytest
- **Data:** synthetic cohorts and yards, calibrated to Rojas et al. 2022 (1,733 feedlot cohorts). No paid APIs, accounts, or database.
- **Submission:** this repository, with the [technical brief](docs/technical_brief.pdf), the [demonstration case](docs/demonstration_case.md), and the [AI disclosure](docs/ai_disclosure.md)
- **Demo video:** [docs/demo_video.mp4](docs/demo_video.mp4) (4:52, narrated walkthrough of the click path below)
- **Contributing:** see [CONTRIBUTING.md](CONTRIBUTING.md) for setup, tests, Streamlit vs ASGI, PR/CI expectations, and synthetic-data notes

## Install

Requires Python 3.11 or newer.

```bash
git clone https://github.com/snr2753423/brd-command-center
cd brd-command-center
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest                             # expect 44 passed
```

Or: `make install && make test` (optional local shortcut; see `Makefile`). CI still uses `pip` + `pytest` directly.

Demo CSVs ship in `data/`. No `.env` or secrets are required.

## Launch (Streamlit)

```bash
streamlit run streamlit_app.py
```

The app opens on the **Shortage** scenario. This is the default judge path.

## 3-minute click path

Stay on the main path. Leave **Extras** and **Upload cohorts** closed unless asked.

1. **Overview** — ranked arrivals; Lot **4401** first (burden bars highlight it). Lot **4388** morbidity shows **Withheld**.
2. **Cohort → Open Lot 4401** — planning figure **16.7%**, P(morbidity ≥ 15%) **54.5%**, uncertainty band vs the published **15%** line.
3. **Compare → Compare with current practice** — named rule: veterinary review when arrival weight is under 600 lb and sources ≥ 2. Enhanced surveillance on Lot 4401: **30.8** cases / **$4,960** / **180** staff hours.
4. **Optimizer → Apply demo staff cut** — TX-A staff **220→90**; Lot 4401 moves enhanced surveillance → standard care; yard totals **103.5→109.4** cases, **17.1→18.1** BRD deaths, **$15,954→$16,545** operating loss.
5. **Open the incomplete record** (Lot **4388**) — missing travel / weaning / vaccination, so the app refuses a confident call and plans worst-case **18.6%**.
6. **Export → Download decision summary** — labeled synthetic summary; staff cut and refusal are both recorded.

Worked numbers and narrative: [demonstration case](docs/demonstration_case.md).

## Optional: ASGI shortage page

Same engines, no Streamlit widgets:

```bash
uvicorn app:app --reload
```

- `/` — HTML storyboard beats (ranked shortage, Lot 4401, staff cut, Lot 4388, summary)
- `/summary` — plain-text decision summary
- `/health` — liveness (`ok`)
- `/ready` — readiness (builds the shortage scenario)

## Docs and fixtures

| Link | Use |
|------|-----|
| [hosting notes](docs/hosting.md) | Local Streamlit default; optional Streamlit Community Cloud (`streamlit_app.py`); ASGI routes |
| [SME briefing](docs/sme_briefing.md) | Assumptions and the named current-practice rule for SME review |
| [data dictionary](docs/data_dictionary.md) | Columns, units, unknown-field handling |
| CSV dry-run fixtures | `data/upload_valid_sample.csv` (accept), `data/upload_bad_rows.csv`, `data/upload_missing_column.csv` |

Optional maintainer rebuilds (not needed for the demo):

```bash
python data/generate_demo_data.py
python data/calibrate_to_rojas.py
pip install markdown && python docs/build_brief.py
```

## Repo roadmap

```text
streamlit_app.py        Dashboard: Overview, Cohort, Compare, Optimizer, Export
app.py                  ASGI entry (uvicorn app:app): /, /summary, /health, /ready
src/
  risk_model.py         45-day morbidity score, drivers, unknown-field planning
  calibration.py        Fit to Rojas 2022 mean, high-risk share, and AUC
  economics.py          Cases, deaths, operating loss, antimicrobial exposure per action
  optimizer.py          PuLP plan under staff, pen, treatment limits and welfare floors
  practice.py           Named current-practice rule (the baseline)
  validation.py         CSV upload checks
  assumptions.py        Every constant, tagged published, derived, or assumption
data/
  generate_demo_data.py Writes the demo cohorts and yard capacities
  calibrate_to_rojas.py Refits the score and writes calibration_*.csv
  upload_*.csv          Dry-run CSV fixtures (valid / bad rows / missing column)
  data_dictionary.md    Columns, units, and how unknowns are handled
docs/
  technical_brief.pdf   Three-page brief plus references
  demonstration_case.md One end-to-end decision for Lot 4401
  evidence_registry.md  Source for every number
  sme_briefing.md       SME pack to stress-test assumptions and the practice rule
  hosting.md            Optional local / Community Cloud / ASGI notes (no paid infra)
  ai_disclosure.md      AI tools and external resources
tests/                  pytest suite (44 tests: risk, costs, optimizer, calibration, app, ASGI)
```
