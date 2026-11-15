"""ASGI entry for the shortage demo. The Streamlit UI stays in streamlit_app.py."""

from __future__ import annotations

from functools import lru_cache
from html import escape

from starlette.applications import Starlette
from starlette.responses import HTMLResponse, PlainTextResponse
from starlette.routing import Route

from src.data_loader import load_demo
from src.format import money, num, pct
from src.optimizer import evaluate_assignment, solve
from src.pipeline import Context, build_context
from src.practice import action_label
from src.reporting import decision_summary
from src.risk_model import why_line
from src.schema import DEMO_YARD_ID, INCOMPLETE_COHORT_ID, PRIORITY_COHORT_ID


def _e(value: object) -> str:
    return escape(str(value), quote=True)


def _cohort(context: Context, cohort_id: str):
    return next(item for item in context.cohorts if item.cohort_id == cohort_id)


@lru_cache(maxsize=1)
def _scenario():
    """Shortage file, seeded plan, and the TX-A staff cut. Same engines as the Streamlit demo."""
    cohorts, yards = load_demo("shortage")
    context = build_context(cohorts, yards)
    seeded = solve(
        context.cohorts,
        context.metrics,
        context.yards,
        objective="operating_loss",
    )
    txa = context.yards[DEMO_YARD_ID]
    cut_hours = float(txa.demo_staff_hours)
    staff_hours = {DEMO_YARD_ID: cut_hours}
    cut = solve(
        context.cohorts,
        context.metrics,
        context.yards,
        objective="operating_loss",
        staff_hours=staff_hours,
    )
    practice = evaluate_assignment(
        {cohort.cohort_id: context.practice[cohort.cohort_id] for cohort in context.cohorts},
        context.cohorts,
        context.metrics,
        context.yards,
        staff_hours=staff_hours,
        objective="operating_loss",
    )
    note = (
        f"TX-A staff hours in this solve: {cut_hours:.1f} "
        f"(seeded {txa.staff_hours:.1f}, demo cut {txa.demo_staff_hours:.1f})."
    )
    summary = decision_summary(context, cut, practice, "shortage", note)
    return context, seeded, cut, practice, summary


def render_summary() -> str:
    return _scenario()[4]


def _staff_cut_line(seeded, cut) -> str:
    if not cut.feasible:
        return cut.message
    seeded_action = seeded.assignment.get(PRIORITY_COHORT_ID) if seeded.feasible else None
    cut_action = cut.assignment.get(PRIORITY_COHORT_ID)
    if seeded_action and cut_action and seeded_action != cut_action:
        return (
            f"Staff hours changed Lot 4401 from {action_label(seeded_action)} "
            f"to {action_label(cut_action)}. "
            "Cases, operating loss, and antimicrobial exposure updated from this solve."
        )
    if cut_action:
        return (
            f"Feasible plan. Lot 4401 is on {action_label(cut_action)}. "
            "Staff, pen, and treatment are within their limits."
        )
    return cut.message


def _withheld_line(context: Context) -> str:
    scored = context.scored[INCOMPLETE_COHORT_ID]
    if scored.confident_call:
        return (
            "Records are complete enough to compare actions. "
            "This is still an assumption-based estimate, not a validated prediction."
        )
    missing = ", ".join(scored.confidence.critical_missing)
    return (
        f"No confident recommendation. Missing {missing}. "
        "Those fields were not filled with a typical value. "
        "Any known-fields figure is only a planning input."
    )


def render_page() -> str:
    context, seeded, cut, practice, summary = _scenario()
    priority = _cohort(context, PRIORITY_COHORT_ID)
    incomplete = _cohort(context, INCOMPLETE_COHORT_ID)
    incomplete_score = context.scored[INCOMPLETE_COHORT_ID]
    priority_score = context.scored[PRIORITY_COHORT_ID]
    txa = context.yards[DEMO_YARD_ID]

    rows = []
    for rank, cohort_id in enumerate(context.ranked_ids, start=1):
        cohort = _cohort(context, cohort_id)
        scored = context.scored[cohort_id]
        morbidity = "Withheld" if not scored.confident_call else pct(scored.morbidity)
        rows.append(
            "<tr>"
            f"<td>{rank}</td>"
            f"<td>{_e(cohort.cohort_name)} ({_e(cohort.cohort_id)})</td>"
            f"<td>{_e(cohort.yard_id)}</td>"
            f"<td>{cohort.head_count}</td>"
            f"<td>{_e(morbidity)}</td>"
            f"<td>{_e(scored.confidence.level)}</td>"
            f"<td>{_e(action_label(context.practice[cohort_id]))}</td>"
            "</tr>"
        )

    practice_note = (
        "Current practice is not feasible under these limits. " + " ".join(practice.violations)
        if practice.violations
        else "Current practice fits these limits."
    )
    shown = "Withheld" if not incomplete_score.confident_call else pct(incomplete_score.morbidity)
    totals = (
        f"<p>Expected cases {_e(num(seeded.totals.expected_cases))} to {_e(num(cut.totals.expected_cases))}. "
        f"Operating loss {_e(money(seeded.totals.operating_loss))} to {_e(money(cut.totals.operating_loss))}. "
        f"Antimicrobial exposure {_e(num(seeded.totals.amu))} to {_e(num(cut.totals.amu))} synthetic units.</p>"
        if seeded.feasible and cut.feasible
        else ""
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>BRD Command Center</title>
  <style>
    body {{
      margin: 0;
      background: #F3F4F6;
      color: #1B1E23;
      font-family: "Segoe UI", "Helvetica Neue", Helvetica, Arial, sans-serif;
    }}
    main {{
      max-width: 980px;
      margin: 0 auto;
      padding: 1.4rem 1.1rem 3rem;
    }}
    h1 {{
      font-size: 1.85rem;
      letter-spacing: -0.03em;
      margin-bottom: 0.2rem;
    }}
    h2 {{ font-size: 1.15rem; margin-top: 1.8rem; }}
    a {{ color: #B85C38; }}
    .banner, section, pre {{
      background: #FFFFFF;
      border: 1px solid #E2E4E8;
    }}
    .banner {{
      border-left: 4px solid #B85C38;
      padding: 0.75rem 0.95rem;
    }}
    section {{ padding: 0.9rem 1rem; }}
    .call {{
      border-left: 4px solid #B85C38;
      padding-left: 0.75rem;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.92rem;
    }}
    th, td {{
      text-align: left;
      padding: 0.35rem 0.4rem;
      border-bottom: 1px solid #E2E4E8;
    }}
    pre {{
      white-space: pre-wrap;
      padding: 0.9rem 1rem;
      font-size: 0.84rem;
      line-height: 1.45;
    }}
    .nav {{ margin: 0.8rem 0 0; }}
    .nav a {{ margin-right: 1rem; }}
  </style>
</head>
<body>
<main>
  <h1>BRD Command Center</h1>
  <p>Feedlot arrival decisions for four Texas Panhandle and western Kansas yards.</p>
  <div class="banner">
    <strong>Synthetic data.</strong>
    Yard volumes, cohort rows, and weather-stress flags are synthetic.
    The 15% line and the $151.18, $23.60, and 50% metaphylaxis constants are published (Rojas et al. 2022).
    Other effect sizes and the risk coefficients are assumptions, not validated accuracy.
    Medication actions are not prescriptions.
  </div>
  <p class="nav">
    <a href="#shortage">Shortage</a>
    <a href="#staff-cut">Lot 4401 staff cut</a>
    <a href="#withheld">Lot 4388</a>
    <a href="#summary">Decision summary</a>
    <a href="/summary">Plain text</a>
  </p>

  <h2 id="shortage">Shortage scenario</h2>
  <section>
    <p>Ranked by standard-care expected cases. Morbidity is an assumption-based 45-day estimate.</p>
    <table>
      <thead>
        <tr>
          <th>Rank</th><th>Cohort</th><th>Yard</th><th>Head</th>
          <th>45-day morbidity</th><th>Confidence</th><th>Current practice</th>
        </tr>
      </thead>
      <tbody>
        {''.join(rows)}
      </tbody>
    </table>
    <p><strong>Why {_e(priority.cohort_name)} ranks first.</strong> {_e(why_line(priority_score))}</p>
    <p>{_e(practice_note)}</p>
  </section>

  <h2 id="staff-cut">Lot 4401 staff cut</h2>
  <section>
    <p>Hard limits: staff hours, pen space, and treatment throughput. Welfare floors stay on.</p>
    <p>Seeded {_e(f"{txa.staff_hours:.0f}")} h on {_e(DEMO_YARD_ID)}.
       Demo cut {_e(f"{txa.demo_staff_hours:.0f}")} h, the standard-care floor.</p>
    <p class="call">{_e(_staff_cut_line(seeded, cut))}</p>
    {totals}
  </section>

  <h2 id="withheld">Lot 4388</h2>
  <section>
    <p><strong>{_e(incomplete.cohort_name)}</strong> · {_e(incomplete.cohort_id)} · {_e(incomplete.yard_id)}</p>
    <p class="call">{_e(_withheld_line(context))}</p>
    <p>45-day morbidity: {_e(shown)}. P(morbidity at or above 15%): {_e(pct(incomplete_score.p_high_risk))}.</p>
    <p>Do not treat a known-fields figure as a call against the 15% benchmark when the record is incomplete.</p>
  </section>

  <h2 id="summary">Decision summary</h2>
  <p>Text export for the shortage file after the demo staff cut. <a href="/summary">Open as plain text</a>.</p>
  <pre>{_e(summary)}</pre>
</main>
</body>
</html>
"""


def homepage(_request):
    return HTMLResponse(render_page())


def summary(_request):
    return PlainTextResponse(render_summary())


app = Starlette(
    routes=[
        Route("/", homepage),
        Route("/summary", summary),
    ]
)
