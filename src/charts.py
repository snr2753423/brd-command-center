"""Plotly charts for the storyboard screens. Oxidized copper accent; neutrals elsewhere."""

from __future__ import annotations

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .format import money, num
from .optimizer import Evaluation, YardUse
from .pipeline import Context
from .practice import action_label
from .risk_model import Scored
from .schema import PRIORITY_COHORT_ID

ACCENT = "#B85C38"
INK = "#1B1E23"
GRAY = "#C5C8CE"
MID = "#5C6570"
LINE = "#E2E4E8"
TEAL = "#2F6F6A"
STEEL = "#3D5A73"
FONT = "Segoe UI, Helvetica Neue, Helvetica, Arial, sans-serif"


def _finish(fig: go.Figure, title: str, *, height: int = 360) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, font=dict(size=15, color=INK, family=FONT), x=0, xanchor="left"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, color=INK, size=13),
        margin=dict(l=52, r=18, t=56, b=48),
        height=height,
        legend=dict(orientation="h", yanchor="top", y=-0.18, font=dict(size=12)),
        bargap=0.28,
        hoverlabel=dict(bgcolor="#FFFFFF", font_size=12, font_family=FONT, bordercolor=LINE),
    )
    fig.update_xaxes(showgrid=False, color=INK, linecolor=LINE, tickfont=dict(size=12))
    fig.update_yaxes(gridcolor=LINE, zeroline=False, color=INK, tickfont=dict(size=12))
    return fig


def burden_chart(context: Context) -> go.Figure:
    """Standard-care expected cases by cohort; Lot 4401 highlighted."""
    labels = []
    values = []
    colors = []
    custom = []
    for cohort_id in context.ranked_ids:
        cohort = next(item for item in context.cohorts if item.cohort_id == cohort_id)
        cases = context.metrics[cohort_id]["standard_care"].expected_cases
        scored = context.scored[cohort_id]
        labels.append(cohort.cohort_name)
        values.append(cases)
        colors.append(ACCENT if cohort_id == PRIORITY_COHORT_ID else GRAY)
        custom.append(
            f"{cohort.cohort_id}<br>Planning {100 * scored.planning_morbidity:.1f}% · {scored.confidence.level}"
        )
    fig = go.Figure(
        go.Bar(
            x=labels,
            y=values,
            marker=dict(color=colors, line=dict(width=0)),
            text=[f"{v:.1f}" for v in values],
            textposition="outside",
            cliponaxis=False,
            customdata=custom,
            hovertemplate="<b>%{x}</b><br>Expected cases: %{y:.1f}<br>%{customdata}<extra></extra>",
        )
    )
    fig.update_yaxes(title_text="Expected cases", rangemode="tozero")
    return _finish(fig, "Standard-care expected cases · assumption × synthetic head count", height=380)


def compare_chart(rows: list) -> go.Figure:
    """Expected cases by action; current practice marked."""
    labels = []
    values = []
    colors = []
    for row in rows:
        name = action_label(row.action_id)
        if row.is_current_practice:
            name = f"{name} (current practice)"
        labels.append(name)
        values.append(row.metric.expected_cases)
        colors.append(ACCENT if row.is_current_practice else GRAY)
    fig = go.Figure(
        go.Bar(
            x=labels,
            y=values,
            marker_color=colors,
            text=[f"{v:.1f}" for v in values],
            textposition="outside",
            cliponaxis=False,
            hovertemplate="<b>%{x}</b><br>Expected cases: %{y:.1f}<extra></extra>",
        )
    )
    fig.update_yaxes(title_text="Expected cases", rangemode="tozero")
    return _finish(fig, "Expected cases by action · assumption efficacy, synthetic head count", height=380)


def compare_delta_chart(rows: list) -> go.Figure:
    """Δ cases, deaths, loss, and exposure vs current practice (alternatives only)."""
    alternatives = [row for row in rows if not row.is_current_practice]
    if not alternatives:
        fig = go.Figure()
        return _finish(fig, "Δ vs current practice · no alternatives")

    labels = [action_label(row.action_id) for row in alternatives]
    metrics = [
        ("Δ cases", [row.delta_cases for row in alternatives], STEEL),
        ("Δ deaths", [row.delta_deaths for row in alternatives], MID),
        ("Δ loss ($)", [row.delta_loss for row in alternatives], ACCENT),
        ("Δ exposure", [row.delta_amu for row in alternatives], TEAL),
    ]
    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=[title for title, _, _ in metrics],
        vertical_spacing=0.16,
        horizontal_spacing=0.10,
    )
    for index, (_, values, color) in enumerate(metrics):
        row_i = 1 + index // 2
        col_i = 1 + index % 2
        fig.add_trace(
            go.Bar(
                x=labels,
                y=values,
                marker_color=color,
                hovertemplate="%{x}: %{y:.1f}<extra></extra>",
                showlegend=False,
            ),
            row=row_i,
            col=col_i,
        )
        fig.add_hline(y=0, line_dash="dot", line_color=GRAY, row=row_i, col=col_i)
    fig.update_annotations(font=dict(size=12, color=INK))
    return _finish(
        fig,
        "Δ vs current practice · negative is better for cases, deaths, loss, and exposure",
        height=440,
    )


def index_chart(recommended: Evaluation, practice: Evaluation) -> go.Figure:
    """Before/after: current practice vs recommended plan on four totals."""
    names = ["Expected cases", "Operating loss", "Antimicrobial exposure", "Expected BRD deaths"]
    practice_vals = [
        practice.totals.expected_cases,
        practice.totals.operating_loss,
        practice.totals.amu,
        practice.totals.expected_deaths,
    ]
    plan_vals = [
        recommended.totals.expected_cases,
        recommended.totals.operating_loss,
        recommended.totals.amu,
        recommended.totals.expected_deaths,
    ]
    # Dual display: absolute grouped bars + index annotation via hover.
    practice_text = [
        num(practice.totals.expected_cases),
        money(practice.totals.operating_loss),
        num(practice.totals.amu),
        num(practice.totals.expected_deaths),
    ]
    plan_text = [
        num(recommended.totals.expected_cases),
        money(recommended.totals.operating_loss),
        num(recommended.totals.amu),
        num(recommended.totals.expected_deaths),
    ]
    indexed = [100.0 * now / was if was else 0.0 for now, was in zip(plan_vals, practice_vals)]
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            name="Current practice",
            x=names,
            y=[100.0] * len(names),
            marker_color=GRAY,
            customdata=practice_text,
            hovertemplate="<b>%{x}</b><br>Current practice: %{customdata} (index 100)<extra></extra>",
        )
    )
    fig.add_trace(
        go.Bar(
            name="Recommended plan",
            x=names,
            y=indexed,
            marker_color=[ACCENT, INK, TEAL, STEEL],
            text=[f"{value:.0f}" for value in indexed],
            textposition="outside",
            cliponaxis=False,
            customdata=list(zip(plan_text, indexed)),
            hovertemplate="<b>%{x}</b><br>Recommended: %{customdata[0]} (index %{customdata[1]:.0f})<extra></extra>",
        )
    )
    fig.add_hline(y=100, line_dash="dot", line_color=MID, annotation_text="100 = current practice", annotation_position="top right")
    fig.update_layout(barmode="group")
    fig.update_yaxes(title_text="Index (current practice = 100)", rangemode="tozero")
    return _finish(fig, "Recommended plan vs current practice · index view", height=400)


def calibration_chart(fit, context: Context) -> go.Figure:
    """Synthetic-population morbidity against the 15% line, with this file's cohorts marked."""
    fig = go.Figure()
    fig.add_trace(
        go.Histogram(
            x=fit.realized * 100,
            xbins=dict(start=0, end=60, size=1.5),
            marker=dict(color=GRAY, line=dict(width=0)),
            name="Synthetic cohorts, simulated 45-day morbidity",
            hovertemplate="%{x}%: %{y} cohorts<extra></extra>",
        )
    )
    xs, labels, colors = [], [], []
    for cohort_id in context.ranked_ids:
        cohort = next(item for item in context.cohorts if item.cohort_id == cohort_id)
        xs.append(context.scored[cohort_id].planning_morbidity * 100)
        labels.append(cohort.cohort_name)
        colors.append(ACCENT if cohort_id == PRIORITY_COHORT_ID else STEEL)
    fig.add_trace(
        go.Scatter(
            x=xs,
            y=[0] * len(xs),
            mode="markers+text",
            marker=dict(color=colors, size=12, symbol="triangle-up", line=dict(width=0)),
            name="This file's cohorts, planning morbidity",
            text=labels,
            textposition="top center",
            textfont=dict(size=10, color=INK),
            hovertemplate="%{text}: %{x:.1f}%<extra></extra>",
        )
    )
    fig.add_vline(x=15, line_dash="dot", line_color=INK, annotation_text="15% (Rojas)", annotation_position="top")
    fig.update_xaxes(title_text="45-day BRD morbidity (%)", range=[0, 60])
    fig.update_yaxes(title_text="Cohorts")
    fig = _finish(fig, "Synthetic population calibrated to Rojas et al. 2022", height=420)
    fig.update_layout(margin=dict(b=120), legend=dict(y=-0.28))
    return fig


def drivers_chart(scored: Scored) -> go.Figure:
    """Horizontal log-odds contributions for known drivers (unknowns omitted)."""
    known = [
        driver
        for driver in scored.drivers
        if driver.contribution is not None and abs(driver.contribution) > 1e-12
    ]
    known.sort(key=lambda driver: abs(driver.contribution or 0.0))
    if not known:
        fig = go.Figure()
        fig.add_annotation(
            text="No scored log-odds drivers to plot for this record.",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(color=MID, size=13),
        )
        return _finish(fig, "Risk drivers · log-odds contribution (assumption coefficients)", height=280)

    labels = [f"{driver.label} ({driver.domain})" for driver in known]
    values = [driver.contribution or 0.0 for driver in known]
    colors = [ACCENT if value > 0 else TEAL for value in values]
    fig = go.Figure(
        go.Bar(
            y=labels,
            x=values,
            orientation="h",
            marker_color=colors,
            text=[f"{value:+.3f}" for value in values],
            textposition="outside",
            cliponaxis=False,
            hovertemplate="<b>%{y}</b><br>Log-odds: %{x:+.3f}<extra></extra>",
        )
    )
    fig.add_vline(x=0, line_color=LINE)
    fig.update_xaxes(title_text="Log-odds contribution", zeroline=False)
    height = max(300, 48 + 28 * len(known))
    return _finish(fig, "Risk drivers · log-odds contribution (assumption coefficients)", height=height)


def uncertainty_chart(scored: Scored) -> go.Figure:
    """Planning morbidity with known-fields 90% band and optional unknown-state range."""
    planning = 100 * scored.planning_morbidity
    low = 100 * scored.interval_low
    high = 100 * scored.interval_high
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=[planning],
            y=["Planning figure"],
            mode="markers",
            marker=dict(size=14, color=ACCENT, symbol="diamond"),
            error_x=dict(
                type="data",
                symmetric=False,
                array=[high - planning],
                arrayminus=[planning - low],
                color=MID,
                thickness=2,
                width=8,
            ),
            name="Planning ± ~90% band on known-fields logit",
            hovertemplate=(
                f"Planning {planning:.1f}%<br>"
                f"~90% band {low:.1f}%–{high:.1f}%<extra></extra>"
            ),
            showlegend=True,
        )
    )
    if scored.confidence.missing_fields:
        state_low = 100 * scored.state_low
        state_high = 100 * scored.state_high
        fig.add_trace(
            go.Scatter(
                x=[state_low, state_high],
                y=["Unknown-state range", "Unknown-state range"],
                mode="lines+markers",
                line=dict(color=STEEL, width=3),
                marker=dict(size=9, color=STEEL, symbol="line-ns-open"),
                name="Range across unknown states",
                hovertemplate="Unknown-state bound: %{x:.1f}%<extra></extra>",
            )
        )
    fig.add_vline(x=15, line_dash="dot", line_color=INK, annotation_text="15% (Rojas)", annotation_position="top")
    if not scored.confident_call:
        fig.add_annotation(
            text="Confident call withheld",
            xref="paper",
            yref="paper",
            x=0.98,
            y=0.05,
            xanchor="right",
            showarrow=False,
            font=dict(color=ACCENT, size=12),
        )
    fig.update_xaxes(title_text="45-day BRD morbidity (%)", range=[0, max(60, high + 5, planning + 5)])
    fig.update_yaxes(title_text="")
    return _finish(fig, "Morbidity uncertainty · assumption band; 15% line is published", height=300)


def yard_limits_chart(by_yard: dict[str, YardUse]) -> go.Figure:
    """Staff / pen / treatment utilization (%) by yard under the recommended plan."""
    if not by_yard:
        fig = go.Figure()
        return _finish(fig, "Yard limit use · no feasible plan")

    yards = list(by_yard.keys())
    staff = [100 * by_yard[y].staff_ratio for y in yards]
    pen = [100 * by_yard[y].pen_ratio for y in yards]
    treatment = [100 * by_yard[y].treatment_ratio for y in yards]
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            name="Staff",
            x=yards,
            y=staff,
            marker_color=ACCENT,
            hovertemplate="%{x} staff: %{y:.0f}% used<extra></extra>",
        )
    )
    fig.add_trace(
        go.Bar(
            name="Pen",
            x=yards,
            y=pen,
            marker_color=STEEL,
            hovertemplate="%{x} pen: %{y:.0f}% used<extra></extra>",
        )
    )
    fig.add_trace(
        go.Bar(
            name="Treatment",
            x=yards,
            y=treatment,
            marker_color=TEAL,
            hovertemplate="%{x} treatment: %{y:.0f}% used<extra></extra>",
        )
    )
    fig.add_hline(y=100, line_dash="dot", line_color=INK, annotation_text="At cap", annotation_position="top left")
    fig.update_layout(barmode="group")
    fig.update_yaxes(title_text="% of arrival-week limit used", range=[0, 115])
    return _finish(fig, "Yard limits under the recommended plan · synthetic capacities", height=380)


def totals_caption(recommended: Evaluation, practice: Evaluation) -> str:
    return (
        f"Recommended {num(recommended.totals.expected_cases)} cases, "
        f"{money(recommended.totals.operating_loss)}, "
        f"{num(recommended.totals.amu)} exposure units. "
        f"Current practice {num(practice.totals.expected_cases)} cases, "
        f"{money(practice.totals.operating_loss)}, "
        f"{num(practice.totals.amu)} units."
    )
