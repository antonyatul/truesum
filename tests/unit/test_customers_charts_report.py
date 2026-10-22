import json

import numpy as np
import pandas as pd
import pytest

from smartlytics.core import charts, customers, profile, report
from smartlytics.core.audit import AuditEntry
from smartlytics.core.charts import ChartError, ChartSpec
from tests.conftest import tiny_sales


# ---- customers ---------------------------------------------------------------
def test_F03_H1_top_customers():
    top = customers.top_customers(tiny_sales(), "customer", "revenue", 2)
    assert top["customer"].tolist() == ["A", "B"]
    assert top["total"].tolist() == [300.0, 50.0]
    assert top["share_pct"].iloc[0] == pytest.approx(300 / 360 * 100)


def test_F03_H2_repeat_customers():
    table, stats = customers.repeat_customers(tiny_sales(), "customer")
    assert table.to_dict("records") == [{"customer": "A", "orders": 2}]
    assert stats == {"customers": 3, "repeat_customers": 1, "repeat_pct": pytest.approx(100 / 3),
                     "orders_from_repeat_pct": 50.0}


def test_F03_E1_no_repeats():
    table, stats = customers.repeat_customers(pd.DataFrame({"c": ["a", "b"]}), "c")
    assert table.empty and stats["repeat_customers"] == 0


def test_F03_E2_numeric_ids_are_categories(sample_clean):
    df = pd.DataFrame({"customer_id": [101, 102, 101], "revenue": [1.0, 2.0, 3.0]})
    assert profile.column_types(df)["customer_id"] == "category"
    assert customers.top_customers(df, "customer_id", "revenue")["customer"].tolist() == ["101", "102"]


def test_F03_N1_text_amount_rejected():
    with pytest.raises(ValueError):
        customers.top_customers(tiny_sales(), "customer", "customer")


# ---- charts -------------------------------------------------------------------
@pytest.mark.parametrize("spec", [
    ChartSpec("histogram", x="revenue"), ChartSpec("bar", x="product", y="revenue"),
    ChartSpec("bar", x="region", agg="count"), ChartSpec("bar", x="region", y="revenue", agg="mean"),
    ChartSpec("pie", x="region"), ChartSpec("pie", x="category", y="revenue"),
    ChartSpec("scatter", x="quantity", y="revenue"), ChartSpec("correlation"),
    ChartSpec("trend", x="order_date", y="revenue", freq="W", smooth=4),
])
def test_F04_H1_every_chart_builds(sample_clean, spec):
    built = charts.build(sample_clean, spec)
    assert built.figure.data
    assert built.figure.layout.title.text[0].isupper()


def test_F04_E1_trend_needs_a_date(sample_clean):
    with pytest.raises(ChartError, match="date"):
        charts.build(sample_clean, ChartSpec("trend", x="region", y="revenue"))


def test_chart_needs_numeric_y(sample_clean):
    with pytest.raises(ChartError, match="numbers"):
        charts.build(sample_clean, ChartSpec("scatter", x="quantity", y="region"))


def test_F04_E2_scatter_sampled():
    df = pd.DataFrame({"a": np.arange(20000.0), "b": np.arange(20000.0)})
    built = charts.build(df, ChartSpec("scatter", x="a", y="b"))
    assert len(built.figure.data[0].x) == charts.SCATTER_MAX
    assert "5,000 of 20,000" in built.note


def test_F04_E3_bar_capped():
    df = pd.DataFrame({"k": [f"c{i}" for i in range(500)], "v": np.ones(500)})
    built = charts.build(df, ChartSpec("bar", x="k", y="v"))
    assert len(built.figure.data[0].x) == charts.BAR_MAX
    assert "top 20 of 500" in built.note


def test_pie_groups_small_slices():
    df = pd.DataFrame({"k": [f"c{i}" for i in range(30)]})
    built = charts.build(df, ChartSpec("pie", x="k"))
    labels = list(built.figure.data[0].labels)
    assert len(labels) == charts.PIE_MAX and labels[-1] == "Other"
    assert sum(built.figure.data[0].values) == 30


def test_F04_E4_correlation_needs_two_numbers():
    with pytest.raises(ChartError, match="two number"):
        charts.build(pd.DataFrame({"a": [1, 2]}), ChartSpec("correlation"))


def test_F04_E5_histogram_payload_small():
    df = pd.DataFrame({"v": np.random.default_rng(0).normal(size=200_000)})
    built = charts.build(df, ChartSpec("histogram", x="v"))
    assert len(built.figure.to_json()) < 50_000
    assert sum(built.figure.data[0].y) == 200_000


def test_threshold_and_sales_charts(sample_result):
    b = charts.profit_thresholds(sample_result)
    texts = [a.text for a in b.figure.layout.annotations]
    assert len(texts) == 3 and texts[0].startswith("Low / Medium")
    assert len({a.y for a in b.figure.layout.annotations}) == 3  # staggered labels
    assert charts.sales_vs_profit(sample_result).figure.data


# ---- report -------------------------------------------------------------------
def test_F05_H1_full_report(sample_clean, sample_result):
    saved = [report.SavedChart("Profit chart", charts.profit_thresholds(sample_result).figure.to_json())]
    log = [AuditEntry("x", "Removed 40 duplicate rows", 5040, 5000)]
    html = report.build_html("Sample", sample_clean, log, sample_result, saved).decode()
    for needle in ("Sales performance", "Tier boundaries", "Top 20 rows", "Profit chart", "Removed 40 duplicate rows",
                   "Missing values", "Number columns"):
        assert needle in html
    assert html.count("Plotly.newPlot") == 1


def test_F05_H2_report_without_sales(sample_clean):
    html = report.build_html("Sample", sample_clean, [], None, []).decode()
    assert "Sales performance" not in html and "<h2>Charts</h2>" not in html


def test_F05_E3_plotly_js_embedded_once(sample_clean, sample_result):
    fig = charts.build(sample_clean, ChartSpec("histogram", x="revenue")).figure.to_json()
    html = report.build_html("S", sample_clean, [], None, [report.SavedChart("a", fig), report.SavedChart("b", fig)]).decode()
    assert html.count("Plotly.newPlot") == 2
    assert html.count("plotly.js v") == 1  # library header appears once


def test_F05_E1_report_escapes_user_text():
    evil = "<script>alert(1)</script>"
    df = pd.DataFrame({evil: ["<img src=x onerror=alert(2)>"], "n": [1.0]})
    html = report.build_html(evil, df, [AuditEntry("x", evil, 1, 1)], None,
                             [report.SavedChart(evil, json.dumps({"data": [], "layout": {}}))]).decode()
    assert "<script>alert(1)</script>" not in html
    assert "<img src=x" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
