from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


def _app() -> AppTest:
    app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=60)
    app.run()
    assert not app.exception
    return app


def _values(elements) -> str:
    return "\n".join(getattr(item, "value", "") for item in elements)


def test_storyboard_staff_cut_and_withheld_call():
    app = _app()
    assert "BRD Command Center" in _values(app.title)
    assert "Synthetic data" in _values(app.markdown)
    assert any("No CSV uploaded." in item.value for item in app.info)
    assert any("TX-B staff" in item.value for item in app.warning)

    app.sidebar.radio[0].set_value("Optimizer").run()
    assert not app.exception
    assert any("Enhanced surveillance" in item.value for item in app.success)

    next(button for button in app.button if button.key == "demo_cut").click().run()
    assert not app.exception
    joined = _values(app.success)
    assert "Standard care" in joined
    assert "changed Lot 4401" in joined

    app.sidebar.radio[0].set_value("Cohort").run()
    app.selectbox[0].set_value("TXB-4388").run()
    assert not app.exception
    assert any("No confident recommendation" in item.value for item in app.error)

    app.sidebar.radio[0].set_value("Export").run()
    assert any("Decision summary ready." in item.value for item in app.success)
    preview = _values(app.text)
    assert "SYNTHETIC DATA" in preview
    assert "TXB-4388" in preview
    assert len(app.download_button) == 1


def test_bad_csv_is_rejected_in_the_app():
    app = _app()
    payload = (ROOT / "data" / "upload_bad_rows.csv").read_bytes()
    app.file_uploader[0].upload("upload_bad_rows.csv", payload, "text/csv").run()
    assert not app.exception
    assert any("accepted" in item.value for item in app.success)
    tables = "\n".join(frame.value.astype(str).to_string() for frame in app.dataframe)
    assert "duplicated" in tables
    assert "BAD-HEAD" in tables or "head_count" in tables

    missing = (ROOT / "data" / "upload_missing_column.csv").read_bytes()
    app.file_uploader[0].upload("upload_missing_column.csv", missing, "text/csv").run()
    assert any("head_count" in item.value for item in app.error)


def test_cost_stress_flips_the_action_and_low_staff_is_refused():
    app = _app()
    app.sidebar.radio[0].set_value("Optimizer").run()
    next(button for button in app.button if button.key == "cost_stress").click().run()
    assert not app.exception
    assert any("Veterinary review" in item.value for item in app.success)

    next(button for button in app.button if button.key == "cost_default").click().run()
    assert any("Enhanced surveillance" in item.value for item in app.success)

    app.slider[0].set_value(45).run()
    assert any("No feasible plan" in item.value for item in app.error)


def test_uploaded_rows_enter_the_plan_and_pen_slider_resolves_it():
    app = _app()
    payload = (ROOT / "data" / "upload_bad_rows.csv").read_bytes()
    app.file_uploader[0].upload("upload_bad_rows.csv", payload, "text/csv").run()
    next(button for button in app.button if button.key == "upload_add").click().run()
    assert not app.exception
    assert any("uploaded cohort(s)" in item.value for item in app.info)

    app.sidebar.radio[0].set_value("Optimizer").run()
    # The seeded TX-A pens are full, so 100 more head cannot fit until pen space is added.
    assert any("TX-A pen needs at least" in item.value for item in app.error)
    pen = next(slider for slider in app.slider if slider.key == "w_cap_shortage_TX-A_pen_capacity_sqft")
    pen.set_value(150000.0).run()
    assert not app.exception
    assert not app.error
    tables = "\n".join(frame.value.astype(str).to_string() for frame in app.dataframe)
    assert "UPLOAD-1" in tables

    app.sidebar.radio[0].set_value("Overview").run()
    next(button for button in app.button if button.key == "clear_upload").click().run()
    app.sidebar.radio[0].set_value("Optimizer").run()
    tables = "\n".join(frame.value.astype(str).to_string() for frame in app.dataframe)
    assert "UPLOAD-1" not in tables
