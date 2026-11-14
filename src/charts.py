"""Plotly charts for the storyboard screens. One accent, neutrals for the rest."""

from __future__ import annotations

import plotly.graph_objects as go

from .format import money, num
from .optimizer import Evaluation
from .pipeline import Context
from .practice import action_label
from .schema import PRIORITY_COHORT_ID

ACCENT = "#B85C38"
INK = "#1B1E23"
GRAY = "#C5C8CE"
MID = "#5C6570"
FONT = "Segoe UI, Helvetica Neue, Helvetica, Arial, sans-serif"


def _finish(fig: go.Figure, title: str) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, font=dict(size=15, color=INK)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, color=INK, size=13),
        margin=dict(l=48, r=12, t=52, b=40),
        height=340,
        legend=dict(orientation="h", yanchor="top", y=-0.18),
    )
    fig.update_xaxes(showgrid=False, color=INK)
    fig.update_yaxes(gridcolor="#E2E4E8", zeroline=False)
    return fig


def burden_chart(context: Context) -> go.Figure:
    labels = []
    values = []
    colors = []
    for cohort_id in context.ranked_ids:
        cohort = next(item for item in context.cohorts if item.cohort_id == cohort_id)
        labels.append(cohort.cohort_name)
        values.append(context.metrics[cohort_id]["standard_care"].expected_cases)
        colors.append(ACCENT if cohort_id == PRIORITY_COHORT_ID else GRAY)
    fig = go.Figure(go.Bar(x=labels, y=values, marker_color=colors, hovertemplate="%{x}: %{y:.1f}<extra></extra>"))
    return _finish(fig, "Standard-care expected cases · assumption × synthetic head count")


def compare_chart(rows: list) -> go.Figure:
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
    fig = go.Figure(go.Bar(x=labels, y=values, marker_color=colors, hovertemplate="%{x}: %{y:.1f}<extra></extra>"))
    return _finish(fig, "Expected cases by action · assumption efficacy, synthetic head count")


def index_chart(recommended: Evaluation, practice: Evaluation) -> go.Figure:
    names = ["Expected cases", "Operating loss", "Antimicrobial exposure"]
    base = [
        practice.totals.expected_cases,
        practice.totals.operating_loss,
        practice.totals.amu,
    ]
    current = [
        recommended.totals.expected_cases,
        recommended.totals.operating_loss,
        recommended.totals.amu,
    ]
    indexed = [100.0 * now / was if was else 0.0 for now, was in zip(current, base)]
    fig = go.Figure(
        go.Bar(
            x=names,
            y=indexed,
            marker_color=[ACCENT, INK, MID],
            text=[f"{value:.0f}" for value in indexed],
            textposition="outside",
            hovertemplate="%{x}: %{y:.1f}<extra></extra>",
        )
    )
    fig.add_hline(y=100, line_dash="dot", line_color=GRAY)
    return _finish(fig, "Recommended plan as an index · current practice = 100")


def totals_caption(recommended: Evaluation, practice: Evaluation) -> str:
    return (
        f"Recommended {num(recommended.totals.expected_cases)} cases, "
        f"{money(recommended.totals.operating_loss)}, "
        f"{num(recommended.totals.amu)} exposure units. "
        f"Current practice {num(practice.totals.expected_cases)} cases, "
        f"{money(practice.totals.operating_loss)}, "
        f"{num(practice.totals.amu)} units."
    )
