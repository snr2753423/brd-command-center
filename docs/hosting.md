# Hosting (optional)

This repo is built for a **local hackathon demo**. Hosting is optional. There is no auth, no paid cloud dependency, and no required secrets.

## Local (default)

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Python 3.11+. Demo CSVs ship in `data/`. No `.env` file is needed for the app.

Optional static shortage page (same engines, no Streamlit widgets):

```bash
pip install -r requirements.txt
uvicorn app:app --reload
```

- Streamlit UI: `streamlit_app.py`
- ASGI shortage demo: `app.py` via `uvicorn app:app`
  - `/` HTML storyboard beats (ranked shortage, Lot 4401, staff cut, Lot 4388, summary)
  - `/summary` plain-text decision summary
  - `/health` liveness (`ok`)
  - `/ready` readiness (builds the shortage scenario)
- `uvicorn[standard]` and `httpx2` are pinned in `requirements.txt` (ASGI serve + Starlette TestClient).
- Theme: `.streamlit/config.toml` (committed). Keep secrets out of git; `.streamlit/secrets.toml` is ignored and unused by this demo.

## Streamlit Community Cloud (optional)

If you want a shareable UI link without paid infra:

1. Push this repository to GitHub (already public for the submission).
2. In [Streamlit Community Cloud](https://share.streamlit.io/), deploy from the repo.
3. **Main file path:** `streamlit_app.py`
4. Python version: 3.11 or 3.12. Dependencies come from `requirements.txt` (Streamlit, pandas, NumPy, PuLP, Plotly, Starlette, uvicorn, httpx2, pytest).

No secrets, API keys, or environment variables are required for the demo. Leave Cloud secrets empty. CSV upload (if used) stays in the session; nothing is written to a database.

Community Cloud free tier limits apply (idle sleep, resource caps). Treat a hosted URL as a convenience for judges or teammates, not production ops.

## Environment notes

| Need | Status |
|------|--------|
| Accounts / login | None |
| Paid APIs / weather / DB | None |
| Required env vars | None for Streamlit or ASGI |
| PuLP CBC | Bundled with `pulp==2.9.0` in requirements |

Rebuilding demo data or recalibrating (`data/generate_demo_data.py`, `data/calibrate_to_rojas.py`) is local maintainer work, not a deploy step.

## Disclaimers (always)

- **Synthetic data.** Cohorts, yards, capacities, and weather-stress flags are generated demo rows, not records from a yard.
- **Not a prescription.** Medication actions require veterinary review. The tool does not prescribe or withhold drugs.
- **Assumption-based.** Outside the published Rojas et al. 2022 constants called out in-app, effect sizes and risk coefficients are assumptions, not validated accuracy.

See the in-app banner, [demonstration case](demonstration_case.md), and [AI disclosure](ai_disclosure.md).
