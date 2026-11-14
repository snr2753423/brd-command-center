# BRD Command Center

A local decision aid for a feedlot manager. It turns synthetic arrival cohorts into an explainable 45-day morbidity estimate, a comparison with today's rule, and a resource-feasible plan. No account, no database, no paid API.

## Launch

```bash
cd brd-decision-aid
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
streamlit run app.py
```

Python 3.11 or newer. PuLP is pinned to 2.9 because that release bundles the CBC solver. The demo CSVs are already in `data/`. To rewrite them:

```bash
python data/generate_demo_data.py
```

The app opens on the shortage scenario. Use **Apply demo staff cut** on the Optimizer screen. Lot 4401 should move off enhanced surveillance, and the case, cost, and antimicrobial totals should change. Lot 4388 should refuse a confident call. The CSV check rejects `data/upload_bad_rows.csv` and `data/upload_missing_column.csv`.

## Docs

- `docs/design.md` — visual rules for the storyboard screens
- `docs/decision-record.md`, `docs/scope.md`, `docs/expansion.md` — product lock
- `data/data_dictionary.md` — columns, next to the generator
- `docs/evidence_registry.md` — published, synthetic, and assumption tags
- `docs/technical_brief.md` — method and limits
- `docs/demonstration_case.md` — the three-minute path
- `docs/ai_disclosure.md`
- `docs/final-report.md`
