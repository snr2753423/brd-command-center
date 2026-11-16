# BRD Command Center

A decision aid for feedlot managers handling bovine respiratory disease (BRD) in the first 45 days after arrival. It scores each arrival cohort's BRD risk and shows how uncertain that score is. It compares treatment options against the yard's current practice on cases, deaths, cost, and antimicrobial use. It then builds a plan that fits each yard's staff, pen, and treatment limits. Medication decisions stay with a veterinarian.

- **Competition:** AISFS × Merck Animal Health Interdisciplinary Hackathon 2026, hosted by the AISFS Club (Artificial Intelligence for Sustainable Livestock Systems), Texas A&M University
- **Track:** Problem 1, BRD Decision Aid
- **Team:** Srivanth Rudrangi, Vignesh Nagarajan, Krish Hariharan
- **Tech stack:** Python 3.11+, Streamlit, pandas, NumPy, PuLP (CBC solver), Plotly, pytest
- **Data:** synthetic cohorts and yards, calibrated to Rojas et al. 2022 (1,733 feedlot cohorts). No paid APIs, accounts, or database.
- **Submission:** this repository, with the [technical brief](docs/technical_brief.pdf), the [demonstration case](docs/demonstration_case.md), and the [AI disclosure](docs/ai_disclosure.md)

## Run it

Requires Python 3.11 or newer.

```bash
git clone https://github.com/snr2753423/brd-command-center
cd brd-command-center
python -m venv .venv
```

Activate the environment (macOS/Linux, then Windows):

```bash
source .venv/bin/activate
```

```bash
.venv\Scripts\activate
```

Install, test, and launch:

```bash
pip install -r requirements.txt
pytest
streamlit run streamlit_app.py
```

Optional: rebuild the demo data, refit the calibration (about 30 s), or rebuild the brief PDF:

```bash
python data/generate_demo_data.py
python data/calibrate_to_rojas.py
pip install markdown && python docs/build_brief.py
```

**Demo path (~3 min):** the app opens on **Shortage**. On **Overview**, open Lot 4401 (ranked first; burden bars highlight it). On **Cohort**, show the 16.7% planning figure and uncertainty band vs the 15% line. On **Compare**, open current practice vs alternatives (cases and Δ charts). On **Optimizer**, click **Apply demo staff cut**: TX-A staff 220→90, Lot 4401 moves from enhanced surveillance to standard care, and yard totals update (103.5→109.4 cases). Open the incomplete record (Lot 4388): missing travel/weaning/vaccination, so the app refuses a confident call and plans worst-case 18.6%. **Export** downloads the labeled synthetic decision summary. Leave **Extras** and CSV upload off this path unless asked.

## Repo roadmap

```text
streamlit_app.py        Dashboard: Overview, Cohort, Compare, Optimizer, Export
app.py                  ASGI entry (uvicorn app:app) serving the demo path
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
  data_dictionary.md    Columns, units, and how unknowns are handled
docs/
  technical_brief.pdf   Three-page brief plus references
  demonstration_case.md One end-to-end decision for Lot 4401
  evidence_registry.md  Source for every number
  sme_briefing.md       SME pack to stress-test assumptions and the practice rule
  ai_disclosure.md      AI tools and external resources
tests/                  pytest suite (risk, costs, optimizer, calibration, app)
```
