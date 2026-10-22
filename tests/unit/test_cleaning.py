import pandas as pd
import pytest

from smartlytics.core import cleaning, profile


def test_F02_H1_recommended_clean_on_sample(sample_raw):
    df, log = cleaning.clean_recommended(sample_raw)
    messages = " | ".join(e.message for e in log)
    assert len(df) == 5000
    assert "Removed 40 duplicate rows" in messages
    assert "Merged 60 labels" in messages
    assert pd.api.types.is_datetime64_any_dtype(df["order_date"])
    assert (df["product"] == "Unknown").sum() == 25
    assert set(df["region"]) == {"Scotland", "North England", "Midlands", "London", "South West", "Wales"}


def test_F02_H2_missing_cost_left_missing(sample_raw, sample_clean):
    # 50 missing costs planted; one sits on a duplicated row at most, so 49-50 remain
    assert 49 <= sample_clean["unit_cost"].isna().sum() <= 50


def test_F02_E7_input_not_mutated(sample_raw):
    before = sample_raw.copy()
    cleaning.clean_recommended(sample_raw)
    pd.testing.assert_frame_equal(sample_raw, before)


def test_F02_E2_currency_text_to_numbers():
    df = pd.DataFrame({"amount": ["£1,200", "$35.50", "  €7 ", None]})
    out, entry = cleaning.coerce_numeric(df)
    assert out["amount"].tolist()[:3] == [1200.0, 35.5, 7.0]
    assert pd.isna(out["amount"].iloc[3])
    assert "amount" in entry.message


def test_mostly_text_column_not_converted():
    df = pd.DataFrame({"code": ["A1", "B2", "3", "4"]})
    out, _ = cleaning.coerce_numeric(df)
    assert out["code"].tolist() == ["A1", "B2", "3", "4"]


def test_F02_E3_duplicate_headers_made_unique():
    df = pd.DataFrame([[1, 2, 3]], columns=["Sales Amount", "sales-amount", "Discount %"])
    out, _ = cleaning.standardise_columns(df)
    assert list(out.columns) == ["sales_amount", "sales_amount_2", "discount_pct"]


def test_F01_E6_long_header_cleaned():
    name = "A very long column name that goes on and on for sixty chars!!"
    out, _ = cleaning.standardise_columns(pd.DataFrame({name: [1]}))
    assert out.columns[0] == "a_very_long_column_name_that_goes_on_and_on_for_sixty_chars"


def test_header_with_only_symbols():
    out, _ = cleaning.standardise_columns(pd.DataFrame({"%%%": [1], "£": [2]}))
    assert len(set(out.columns)) == 2


def test_F02_E4_median_on_text_rejected():
    df = pd.DataFrame({"region": ["a", None]})
    with pytest.raises(ValueError, match="not numeric"):
        cleaning.fill_missing(df, {"region": "median"})


def test_fill_methods():
    df = pd.DataFrame({"n": [1.0, None, 3.0], "t": ["x", None, "x"]})
    out, _ = cleaning.fill_missing(df, {"n": "median", "t": "mode"})
    assert out["n"].tolist() == [1.0, 2.0, 3.0]
    assert out["t"].tolist() == ["x", "x", "x"]
    dropped, entry = cleaning.fill_missing(df, {"n": "drop_rows"})
    assert len(dropped) == 2 and entry.rows_after == 2


def test_F02_E5_drop_negative():
    df = pd.DataFrame({"revenue": [10, -5, 3], "x": ["a", "b", "c"]})
    out, entry = cleaning.drop_negative(df, ["revenue"])
    assert out["x"].tolist() == ["a", "c"]
    assert "Removed 1" in entry.message


def test_unify_case_keeps_most_common_spelling():
    df = pd.DataFrame({"city": ["London", "London", "london", "LONDON", None]})
    out, entry = cleaning.unify_case(df)
    assert out["city"].dropna().unique().tolist() == ["London"]
    assert "Merged 2" in entry.message


def test_trim_counts_only_real_changes():
    df = pd.DataFrame({"t": [" a", "b", None, "c  d"]})
    out, entry = cleaning.trim_text(df)
    assert out["t"].tolist()[:2] == ["a", "b"] and out["t"].iloc[3] == "c d"
    assert "2 text values" in entry.message


def test_identifier_columns_are_categories():
    df = pd.DataFrame({"customer_id": [1, 2], "order_no": [5, 6], "amount": [1.0, 2.0]})
    t = profile.column_types(df)
    assert t == {"customer_id": "category", "order_no": "category", "amount": "numeric"}
