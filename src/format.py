"""Display helpers shared by the export and the app."""

from __future__ import annotations

from src.schema import FIELD_LABEL


def money(value: float) -> str:
    return f"${value:,.0f}"


def num(value: float, digits: int = 1) -> str:
    return f"{value:,.{digits}f}"


def pct(value: float) -> str:
    return f"{100 * value:.1f}%"


def field_labels(keys: tuple[str, ...] | list[str]) -> str:
    """Comma-separated human labels for schema field keys (demo refusal copy)."""
    return ", ".join(FIELD_LABEL.get(key, key.replace("_", " ")) for key in keys)