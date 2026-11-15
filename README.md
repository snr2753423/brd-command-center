# BRD Command Center

A local decision aid for a feedlot manager. It turns synthetic arrival cohorts into an explainable 45-day morbidity estimate, a comparison with today's rule, and a resource-feasible plan. No account, no database, no paid API.

## Launch

```bash
git clone https://github.com/snr2753423/brd-command-center
cd brd-command-center
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest
streamlit run streamlit_app.py
```

`app.py` is the ASGI entry (`uvicorn app:app`). It serves the same shortage path: the Lot 4401 staff cut, Lot 4388 with no confident call, and the text decision summary.

Python 3.11 or newer. PuLP is pinned to 2.9 because that release bundles the CBC solver. The demo CSVs are already in `data/`. To rewrite them, or to refit the risk score to the Rojas et al. 2022 summary statistics (about 30 seconds):

```bash
python data/generate_demo_data.py
python data/calibrate_to_rojas.py
```

The app opens on the shortage scenario. Use **Apply demo staff cut** on the Optimizer screen. Lot 4401 should move off enhanced surveillance, and the case, cost, and antimicrobial totals should change. Lot 4388 should refuse a confident call. **Calibration against Rojas et al. 2022** on the Overview screen shows the synthetic population against the published figures. The CSV check rejects `data/upload_bad_rows.csv` and `data/upload_missing_column.csv`.

Every yard's staff, pen, and treatment limit has its own slider on the Optimizer screen. Accepted upload rows can be added to the plan or replace the seeded cohorts. The optimizer then re-solves with them. If a limit is too tight, the error names the yard and the limit that is short.

## Docs

- `docs/design.md` — visual rules for the storyboard screens
- `docs/decision-record.md`, `docs/scope.md`, `docs/expansion.md` — product lock
- `data/data_dictionary.md` — columns, next to the generator
- `docs/evidence_registry.md` — published, synthetic, and assumption tags, with sources
- `docs/technical_brief.pdf` — the submitted brief: three pages plus references. Source: `docs/technical_brief.md`. Rebuild it with `pip install markdown` then `python docs/build_brief.py`, which fails if the body runs past three pages.
- `docs/demonstration_case.md` — the three-minute path
- `docs/ai_disclosure.md`
- `docs/final-report.md`
