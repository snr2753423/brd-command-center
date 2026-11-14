"""Display helpers shared by the export and the app."""

from __future__ import annotations


def money(value: float) -> str:
    return f"${value:,.0f}"


def num(value: float, digits: int = 1) -> str:
    return f"{value:,.{digits}f}"


def pct(value: float) -> str:
    return f"{100 * value:.1f}%"
