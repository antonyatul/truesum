"""Page tests with Streamlit's AppTest: real page scripts, no browser."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from smartlytics.core import io
from smartlytics.ui.state import AppState

TIMEOUT = 60
APP = str(Path(__file__).resolve().parents[2] / "app.py")


def app() -> AppTest:
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    at.run()
    assert not at.exception, at.exception
    return at


def state(at: AppTest) -> AppState:
    return at.session_state["smartlytics"]


def go(at: AppTest, page: str) -> AppTest:
    at.switch_page(f"pages/{page}.py")
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    return at


def button(at: AppTest, key: str):
    return at.button(key=key)


def loaded(df: pd.DataFrame | None = None, name: str = "Sample") -> AppTest:
    at = app()
    if df is None:
        button(at, "load_sample").click().run()
    else:
        state(at).load(name, df)
        at.run()
    assert not at.exception
    return at


def markdown_text(at: AppTest) -> str:
    return " ".join(m.value for m in at.markdown) + " ".join(c.value for c in at.caption)


@pytest.mark.parametrize("page", ["overview", "sales", "customers", "charts", "report"])
def test_F01_N1_gate_on_every_page(page):
    at = go(app(), page)
    assert "No data loaded yet" in markdown_text(at)


def test_F01_H1_load_sample_shows_preview():
    at = loaded()
    assert state(at).df.shape == (5040, 11)
    assert any("Preview · Sample sales" in s.value for s in at.header)


def test_F02_H1_and_E1_clean_runs_once():
    at = go(loaded(), "overview")
    button(at, "clean_recommended").click().run()
    s = state(at)
    assert s.cleaned and len(s.df) == 5000
    n_steps = len(s.audit)
    assert button(at, "clean_recommended").disabled  # second click impossible
    at.run()
    assert len(state(at).audit) == n_steps


def test_F02_E6_undo_keeps_charts():
    at = go(loaded(), "overview")
    button(at, "clean_recommended").click().run()
    state(at).charts.append(object())  # stand-in: undo must not drop report charts
    button(at, "reset").click().run()
    s = state(at)
    assert not s.cleaned and len(s.df) == 5040 and not s.audit and len(s.charts) == 1


def test_F06_full_analysis_and_E8_reset_on_clean():
    at = go(loaded(), "overview")
    button(at, "clean_recommended").click().run()
    go(at, "sales")
    submit = [b for b in at.button if b.label == "Run analysis"][0]
    submit.click().run()
    assert not at.exception
    s = state(at)
    assert s.result is not None and s.result.metric == "profit"
    assert any("50 rows have no cost" in w.value for w in at.warning)
    # cleaning again must clear the analysis (columns may have changed)
    s.replace_data(s.df, [])
    assert s.result is None


def test_F06_E5_validation_error_shown():
    at = go(loaded(), "overview")
    button(at, "clean_recommended").click().run()
    go(at, "sales")
    at.selectbox(key="map_quantity").set_value("— none —")
    [b for b in at.button if b.label == "Run analysis"][0].click().run()
    assert any("quantity column is needed" in e.value for e in at.error)
    assert state(at).result is None


def test_F04_H2_add_chart_twice():
    at = go(loaded(), "overview")
    button(at, "clean_recommended").click().run()
    go(at, "charts")
    button(at, "save_builder_bar").click().run()
    button(at, "save_builder_bar").click().run()
    assert len(state(at).charts) == 1
    toasts = [t.value for t in at.toast]
    assert any("already in your report" in t for t in toasts)


def test_F04_E1_trend_without_dates_warns():
    df = pd.DataFrame({"region": ["a", "b"], "revenue": [1.0, 2.0]})
    at = go(loaded(df, "nodates.csv"), "charts")
    at.radio(key="chart_kind").set_value("trend").run()
    assert any("needs a date column" in w.value for w in at.warning)


def test_F05_E2_reorder_and_remove():
    at = go(loaded(), "overview")
    button(at, "clean_recommended").click().run()
    go(at, "charts")
    button(at, "save_builder_bar").click().run()
    at.radio(key="chart_kind").set_value("histogram").run()
    button(at, "save_builder_histogram").click().run()
    go(at, "report")
    first, second = [c.title for c in state(at).charts]
    button(at, "down_0").click().run()
    assert [c.title for c in state(at).charts] == [second, first]
    button(at, "rm_0").click().run()
    assert [c.title for c in state(at).charts] == [first]


def test_F01_E10_second_upload_resets_everything():
    at = go(loaded(), "overview")
    button(at, "clean_recommended").click().run()
    state(at).load("other.csv", pd.DataFrame({"a": [1]}))
    s = state(at)
    assert s.name == "other.csv" and not s.cleaned and not s.audit and not s.charts and s.result is None


def test_F01_E12_sessions_are_isolated():
    a, b = loaded(), app()
    assert state(a).has_data and not state(b).has_data


def test_F01_E6_long_names_and_unicode_pages_render():
    long = "A very long column name that goes on and on for sixty chars!!"
    df = pd.DataFrame({long: [1.0, 2.0, 3.0], "région 🌍": ["Île", "Île", "Paris"], "customer": ["x", "y", "x"]})
    at = loaded(df, "données 📊.csv")
    for page in ("overview", "sales", "customers", "charts", "report"):
        go(at, page)


def test_report_page_has_downloads():
    at = go(loaded(io.load_sample(), "s.csv"), "report")
    labels = [b.label for b in at.get("download_button")]
    assert any("Report (HTML)" in label for label in labels)
