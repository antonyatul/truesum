import numpy as np
import pandas as pd
import pytest

from smartlytics.core import cleaning, io, sales
from tests.conftest import ORIGINAL_100K, tiny_sales


def test_F06_H1_guess_mapping_on_sample(sample_clean):
    m = sales.guess_mapping(sample_clean)
    assert (m.revenue, m.cost, m.quantity, m.cost_is_per_unit) == ("revenue", "unit_cost", "quantity", True)
    assert (m.date, m.customer, m.product) == ("order_date", "customer_id", "product")


def test_F06_H2_profit_uses_cost_times_quantity():
    df = tiny_sales()
    m = sales.SalesMapping(revenue="revenue", cost="unit_cost", quantity="quantity")
    p = sales.compute_profit(df, m)
    assert p.tolist()[:3] == [60.0, 20.0, 170.0]  # 100-20*2, 50-10*3, 200-30*1


def test_F06_E4_missing_cost_is_unknown_not_free():
    r = sales.analyse(tiny_sales(), sales.SalesMapping(revenue="revenue", cost="unit_cost", quantity="quantity"))
    assert pd.isna(r.df["profit"].iloc[3])
    assert pd.isna(r.df["tier"].iloc[3])
    assert r.totals["unrated_rows"] == 1
    assert any("no cost" in w for w in r.warnings)


def test_F06_E2_cost_already_a_row_total():
    m = sales.SalesMapping(revenue="revenue", cost="unit_cost", quantity="quantity", cost_is_per_unit=False)
    p = sales.compute_profit(tiny_sales(), m)
    assert p.tolist()[:3] == [80.0, 40.0, 170.0]


def test_F06_H3_tiers_are_quartile_based():
    values = pd.Series(np.arange(1, 101, dtype=float), name="profit")
    tier, t = sales.assign_tiers(values)
    assert tier.value_counts().to_dict() == {"Medium": 50, "High": 25, "Low": 25}
    assert t.q25 == pytest.approx(25.75) and t.q75 == pytest.approx(75.25)
    assert (tier[values >= t.q75] == "High").all()
    assert (tier[values < t.q25] == "Low").all()


def test_F06_E3_identical_values_all_high():
    tier, t = sales.assign_tiers(pd.Series([5.0] * 10, name="profit"))
    assert t.q25 == t.q75 == 5.0
    assert (tier == "High").all()


def test_assign_tiers_needs_values():
    with pytest.raises(ValueError):
        sales.assign_tiers(pd.Series([np.nan, np.nan], name="profit"))


def test_F06_E1_no_cost_rates_on_revenue():
    r = sales.analyse(tiny_sales(), sales.SalesMapping(revenue="revenue"))
    assert r.metric == "revenue"
    assert "profit" not in r.df.columns
    assert r.totals["unrated_rows"] == 0
    assert any("rated on revenue" in w for w in r.warnings)


def test_F06_E5_per_unit_without_quantity_blocked():
    m = sales.SalesMapping(revenue="revenue", cost="unit_cost", cost_is_per_unit=True)
    assert any("quantity" in p for p in sales.validate_mapping(tiny_sales(), m))
    with pytest.raises(ValueError):
        sales.analyse(tiny_sales(), m)


def test_F06_E6_same_column_twice_blocked():
    m = sales.SalesMapping(revenue="revenue", cost="revenue", cost_is_per_unit=False)
    assert any("only be used for one" in p for p in sales.validate_mapping(tiny_sales(), m))


def test_F06_N1_text_revenue_blocked():
    m = sales.SalesMapping(revenue="customer")
    assert any("must contain numbers" in p for p in sales.validate_mapping(tiny_sales(), m))


def test_missing_revenue_blocked():
    assert sales.validate_mapping(tiny_sales(), sales.SalesMapping())


def test_totals_and_margin(sample_result):
    t = sample_result.totals
    assert t["rows"] == 5000
    assert t["high_rows"] + t["medium_rows"] + t["low_rows"] + t["unrated_rows"] == 5000
    known = sample_result.df["profit"].notna()
    expected_margin = sample_result.df.loc[known, "profit"].sum() / sample_result.df.loc[known, "revenue"].sum() * 100
    assert t["margin_pct"] == pytest.approx(expected_margin)


def test_tier_summary_and_breakdown(sample_result):
    summary = sales.tier_summary(sample_result)
    assert summary["tier"].tolist() == ["High", "Medium", "Low"]
    assert summary["share_of_rows_pct"].sum() == pytest.approx(100)
    b = sales.breakdown(sample_result, "product")
    assert b["profit"].is_monotonic_decreasing
    assert "Laptop" in b["product"].tolist()


def test_top_performers_sorted(sample_result):
    top = sales.top_performers(sample_result)
    assert (top["tier"] == "High").all()
    assert top["profit"].is_monotonic_decreasing


def test_guess_mapping_with_total_cost():
    df = pd.DataFrame({"Turnover": [10.0], "Total Cost": [4.0], "Qty": [2]})
    df, _ = cleaning.standardise_columns(df)
    m = sales.guess_mapping(df)
    assert (m.revenue, m.cost, m.quantity, m.cost_is_per_unit) == ("turnover", "total_cost", "qty", False)


@pytest.mark.skipif(not ORIGINAL_100K.exists(), reason="original 100k file not available")
def test_F06_E7_original_tool_dataset_regression():
    df, _ = cleaning.clean_recommended(io.read_table(ORIGINAL_100K.read_bytes(), ORIGINAL_100K.name))
    r = sales.analyse(df, sales.guess_mapping(df))
    assert r.thresholds.mean == pytest.approx(283.08, abs=0.01)
    assert r.totals["unrated_rows"] == 407
