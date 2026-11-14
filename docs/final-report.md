# Final report

BRD Command Center is a local Streamlit app for a feedlot manager. The shortage path runs on synthetic data.

## What the slice does

Four yards, with Lot 4401 ranked first and explained by its drivers. Current practice is a named rule: veterinary review only when arrival weight is under 600 lb and there are at least two sources. Every alternative is compared with that rule. Staff hours, pen space, and treatment throughput are hard PuLP limits, and welfare floors stay on.

The demo cut takes TX-A from 220 staff hours to 90. Lot 4401 moves from enhanced surveillance to standard care. Expected cases go from about 182.3 to 191.4, operating loss from about $27,858 to $28,941, and antimicrobial exposure rises with the cases. Lot 4388 is missing travel, weaning, and vaccination. The app withholds a confident call and does not fill those fields. The text export is labeled synthetic. A CSV upload rejects bad rows and a file that is missing `head_count`.

After that path, a morbidity-cost control ($151.18 versus a $400 stress value) can flip Lot 4401 to veterinary review, and three objectives share the same optimizer. Neither extra is on the three-minute path.

## Checks

`pytest`: 28 passed. That includes risk math, separate morbidity and metaphylaxis dollars, constraint feasibility, the staff cut, the cost flip, and the storyboard in the app.

Launch, from `brd-decision-aid`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

No paid key. The demo CSVs are already in `data/`, next to `data/generate_demo_data.py` and `data/data_dictionary.md`.

## Repository

Not pushed. Creating `snr2753423/brd-command-center` failed with exit code 4:

```
To get started with GitHub CLI, please run:  gh auth login
Alternatively, populate the GH_TOKEN environment variable with a GitHub API authentication token.
```

`gh auth status` had already reported: `You are not logged into any GitHub hosts. To log in, run: gh auth login`. The commit is local on `main`.

## Limits

The 15% benchmark is the published Rojas threshold. The dollar constants, the 50% efficacy, and the other effect sizes are assumptions, not validated accuracy. Medication actions require veterinary review. The weather-stress flag is synthetic. There is no live weather API.
