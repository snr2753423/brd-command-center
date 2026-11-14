from __future__ import annotations

from starlette.applications import Starlette

from app import app, render_page, render_summary


def test_app_exports_an_asgi_entry_for_the_shortage_path():
    assert isinstance(app, Starlette)
    page = render_page()
    summary = render_summary()
    assert "BRD Command Center" in page
    assert "Shortage scenario" in page
    assert "changed Lot 4401 from Enhanced surveillance to Standard care" in page
    assert "No confident recommendation" in page
    assert "TXB-4388" in page
    assert "SYNTHETIC DATA" in summary
    assert "TXA-4401" in summary
    assert "TXB-4388" in summary
    assert "No confident recommendation" in summary
    assert "Not a prescription" in summary
