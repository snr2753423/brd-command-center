"""BRD Command Center. Local Streamlit app. No accounts, no paid APIs."""

from __future__ import annotations

from dataclasses import replace

import pandas as pd
import streamlit as st

from src.assumptions import Assumptions
from src.charts import burden_chart, compare_chart, index_chart, totals_caption
from src.data_loader import load_demo
from src.economics import compare_to_practice
from src.format import money, num, pct
from src.optimizer import evaluate_assignment, solve
from src.pipeline import Context, build_context
from src.practice import action_label, rule_text
from src.reporting import decision_summary
from src.risk_model import domain_summary, why_line
from src.schema import (
    ACTION_LABEL,
    DEMO_YARD_ID,
    INCOMPLETE_COHORT_ID,
    OBJECTIVE_LABEL,
    OBJECTIVES,
    PRIORITY_COHORT_ID,
)
from src.validation import validate_cohort_frame

PAGES = ["Overview", "Cohort", "Compare", "Optimizer", "Export"]
FONT = '"Segoe UI", "Helvetica Neue", Helvetica, Arial, sans-serif'


def _go(page: str, cohort_id: str | None = None) -> None:
    st.session_state.page = page
    if cohort_id is not None:
        st.session_state.cohort_id = cohort_id


def _set_staff(value: float) -> None:
    st.session_state.staff_txa = float(value)


def _set_cost(value: float) -> None:
    st.session_state.morbidity_cost = float(value)


def _inject_css() -> None:
    st.markdown(
        f"""
        <style>
        html, body, [class*="css"] {{
          font-family: {FONT};
        }}
        .block-container {{
          max-width: 1180px;
          padding-top: 1.1rem;
        }}
        h1 {{
          font-weight: 650;
          letter-spacing: -0.03em;
          font-size: 1.85rem;
        }}
        .banner {{
          background: #FFFFFF;
          border: 1px solid #E2E4E8;
          border-left: 4px solid #B85C38;
          padding: 0.75rem 0.95rem;
          margin: 0.2rem 0 0.9rem 0;
          color: #1B1E23;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _banner() -> None:
    st.markdown(
        """
        <div class="banner">
        <strong>Synthetic data.</strong>
        Yard volumes, cohort rows, and weather-stress flags are synthetic.
        The 15% line is a published Rojas benchmark.
        Costs, efficacy, and risk coefficients are assumptions, not validated accuracy.
        Medication actions are not prescriptions.
        </div>
        """,
        unsafe_allow_html=True,
    )


def _cohort(context: Context, cohort_id: str):
    return next(item for item in context.cohorts if item.cohort_id == cohort_id)


def _init_state() -> None:
    _, yards = load_demo("shortage")
    txa = next(yard for yard in yards if yard.yard_id == DEMO_YARD_ID)
    st.session_state.setdefault("page", "Overview")
    st.session_state.setdefault("cohort_id", PRIORITY_COHORT_ID)
    st.session_state.setdefault("scenario_label", "Shortage")
    st.session_state.setdefault("objective", "operating_loss")
    st.session_state.setdefault("morbidity_cost", Assumptions().morbidity_cost_per_case)
    st.session_state.setdefault("staff_txa", float(txa.staff_hours))


def _scenario_name() -> str:
    return "shortage" if st.session_state.scenario_label == "Shortage" else "normal"


def _tag(text: str) -> None:
    st.caption(text)


def page_overview(context: Context, result, practice) -> None:
    st.subheader("Four yards")
    _tag("Capacities are synthetic. A meter at cap is a hard limit, not a target to exceed.")
    columns = st.columns(4)
    for column, yard in zip(columns, context.yards.values()):
        with column:
            with st.container(border=True):
                st.markdown(f"**{yard.yard_name}**")
                st.caption(f"{yard.region} · {yard.yard_id}")
                flag = "yes" if yard.weather_stress_flag else "no"
                st.caption(f"Weather-stress flag: {flag} · synthetic, not a live feed")
                st.caption(f"Tightest story point: {yard.bottleneck}")
                if result.feasible and yard.yard_id in result.by_yard:
                    use = result.by_yard[yard.yard_id]
                    st.write(f"Staff {_meter(use.staff, use.staff_capacity, 'h')}")
                    st.write(f"Pen {_meter(use.pen, use.pen_capacity, 'sq ft')}")
                    st.write(f"Treatment {_meter(use.treatment, use.treatment_capacity, 'slots')}")
                else:
                    st.caption("No feasible use to show.")

    st.subheader("Ranked arrivals")
    _tag(
        "Ranked by standard-care expected cases. "
        "Morbidity is an assumption-based 45-day estimate. "
        "P(above 15%) is a different number. The 15% benchmark is published."
    )
    rows = []
    for rank, cohort_id in enumerate(context.ranked_ids, start=1):
        cohort = _cohort(context, cohort_id)
        scored = context.scored[cohort_id]
        morbidity = "Withheld" if not scored.confident_call else pct(scored.morbidity)
        rows.append(
            {
                "Rank": rank,
                "Cohort": f"{cohort.cohort_name} ({cohort.cohort_id})",
                "Yard": cohort.yard_id,
                "Head": cohort.head_count,
                "Weight lb": f"{cohort.arrival_weight_lb:.0f}",
                "Sources": cohort.source_count,
                "45-day morbidity": morbidity,
                "P(above 15%)": pct(scored.p_high_risk),
                "Confidence": scored.confidence.level,
                "Current practice": action_label(context.practice[cohort_id]),
            }
        )
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    st.plotly_chart(
        burden_chart(context),
        width="stretch",
        config={"displayModeBar": False},
        alt="Bar chart of standard-care expected cases by cohort. Lot 4401 is highlighted.",
    )

    top = context.scored[PRIORITY_COHORT_ID]
    st.markdown(f"**Why Lot 4401 ranks first.** {why_line(top)}")
    _tag("Driver coefficients are assumptions. Head count is synthetic and only scales the cases.")
    left, right = st.columns(2)
    with left:
        st.button(
            "Open Lot 4401",
            type="primary",
            on_click=_go,
            args=("Cohort", PRIORITY_COHORT_ID),
            key="open_priority",
        )
    with right:
        st.button(
            "Open the incomplete record",
            on_click=_go,
            args=("Cohort", INCOMPLETE_COHORT_ID),
            key="open_incomplete",
        )

    if practice.violations:
        st.warning("Current practice is not feasible under these limits. " + " ".join(practice.violations))
    elif result.feasible:
        st.success("Current practice fits these limits, and a feasible allocation is ready on the Optimizer screen.")

    st.subheader("CSV check")
    _tag("Accepted rows are scored beside the seeded scenario. They do not replace it.")
    upload = st.file_uploader("Cohort CSV", type=["csv"], key="cohort_upload")
    if upload is None:
        st.info("No CSV uploaded.")
        return
    with st.spinner("Checking rows…"):
        try:
            frame = pd.read_csv(upload, dtype=str, keep_default_na=False)
        except Exception as exc:
            st.error(f"Could not read that file. {exc}")
            return
        if frame.empty:
            st.info("The file has no data rows.")
            return
        checked = validate_cohort_frame(frame, set(context.yards))
    if checked.file_errors:
        for message in checked.file_errors:
            st.error(message)
        return
    if not checked.accepted:
        st.error("Every row was rejected. Nothing was scored.")
    else:
        st.success(f"{len(checked.accepted)} row(s) accepted. {len(checked.issues)} rejected.")
        preview = build_context(list(checked.accepted), list(context.yards.values()), context.assumptions)
        scored_rows = []
        for cohort in checked.accepted:
            scored = preview.scored[cohort.cohort_id]
            scored_rows.append(
                {
                    "Cohort": cohort.cohort_id,
                    "Confidence": scored.confidence.level,
                    "45-day morbidity": "Withheld" if not scored.confident_call else pct(scored.morbidity),
                    "Current practice": action_label(preview.practice[cohort.cohort_id]),
                }
            )
        st.dataframe(pd.DataFrame(scored_rows), hide_index=True, width="stretch")
    if checked.issues:
        st.dataframe(
            pd.DataFrame(
                [{"Row": issue.row_number, "Field": issue.field, "Reason": issue.message} for issue in checked.issues]
            ),
            hide_index=True,
            width="stretch",
        )


def _meter(used: float, capacity: float, unit: str) -> str:
    ratio = used / capacity if capacity else 0
    state = "At cap" if ratio >= 0.999 else f"{ratio:.0%} used"
    if unit == "sq ft":
        return f"{used:,.0f} / {capacity:,.0f} {unit} · {state}"
    return f"{used:,.1f} / {capacity:,.1f} {unit} · {state}"


def _select_cohort(context: Context) -> str:
    labels = {cohort.cohort_id: f"{cohort.cohort_name} · {cohort.yard_id}" for cohort in context.cohorts}
    if st.session_state.cohort_id not in labels:
        st.session_state.cohort_id = context.ranked_ids[0]
    return st.selectbox(
        "Cohort",
        context.ranked_ids,
        format_func=lambda cohort_id: labels[cohort_id],
        key="cohort_id",
    )


def page_cohort(context: Context) -> None:
    cohort_id = _select_cohort(context)
    cohort = _cohort(context, cohort_id)
    scored = context.scored[cohort_id]
    yard = context.yards[cohort.yard_id]
    st.markdown(f"**{cohort.cohort_name}** · {yard.yard_name}")
    _tag(f"{yard.region}. Weather-stress flag: {'yes' if yard.weather_stress_flag else 'no'} · synthetic.")

    if not scored.confident_call:
        missing = ", ".join(scored.confidence.critical_missing)
        st.error(
            f"No confident recommendation. Missing {missing}. "
            "Those fields were not filled with a typical value. "
            "Any known-fields figure is only a planning input."
        )
    elif scored.confidence.level == "reduced":
        st.warning(
            "Reduced confidence. A non-critical field is unknown and was not imputed. "
            "You can still compare actions, with a wider range."
        )
    else:
        st.success(
            "Records are complete enough to compare actions. "
            "This is still an assumption-based estimate, not a validated prediction."
        )

    grouped = domain_summary(scored)
    columns = st.columns(4)
    titles = (
        ("animal", "Animal"),
        ("management", "Management"),
        ("nutrition", "Nutrition"),
        ("environment", "Environment"),
    )
    for column, (key, title) in zip(columns, titles):
        with column:
            st.markdown(f"**{title}**")
            for driver in grouped[key]:
                value = driver.value if driver.value is not None else "unknown"
                st.write(f"{driver.label}: {value}")

    st.caption(
        f"Already clinically ill: {cohort.clinically_ill_head} head. "
        "That count is a welfare floor. The plan cannot leave them untreated."
    )

    left, right = st.columns(2)
    with left:
        shown = "Withheld" if not scored.confident_call else pct(scored.morbidity)
        st.metric("45-day morbidity", shown)
        _tag("Assumption coefficients. Not the same number as P(above 15%).")
    with right:
        st.metric("P(morbidity ≥ 15%)", pct(scored.p_high_risk))
        _tag("Published 15% benchmark. The probability uses an assumption-based uncertainty band.")

    if scored.confidence.missing_fields:
        st.caption(
            f"Range across unknown states: {pct(scored.state_low)}–{pct(scored.state_high)}. "
            "Those bounds are assumptions, not filled-in values."
        )
    st.caption(
        f"About 90% band on the known-fields logit: {pct(scored.interval_low)}–{pct(scored.interval_high)} · assumption."
    )
    if scored.confident_call and scored.above_benchmark:
        st.caption("The known-fields point estimate is at or above the published 15% benchmark.")
    elif not scored.confident_call:
        st.caption("Do not treat the known-fields figure as a call against the 15% benchmark.")

    st.markdown(f"**Drivers.** {why_line(scored)}")
    driver_rows = []
    for driver in scored.drivers:
        contribution = "unknown" if driver.contribution is None else f"{driver.contribution:+.3f}"
        driver_rows.append(
            {
                "Domain": driver.domain,
                "Factor": driver.label,
                "Value": driver.value if driver.value is not None else "unknown",
                "Log-odds": contribution,
                "Tag": driver.evidence,
                "Note": driver.note,
            }
        )
    st.dataframe(pd.DataFrame(driver_rows), hide_index=True, width="stretch")
    st.button("Compare with current practice", type="primary", on_click=_go, args=("Compare", cohort_id))


def page_compare(context: Context) -> None:
    cohort_id = _select_cohort(context)
    cohort = _cohort(context, cohort_id)
    scored = context.scored[cohort_id]
    practice = context.practice[cohort_id]
    st.markdown(rule_text(context.assumptions))
    st.markdown(
        f"**This cohort:** {action_label(practice)}. "
        f"Arrival weight {cohort.arrival_weight_lb:.0f} lb, {cohort.source_count} sources."
    )
    _tag("The rule uses weight and source count only. It is not the 45-day morbidity estimate.")
    if not scored.confident_call:
        st.error("No confident recommendation on this record. The table is still shown so the rule can be compared.")
    if scored.confident_call and scored.above_benchmark and practice != "vet_review":
        st.warning(
            "The model estimate is at or above the 15% benchmark. "
            "Current practice stays on standard care because this lot is not both light and multi-source."
        )

    rows = compare_to_practice(cohort, scored, context.assumptions, practice)
    table = []
    for row in rows:
        role = "Current practice" if row.is_current_practice else "Alternative"
        metric = row.metric
        table.append(
            {
                "Role": role,
                "Action": action_label(row.action_id),
                "Cases": num(metric.expected_cases),
                "Δ cases": num(row.delta_cases),
                "Operating loss": money(metric.operating_loss),
                "Δ loss": money(row.delta_loss),
                "AM exposure": num(metric.amu),
                "Δ exposure": num(row.delta_amu),
                "Staff h": num(metric.staff_hours),
                "Pen sq ft": f"{metric.pen_sqft:,.0f}",
                "Treatment slots": num(metric.treatment_slots),
                "Vet review required": "yes" if metric.veterinary_review_required else "no",
            }
        )
    st.dataframe(pd.DataFrame(table), hide_index=True, width="stretch")
    _tag(
        "Cases: assumption efficacy × synthetic head count. "
        "Loss: $151.18 per case plus the action's own program cost (assumption). "
        "Metaphylaxis is $23.60 per at-risk head and is not inside the case cost. "
        "Exposure units are synthetic. Staff, pen, and treatment rates are assumptions."
    )
    st.plotly_chart(
        compare_chart(rows),
        width="stretch",
        config={"displayModeBar": False},
        alt="Expected cases for current practice and the other actions.",
    )
    if practice == "vet_review":
        st.caption(
            "Veterinary review is the current-practice action for this lot. "
            "It flags the cohort for a veterinarian. It does not prescribe metaphylaxis."
        )
    st.button("Open the optimizer", type="primary", on_click=_go, args=("Optimizer", cohort_id))


def page_optimizer(context: Context, result, practice, scenario: str, seeded) -> None:
    st.markdown("**Hard limits:** staff hours, pen space, and treatment throughput. Welfare floors stay on.")
    _tag("The live control is staff hours on TX-A. Pen and treatment do not have a second slider.")
    if scenario != "shortage":
        st.info("Normal mix uses relaxed capacities. The staff-cut demo is the shortage scenario.")
    else:
        txa = context.yards[DEMO_YARD_ID]
        cut = float(txa.demo_staff_hours)
        seed = float(txa.staff_hours)
        slider_min = float(int(cut // 2))
        st.slider(
            "TX-A arrival-week staff hours",
            min_value=slider_min,
            max_value=seed,
            step=1.0,
            key="staff_txa",
            help="Synthetic processing hours. Standard care is the welfare floor.",
        )
        one, two = st.columns(2)
        with one:
            st.button(
                "Apply demo staff cut",
                type="primary",
                key="demo_cut",
                on_click=_set_staff,
                args=(cut,),
            )
        with two:
            st.button("Restore seeded staff", key="restore_staff", on_click=_set_staff, args=(seed,))
        _tag(f"Seeded {seed:.0f} h. Demo cut {cut:.0f} h, which is the standard-care floor. Below that, the plan is refused.")

    if not result.feasible:
        st.error(result.message)
    else:
        action = result.assignment.get(PRIORITY_COHORT_ID, "")
        changed = (
            seeded is not None
            and seeded.feasible
            and seeded.assignment.get(PRIORITY_COHORT_ID) != action
        )
        if changed:
            st.success(
                f"Staff hours changed Lot 4401 from {action_label(seeded.assignment[PRIORITY_COHORT_ID])} "
                f"to {action_label(action)}. Cases, operating loss, and antimicrobial exposure updated from this solve."
            )
        else:
            st.success(
                f"Feasible plan. Lot 4401 is on {action_label(action)}. "
                "Staff, pen, and treatment are within their limits."
            )

    if practice.violations:
        st.warning("Named current practice breaks a limit. " + " ".join(practice.violations))

    if result.feasible:
        a, b, c = st.columns(3)
        with a:
            st.metric(
                "Expected cases",
                num(result.totals.expected_cases),
                delta=f"{result.totals.expected_cases - practice.totals.expected_cases:.1f} vs current practice",
                delta_color="inverse",
            )
            _tag("Health · assumption × synthetic")
        with b:
            st.metric(
                "Operating loss",
                money(result.totals.operating_loss),
                delta=f"{result.totals.operating_loss - practice.totals.operating_loss:,.0f} vs current practice",
                delta_color="inverse",
            )
            _tag("Assumption dollars. Drug cost is not inside the case cost.")
        with c:
            st.metric(
                "Antimicrobial exposure",
                num(result.totals.amu),
                delta=f"{result.totals.amu - practice.totals.amu:.1f} vs current practice",
                delta_color="inverse",
            )
            _tag("Synthetic exposure units")

        yard_rows = []
        for yard_id, use in result.by_yard.items():
            yard_rows.append(
                {
                    "Yard": yard_id,
                    "Staff": _meter(use.staff, use.staff_capacity, "h"),
                    "Pen": _meter(use.pen, use.pen_capacity, "sq ft"),
                    "Treatment": _meter(use.treatment, use.treatment_capacity, "slots"),
                }
            )
        st.dataframe(pd.DataFrame(yard_rows), hide_index=True, width="stretch")
        allocation = []
        for cohort_id in context.ranked_ids:
            metric = result.by_cohort[cohort_id]
            scored = context.scored[cohort_id]
            allocation.append(
                {
                    "Cohort": cohort_id,
                    "Action": action_label(metric.action_id),
                    "Current practice": action_label(context.practice[cohort_id]),
                    "Confidence": scored.confidence.level,
                    "Cases": num(metric.expected_cases),
                    "Loss": money(metric.operating_loss),
                    "Exposure": num(metric.amu),
                    "Vet review required": "yes" if metric.veterinary_review_required else "no",
                }
            )
        st.dataframe(pd.DataFrame(allocation), hide_index=True, width="stretch")
        st.plotly_chart(
            index_chart(result, practice),
            width="stretch",
            config={"displayModeBar": False},
            alt="Recommended cases, loss, and antimicrobial exposure indexed to current practice.",
        )
        _tag(totals_caption(result, practice))

    with st.expander("Extras — not on the 3-minute path", expanded=False):
        st.caption(
            "Two checks that the plan is not a hardcoded chart. "
            "They use the same optimizer. The storyboard does not depend on them."
        )
        st.radio(
            "Objective",
            OBJECTIVES,
            format_func=lambda key: OBJECTIVE_LABEL[key],
            key="objective",
        )
        _tag("Operating loss, modeled morbidity, and antimicrobial exposure are labeled objectives.")
        st.number_input(
            "Morbidity cost per case ($)",
            min_value=80.0,
            max_value=400.0,
            step=0.01,
            key="morbidity_cost",
            format="%.2f",
        )
        _tag("Literature constant $151.18. The $400 stress value is an assumption, not a published cost.")
        one, two = st.columns(2)
        with one:
            st.button(
                "Use $151.18",
                key="cost_default",
                on_click=_set_cost,
                args=(Assumptions().morbidity_cost_per_case,),
            )
        with two:
            st.button(
                "Stress cost at $400",
                key="cost_stress",
                on_click=_set_cost,
                args=(Assumptions().flip_morbidity_cost_per_case,),
            )
        st.caption(
            "At the literature constant, Lot 4401 stays on enhanced surveillance when TX-A has its seeded hours. "
            "At $400 per case, the same solve can select veterinary review. That action still requires a veterinarian."
        )


def page_export(context: Context, result, practice, scenario: str) -> None:
    if scenario == "shortage":
        txa = context.yards[DEMO_YARD_ID]
        note = (
            f"TX-A staff hours in this solve: {float(st.session_state.staff_txa):.1f} "
            f"(seeded {txa.staff_hours:.1f}, demo cut {txa.demo_staff_hours:.1f})."
        )
    else:
        note = "Normal mix uses relaxed capacities. The staff-cut demo is the shortage scenario."
    text = decision_summary(context, result, practice, scenario, note)
    if result.feasible:
        st.success("Decision summary ready.")
    else:
        st.error(result.message)
    st.download_button(
        "Download decision summary",
        data=text,
        file_name="brd-decision-summary.txt",
        mime="text/plain",
        type="primary",
        key="download_summary",
    )
    st.text(text)


def main() -> None:
    st.set_page_config(page_title="BRD Command Center", layout="wide")
    _inject_css()
    _init_state()
    assumptions = replace(
        Assumptions(),
        morbidity_cost_per_case=float(st.session_state.morbidity_cost),
    )
    scenario = _scenario_name()
    try:
        cohorts, yards = load_demo(scenario)
    except Exception as exc:
        st.error(f"Demo files could not be loaded. {exc}")
        st.stop()
    if not cohorts:
        st.info("No cohorts in this scenario.")
        st.stop()

    context = build_context(cohorts, yards, assumptions)
    if st.session_state.cohort_id not in context.scored:
        st.session_state.cohort_id = context.ranked_ids[0]

    staff_override = None
    seeded = None
    if scenario == "shortage":
        staff_override = {DEMO_YARD_ID: float(st.session_state.staff_txa)}
    with st.spinner("Solving the arrival-week plan…"):
        try:
            result = solve(
                context.cohorts,
                context.metrics,
                context.yards,
                objective=st.session_state.objective,
                staff_hours=staff_override,
            )
            practice_assignment = {
                cohort.cohort_id: context.practice[cohort.cohort_id] for cohort in context.cohorts
            }
            practice = evaluate_assignment(
                practice_assignment,
                context.cohorts,
                context.metrics,
                context.yards,
                staff_hours=staff_override,
                objective="operating_loss",
            )
            seed_hours = context.yards[DEMO_YARD_ID].staff_hours
            if scenario == "shortage" and abs(float(st.session_state.staff_txa) - seed_hours) > 0.05:
                seeded = solve(
                    context.cohorts,
                    context.metrics,
                    context.yards,
                    objective=st.session_state.objective,
                    staff_hours=None,
                )
        except Exception as exc:
            st.error(f"The optimizer could not run. {exc}")
            st.stop()

    st.sidebar.radio("Screen", PAGES, key="page")
    st.sidebar.radio("Scenario", ["Shortage", "Normal mix"], key="scenario_label")
    st.sidebar.caption(f"Objective: {OBJECTIVE_LABEL[st.session_state.objective]}")
    st.sidebar.caption(f"Morbidity cost assumption: ${float(st.session_state.morbidity_cost):.2f}")
    st.sidebar.caption("Synthetic demo. No login. No live weather.")

    st.title("BRD Command Center")
    st.caption("Feedlot arrival decisions for four Texas Panhandle and western Kansas yards.")
    _banner()

    page = st.session_state.page
    if page == "Overview":
        page_overview(context, result, practice)
    elif page == "Cohort":
        page_cohort(context)
    elif page == "Compare":
        page_compare(context)
    elif page == "Optimizer":
        page_optimizer(context, result, practice, scenario, seeded)
    else:
        page_export(context, result, practice, scenario)


main()
