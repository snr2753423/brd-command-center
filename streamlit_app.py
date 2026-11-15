"""BRD Command Center. Local Streamlit app. No accounts, no paid APIs."""

from __future__ import annotations

import math
from dataclasses import replace

import pandas as pd
import streamlit as st

from src.assumptions import UNKNOWN_PLANNING_LABEL, Assumptions, case_fatality
from src.charts import burden_chart, compare_chart, index_chart, totals_caption
from src.data_loader import load_demo
from src.economics import compare_to_practice
from src.format import money, num, pct
from src.optimizer import CAPACITY_FIELDS, evaluate_assignment, solve
from src.pipeline import Context, build_context
from src.practice import action_label, rule_text
from src.reporting import decision_summary
from src.risk_model import domain_summary, why_line
from src.schema import (
    ACTION_LABEL,
    DEMO_YARD_ID,
    OBJECTIVE_LABEL,
    OBJECTIVES,
    PRIORITY_COHORT_ID,
    Cohort,
    Yard,
)
from src.validation import validate_cohort_frame

PAGES = ["Overview", "Cohort", "Compare", "Optimizer", "Export"]
FONT = '"Segoe UI", "Helvetica Neue", Helvetica, Arial, sans-serif'


def _go(page: str, cohort_id: str | None = None) -> None:
    st.session_state.page = page
    if cohort_id is not None:
        st.session_state.cohort_id = cohort_id


# Label and slider step for each hard limit a manager can move.
CAP_SPEC: dict[str, tuple[str, float]] = {
    "staff_hours": ("Staff h", 0.25),
    "pen_capacity_sqft": ("Pen sq ft", 250.0),
    "treatment_slots": ("Treatment slots", 0.1),
}


def _cap_key(scenario: str, yard_id: str, field: str) -> str:
    return f"cap_{scenario}_{yard_id}_{field}"


def _seed_value(yard: Yard, field: str) -> float:
    """File value rounded up to the slider step, so the seeded limit is never tightened."""
    step = CAP_SPEC[field][1]
    return round(math.ceil(float(getattr(yard, field)) / step - 1e-9) * step, 4)


def _init_caps(scenario: str, yards: list[Yard]) -> None:
    for yard in yards:
        for field in CAPACITY_FIELDS:
            st.session_state.setdefault(_cap_key(scenario, yard.yard_id, field), _seed_value(yard, field))


def _capacity_overrides(scenario: str, yards: list[Yard]) -> dict[str, dict[str, float]]:
    """Only limits the manager moved. Untouched limits keep the exact file value."""
    overrides: dict[str, dict[str, float]] = {}
    for yard in yards:
        for field in CAPACITY_FIELDS:
            value = float(st.session_state[_cap_key(scenario, yard.yard_id, field)])
            if abs(value - _seed_value(yard, field)) > 1e-9:
                overrides.setdefault(yard.yard_id, {})[field] = value
    return overrides


def _set_cap(key: str, value: float) -> None:
    st.session_state[key] = float(value)


def _sync(widget_key: str, key: str) -> None:
    st.session_state[key] = st.session_state[widget_key]


def _restore_caps(scenario: str, yards: list[Yard]) -> None:
    for yard in yards:
        for field in CAPACITY_FIELDS:
            st.session_state[_cap_key(scenario, yard.yard_id, field)] = _seed_value(yard, field)


def _use_upload(cohorts: list[Cohort], mode: str) -> None:
    st.session_state.uploaded_cohorts = list(cohorts)
    st.session_state.upload_mode = mode


def _clear_upload() -> None:
    st.session_state.uploaded_cohorts = []


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
        The 15% line and the $151.18, $23.60, and 50% metaphylaxis constants are published (Rojas et al. 2022).
        Other effect sizes and the risk coefficients are assumptions, not validated accuracy.
        Medication actions are not prescriptions.
        </div>
        """,
        unsafe_allow_html=True,
    )


def _cohort(context: Context, cohort_id: str):
    return next(item for item in context.cohorts if item.cohort_id == cohort_id)


def _init_state() -> None:
    st.session_state.setdefault("page", "Overview")
    st.session_state.setdefault("cohort_id", PRIORITY_COHORT_ID)
    st.session_state.setdefault("scenario_label", "Shortage")
    st.session_state.setdefault("objective", "operating_loss")
    st.session_state.setdefault("morbidity_cost", Assumptions().morbidity_cost_per_case)
    st.session_state.setdefault("unknown_planning", Assumptions().unknown_planning)
    st.session_state.setdefault("uploaded_cohorts", [])
    st.session_state.setdefault("upload_mode", "add")


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
        "Morbidity is an assumption-based 45-day estimate. Cohorts with unknown fields are planned on "
        "their unknown-state range (worst case by default), not on a typical value. "
        "P(above 15%) is a different number. The 15% benchmark is published."
    )
    rows = []
    for rank, cohort_id in enumerate(context.ranked_ids, start=1):
        cohort = _cohort(context, cohort_id)
        scored = context.scored[cohort_id]
        morbidity = "Withheld" if not scored.confident_call else pct(scored.planning_morbidity)
        planning = pct(scored.planning_morbidity)
        if scored.planning_basis != "complete":
            planning += f" ({scored.planning_basis.replace('_', ' ')})"
        rows.append(
            {
                "Rank": rank,
                "Cohort": f"{cohort.cohort_name} ({cohort.cohort_id})",
                "Yard": cohort.yard_id,
                "Head": cohort.head_count,
                "Weight lb": f"{cohort.arrival_weight_lb:.0f}",
                "Sources": cohort.source_count,
                "45-day morbidity": morbidity,
                "Planning figure": planning,
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

    top_id = context.ranked_ids[0]
    top_cohort = _cohort(context, top_id)
    st.markdown(f"**Why {top_cohort.cohort_name} ranks first.** {why_line(context.scored[top_id])}")
    _tag("Driver coefficients are assumptions. Head count is synthetic and only scales the cases.")
    incomplete = [cid for cid in context.ranked_ids if not context.scored[cid].confident_call]
    left, right = st.columns(2)
    with left:
        st.button(
            f"Open {top_cohort.cohort_name}",
            type="primary",
            on_click=_go,
            args=("Cohort", top_id),
            key="open_priority",
        )
    with right:
        if incomplete:
            st.button(
                "Open the incomplete record",
                on_click=_go,
                args=("Cohort", incomplete[0]),
                key="open_incomplete",
            )

    if practice.violations:
        st.warning("Current practice is not feasible under these limits. " + " ".join(practice.violations))
    elif result.feasible:
        st.success("Current practice fits these limits, and a feasible allocation is ready on the Optimizer screen.")

    st.subheader("Upload cohorts")
    _tag(
        "Rows are checked first. Accepted rows can be added to the plan or replace the seeded cohorts; "
        "the optimizer then re-solves with them against the same yard limits."
    )
    active = st.session_state.uploaded_cohorts
    if active:
        how = "replacing the seeded cohorts" if st.session_state.upload_mode == "replace" else "added to the seeded cohorts"
        st.info(f"The plan includes {len(active)} uploaded cohort(s), {how}.")
        st.button("Remove uploaded cohorts from the plan", on_click=_clear_upload, key="clear_upload")
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
                    "45-day morbidity": "Withheld" if not scored.confident_call else pct(scored.planning_morbidity),
                    "Planning figure": pct(scored.planning_morbidity),
                    "Current practice": action_label(preview.practice[cohort.cohort_id]),
                }
            )
        st.dataframe(pd.DataFrame(scored_rows), hide_index=True, width="stretch")
        accepted = list(checked.accepted)
        one, two = st.columns(2)
        with one:
            st.button(
                "Add accepted rows to the plan",
                type="primary",
                on_click=_use_upload,
                args=(accepted, "add"),
                key="upload_add",
            )
        with two:
            st.button(
                "Replace seeded cohorts with these rows",
                on_click=_use_upload,
                args=(accepted, "replace"),
                key="upload_replace",
            )
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
            f"The plan uses {UNKNOWN_PLANNING_LABEL[scored.planning_basis].lower()}: "
            f"{pct(scored.planning_morbidity)}. A veterinarian or manager should confirm the history."
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
        shown = "Withheld" if not scored.confident_call else pct(scored.planning_morbidity)
        st.metric("45-day morbidity", shown)
        _tag(
            f"Planning figure {pct(scored.planning_morbidity)}. Assumption coefficients. "
            "Not the same number as P(above 15%)."
        )
    with right:
        st.metric("P(morbidity ≥ 15%)", pct(scored.p_high_risk))
        _tag("Published 15% benchmark. The probability uses an assumption-based uncertainty band.")

    if scored.confidence.missing_fields:
        st.caption(
            f"Range across unknown states: {pct(scored.state_low)}–{pct(scored.state_high)}. "
            "Those bounds are assumptions, not filled-in values. "
            f"Reference-profile figure (unknowns at reference values): {pct(scored.morbidity)}. "
            f"Planned at: {UNKNOWN_PLANNING_LABEL[scored.planning_basis].lower()}."
        )
    st.caption(
        f"About 90% band on the known-fields logit: {pct(scored.interval_low)}–{pct(scored.interval_high)} · assumption."
    )
    cfr = case_fatality(cohort.arrival_weight_lb, context.assumptions)
    st.caption(
        f"BRD deaths per case: {pct(cfr)} for this weight class · derived from published rates "
        "(USDA 2019 death rates, BRD share of deaths, Rojas 2022 mean morbidity). Deaths follow cases."
    )
    if scored.confident_call and scored.above_benchmark:
        st.caption("The planning estimate is at or above the published 15% benchmark.")
    elif not scored.confident_call:
        st.caption("Do not treat the planning figure as a call against the 15% benchmark.")

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
                "Deaths": num(metric.expected_deaths),
                "Δ deaths": num(row.delta_deaths),
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
        "Loss: $151.18 per case (published, Rojas 2022 Table 3) plus the action's own program cost. "
        "Metaphylaxis is $23.60 per at-risk head (published, same table) and is not inside the case cost. "
        "Exposure units are synthetic. Staff, pen, and treatment rates are assumptions. "
        "Deaths are derived from published rates and are not priced, because the $151.18 already "
        "covers the lost value of a sick animal."
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
    _tag(
        "Every yard's arrival-week limits are live. Move any slider and the plan re-solves. "
        "Seeded values come from the synthetic yard file."
    )
    yards = list(context.yards.values())
    one, two = st.columns(2)
    if scenario == "shortage":
        txa = context.yards[DEMO_YARD_ID]
        with one:
            st.button(
                "Apply demo staff cut",
                type="primary",
                key="demo_cut",
                on_click=_set_cap,
                args=(_cap_key(scenario, DEMO_YARD_ID, "staff_hours"), float(txa.demo_staff_hours)),
            )
        _tag(
            f"Demo cut sets TX-A staff to {txa.demo_staff_hours:.0f} h, the standard-care floor. "
            "Below a yard's floor, the plan is refused."
        )
    with two:
        st.button("Restore seeded limits", key="restore_caps", on_click=_restore_caps, args=(scenario, yards))
    columns = st.columns(len(yards))
    for column, yard in zip(columns, yards):
        with column:
            st.markdown(f"**{yard.yard_id}** · {yard.yard_name}")
            for field in CAPACITY_FIELDS:
                label, step = CAP_SPEC[field]
                key = _cap_key(scenario, yard.yard_id, field)
                widget = f"w_{key}"
                seed = _seed_value(yard, field)
                st.session_state[widget] = float(st.session_state[key])
                st.slider(
                    f"{yard.yard_id} {label}",
                    min_value=0.0,
                    max_value=float(max(seed * 2, step * 10)),
                    step=step,
                    key=widget,
                    on_change=_sync,
                    args=(widget, key),
                    help=f"Seeded {seed:,.2f}. Synthetic arrival-week limit.",
                )

    if not result.feasible:
        st.error(result.message)
    else:
        focus = context.ranked_ids[0]
        names = {cohort.cohort_id: cohort.cohort_name for cohort in context.cohorts}
        action = result.assignment.get(focus, "")
        moved = []
        if seeded is not None and seeded.feasible:
            moved = [
                cid
                for cid in context.ranked_ids
                if seeded.assignment.get(cid) != result.assignment.get(cid)
            ]
        if moved:
            changes = "; ".join(
                f"{names[cid]} from {action_label(seeded.assignment[cid])} to {action_label(result.assignment[cid])}"
                for cid in moved
            )
            st.success(
                f"Yard limits changed {changes}. "
                "Cases, operating loss, and antimicrobial exposure updated from this solve."
            )
        else:
            st.success(
                f"Feasible plan. {names[focus]} is on {action_label(action)}. "
                "Staff, pen, and treatment are within their limits."
            )

    if practice.violations:
        st.warning("Named current practice breaks a limit. " + " ".join(practice.violations))

    if result.feasible:
        a, b, c, d = st.columns(4)
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
        with d:
            st.metric(
                "Expected BRD deaths",
                num(result.totals.expected_deaths),
                delta=f"{result.totals.expected_deaths - practice.totals.expected_deaths:.1f} vs current practice",
                delta_color="inverse",
            )
            _tag("Derived from published rates · follows cases")

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
                    "Deaths": num(metric.expected_deaths),
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
        _tag("Operating loss, modeled morbidity, antimicrobial exposure, and expected BRD deaths are labeled objectives.")
        st.number_input(
            "Morbidity cost per case ($)",
            min_value=80.0,
            max_value=400.0,
            step=0.01,
            key="morbidity_cost",
            format="%.2f",
        )
        _tag("Published $151.18 (Rojas 2022 Table 3). The $400 stress value is an assumption, not a published cost.")
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
            "At the published constant, Lot 4401 stays on enhanced surveillance when TX-A has its seeded hours. "
            "At $400 per case, the same solve can select veterinary review. That action still requires a veterinarian."
        )


def page_export(context: Context, result, practice, scenario: str, overrides) -> None:
    if overrides:
        parts = []
        for yard_id, fields in overrides.items():
            yard = context.yards[yard_id]
            for field, value in fields.items():
                parts.append(f"{yard_id} {CAP_SPEC[field][0]} {value:,.2f} (seeded {getattr(yard, field):,.2f})")
        note = "Manager-set limits in this solve: " + "; ".join(parts) + "."
    else:
        note = f"Seeded {scenario} yard limits from the synthetic file."
    uploaded = st.session_state.uploaded_cohorts
    if uploaded:
        note += f" Plan includes {len(uploaded)} uploaded cohort(s) ({st.session_state.upload_mode})."
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
        unknown_planning=str(st.session_state.unknown_planning),
    )
    scenario = _scenario_name()
    try:
        cohorts, yards = load_demo(scenario)
    except Exception as exc:
        st.error(f"Demo files could not be loaded. {exc}")
        st.stop()
    uploaded = list(st.session_state.uploaded_cohorts)
    skipped = 0
    if uploaded:
        if st.session_state.upload_mode == "replace":
            cohorts = uploaded
        else:
            seen = {cohort.cohort_id for cohort in cohorts}
            extra = [cohort for cohort in uploaded if cohort.cohort_id not in seen]
            skipped = len(uploaded) - len(extra)
            cohorts = cohorts + extra
    if not cohorts:
        st.info("No cohorts in this scenario.")
        st.stop()
    _init_caps(scenario, yards)
    overrides = _capacity_overrides(scenario, yards)

    context = build_context(cohorts, yards, assumptions)
    if st.session_state.cohort_id not in context.scored:
        st.session_state.cohort_id = context.ranked_ids[0]

    seeded = None
    with st.spinner("Solving the arrival-week plan…"):
        try:
            result = solve(
                context.cohorts,
                context.metrics,
                context.yards,
                objective=st.session_state.objective,
                capacities=overrides,
            )
            practice_assignment = {
                cohort.cohort_id: context.practice[cohort.cohort_id] for cohort in context.cohorts
            }
            practice = evaluate_assignment(
                practice_assignment,
                context.cohorts,
                context.metrics,
                context.yards,
                objective="operating_loss",
                capacities=overrides,
            )
            if overrides:
                seeded = solve(
                    context.cohorts,
                    context.metrics,
                    context.yards,
                    objective=st.session_state.objective,
                )
        except Exception as exc:
            st.error(f"The optimizer could not run. {exc}")
            st.stop()

    st.sidebar.radio("Screen", PAGES, key="page")
    st.sidebar.radio("Scenario", ["Shortage", "Normal mix"], key="scenario_label")
    st.sidebar.radio(
        "Plan cohorts with unknown fields at",
        list(UNKNOWN_PLANNING_LABEL),
        format_func=lambda key: UNKNOWN_PLANNING_LABEL[key],
        key="unknown_planning",
        help="Leaving an unknown field out of the score equals giving it the reference value. "
        "Worst case is the cautious default.",
    )
    st.sidebar.caption(f"Objective: {OBJECTIVE_LABEL[st.session_state.objective]}")
    st.sidebar.caption(f"Morbidity cost assumption: ${float(st.session_state.morbidity_cost):.2f}")
    if uploaded:
        st.sidebar.caption(f"Uploaded cohorts in plan: {len(uploaded) - skipped}")
    if skipped:
        st.sidebar.caption(f"{skipped} uploaded row(s) skipped: cohort_id already in the seeded file.")
    if overrides:
        st.sidebar.caption("Yard limits: manager-set")
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
        page_export(context, result, practice, scenario, overrides)


main()
