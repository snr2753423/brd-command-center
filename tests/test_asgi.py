from __future__ import annotations

from starlette.applications import Starlette
from starlette.testclient import TestClient

from app import app, render_page, render_summary


def test_app_exports_an_asgi_entry_for_the_shortage_path():
    assert isinstance(app, Starlette)
    page = render_page()
    summary = render_summary()
    assert "BRD Command Center" in page
    assert "Shortage scenario" in page
    assert "Demo path beats" in page
    assert "changed Lot 4401 from Enhanced surveillance to Standard care" in page
    assert "No confident recommendation" in page
    assert "TXB-4388" in page
    assert "16.7%" in page
    assert "103.5" in page and "109.4" in page
    assert "Planning figure (worst case" in page
    assert "18.6%" in page
    assert "SYNTHETIC DATA" in summary
    assert "TXA-4401" in summary
    assert "TXB-4388" in summary
    assert "No confident recommendation" in summary
    assert "Not a prescription" in summary


def test_asgi_routes_via_test_client():
    client = TestClient(app)

    home = client.get("/")
    assert home.status_code == 200
    assert "text/html" in home.headers["content-type"]
    body = home.text
    assert "BRD Command Center" in body
    assert "Shortage scenario" in body
    assert "changed Lot 4401 from Enhanced surveillance to Standard care" in body
    assert "No confident recommendation" in body
    assert "16.7%" in body
    assert "54.5%" in body
    assert "103.5" in body and "109.4" in body
    assert "15,954" in body and "16,545" in body

    summary = client.get("/summary")
    assert summary.status_code == 200
    assert "text/plain" in summary.headers["content-type"]
    assert "SYNTHETIC DATA" in summary.text
    assert "TX-A staff hours in this solve: 90.0" in summary.text
    assert "TXA-4401" in summary.text
    assert "TXB-4388" in summary.text
    assert "Expected cases: 109.4" in summary.text

    health = client.get("/health")
    assert health.status_code == 200
    assert health.text.strip() == "ok"

    ready = client.get("/ready")
    assert ready.status_code == 200
    assert ready.text.strip() == "ready"


def test_asgi_routes_fail_gracefully_when_scenario_breaks(monkeypatch):
    client = TestClient(app)

    def boom():
        raise RuntimeError("demo data missing")

    monkeypatch.setattr("app._scenario", boom)

    home = client.get("/")
    assert home.status_code == 503
    assert "Shortage demo unavailable" in home.text
    assert "/ready" in home.text

    summary = client.get("/summary")
    assert summary.status_code == 503
    assert "summary unavailable" in summary.text

    # Liveness stays up even when the scenario cannot build.
    assert client.get("/health").status_code == 200
    assert client.get("/health").text.strip() == "ok"

    ready = client.get("/ready")
    assert ready.status_code == 503
    assert "not ready" in ready.text
