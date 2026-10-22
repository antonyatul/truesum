"""Describe a dataset: column types, statistics, missing values, plain-English summary."""
from __future__ import annotations

import warnings
from typing import Literal

import pandas as pd

ColumnType = Literal["numeric", "date", "category"]
_DATE_HINTS = ("date", "time", "day", "month", "period")


def _looks_like_dates(s: pd.Series) -> bool:
    sample = s.dropna().astype(str).head(200)
    if sample.empty or sample.str.fullmatch(r"-?\d+(\.\d+)?").all():
        return False  # plain numbers are not dates
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        parsed = pd.to_datetime(sample, errors="coerce", format="mixed")
    return parsed.notna().mean() >= 0.9


def _is_identifier(name: str) -> bool:
    n = name.lower().replace(" ", "_")
    return n in ("id", "code") or n.endswith(("_id", "_code", "_number", "_no")) or n.startswith("id_")


def column_types(df: pd.DataFrame) -> dict[str, ColumnType]:
    out: dict[str, ColumnType] = {}
    for col in df.columns:
        s = df[col]
        if pd.api.types.is_bool_dtype(s):
            out[col] = "category"
        elif pd.api.types.is_numeric_dtype(s):
            out[col] = "category" if _is_identifier(col) else "numeric"
        elif pd.api.types.is_datetime64_any_dtype(s):
            out[col] = "date"
        elif any(h in col.lower() for h in _DATE_HINTS) and _looks_like_dates(s):
            out[col] = "date"
        else:
            out[col] = "category"
    return out


def columns_of(df: pd.DataFrame, kind: ColumnType) -> list[str]:
    return [c for c, t in column_types(df).items() if t == kind]


def overview(df: pd.DataFrame) -> dict[str, float]:
    cells = df.size or 1
    return {
        "rows": len(df),
        "columns": df.shape[1],
        "missing_cells": int(df.isna().sum().sum()),
        "missing_pct": float(df.isna().sum().sum() / cells * 100),
        "duplicate_rows": int(df.duplicated().sum()),
    }


def numeric_stats(df: pd.DataFrame) -> pd.DataFrame:
    num = df.select_dtypes("number")
    if num.empty:
        return pd.DataFrame()
    stats = num.describe().T
    stats = stats.rename(columns={"25%": "q25", "50%": "median", "75%": "q75"})
    return stats[["count", "mean", "std", "min", "q25", "median", "q75", "max"]]


def category_stats(df: pd.DataFrame) -> pd.DataFrame:
    types = column_types(df)
    rows = []
    for col, kind in types.items():
        if kind == "numeric":
            continue
        s = df[col]
        vc = s.astype(str).where(s.notna()).value_counts()
        rows.append({
            "column": col,
            "type": kind,
            "distinct": int(s.nunique(dropna=True)),
            "most_common": vc.index[0] if len(vc) else "",
            "most_common_count": int(vc.iloc[0]) if len(vc) else 0,
        })
    return pd.DataFrame(rows)


def missing(df: pd.DataFrame) -> pd.DataFrame:
    n = df.isna().sum()
    out = pd.DataFrame({"missing": n, "missing_pct": n / max(len(df), 1) * 100})
    out.index.name = "column"
    return out.sort_values("missing", ascending=False).reset_index()


def text_summary(df: pd.DataFrame) -> list[str]:
    """A few plain-English observations. Rule-based, not AI."""
    lines: list[str] = []
    ov = overview(df)
    lines.append(f"The table has {ov['rows']:,} rows and {ov['columns']} columns.")

    miss = missing(df)
    miss = miss[miss["missing"] > 0]
    if miss.empty:
        lines.append("No values are missing.")
    else:
        worst = miss.iloc[0]
        lines.append(
            f"{len(miss)} column{'s have' if len(miss) > 1 else ' has'} gaps; the most is "
            f"'{worst['column']}' with {int(worst['missing']):,} missing ({worst['missing_pct']:.1f}%)."
        )

    if ov["duplicate_rows"]:
        lines.append(f"{ov['duplicate_rows']:,} rows are exact duplicates of another row.")

    num = df.select_dtypes("number")
    for col in num.columns[:6]:
        s = num[col].dropna()
        if s.empty:
            continue
        neg = int((s < 0).sum())
        line = f"'{col}' runs from {s.min():,.2f} to {s.max():,.2f}, median {s.median():,.2f}."
        if neg:
            line += f" {neg:,} values are negative."
        lines.append(line)

    if num.shape[1] >= 2:
        corr = num.corr(numeric_only=True).abs().fillna(0)
        for i in range(len(corr)):
            corr.iat[i, i] = 0
        a, b = divmod(int(corr.to_numpy().argmax()), corr.shape[1])
        r = num.corr(numeric_only=True).iat[a, b]
        if abs(r) >= 0.5:
            lines.append(
                f"'{corr.index[a]}' and '{corr.columns[b]}' move together strongly (correlation {r:.2f})."
            )
    return lines
