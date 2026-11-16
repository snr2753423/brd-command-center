# Contributing

Short notes for collaborators on this hackathon / post-hackathon decision-aid repo.

## Setup

Python **3.11+** (CI uses **3.12**).

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest                             # expect 44 passed
```

Or: `make install && make test` (see `Makefile`). CI still runs `pip` + `pytest` directly.

## Run

| Path | Command | Role |
|------|---------|------|
| **Streamlit** (default demo) | `streamlit run streamlit_app.py` or `make run` | Judge / SME UI |
| **ASGI** (optional) | `uvicorn app:app --reload` or `make asgi` | Same engines; `/`, `/summary`, `/health`, `/ready` |

## Pull requests and CI

1. Branch from latest `main`.
2. Keep changes focused; prefer docs / fixtures / hardening over new product features unless agreed.
3. Run `pytest` locally before opening a PR.
4. GitHub Actions (`.github/workflows/ci.yml`) installs deps and runs `pytest` on push and pull request. Merge when CI is green.

## Synthetic data and no prescriptions

- Demo cohorts and yards are **synthetic**, calibrated to published summaries (Rojas et al. 2022). Do not present them as real cattle records.
- This tool is a **decision aid**, not a prescribing system. Medication stays with a veterinarian; do not add dose / drug-selection features.

## Docs and fixtures to know

| Link | Use |
|------|-----|
| [SME briefing](docs/sme_briefing.md) | Assumptions and named current-practice rule |
| [data dictionary](docs/data_dictionary.md) | Upload schema, units, unknowns |
| CSV dry-run fixtures | `data/upload_valid_sample.csv`, `data/upload_bad_rows.csv`, `data/upload_missing_column.csv` |
| [hosting notes](docs/hosting.md) | Local Streamlit; optional Community Cloud / ASGI |
| [demonstration case](docs/demonstration_case.md) | End-to-end Lot 4401 numbers |

## Licensing

There is **no `LICENSE` file yet**; open-source licensing is **TBD**. Do not assume MIT or any other license until the team adds an explicit choice.
