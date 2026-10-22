"""Cleaning steps. Each takes a DataFrame and returns (new_df, AuditEntry); input is never mutated."""
from __future__ import annotations

import re
from typing import Literal

import pandas as pd

from truesum.core.audit import AuditEntry
from truesum.core.profile import column_types

FillMethod = Literal["leave", "drop_rows", "median", "mean", "mode", "zero", "unknown"]
_CURRENCY = re.compile(r"[£$€,\s]")


def _changed(before: pd.Series, after: pd.Series) -> int:
    """Count cells whose value changed, treating any two missing values as equal."""
    both_missing = before.isna() & after.isna()
    return int((~both_missing & (before.astype(object) != after.astype(object))).sum())


def _snake(name: str) -> str:
    s = re.sub(r"[^0-9a-zA-Z]+", "_", str(name).strip().lower()).strip("_")
    return s or "column"


def standardise_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, AuditEntry]:
    new, seen = [], {}
    for col in df.columns:
        base = _snake(col).replace("__", "_")
        if "%" in str(col) and not base.endswith("pct"):
            base = f"{base}_pct"
        n = seen.get(base, 0)
        seen[base] = n + 1
        new.append(base if n == 0 else f"{base}_{n + 1}")
    renamed = sum(a != b for a, b in zip(df.columns, new, strict=True))
    out = df.copy()
    out.columns = new
    return out, AuditEntry("standardise_columns", f"Renamed {renamed} column headers to snake_case", len(df), len(out))


def trim_text(df: pd.DataFrame) -> tuple[pd.DataFrame, AuditEntry]:
    out = df.copy()
    changed = 0
    for col in out.columns:
        s = out[col]
        if pd.api.types.is_object_dtype(s) or pd.api.types.is_string_dtype(s):
            if pd.api.types.is_numeric_dtype(s):
                continue
            text = s.astype("string")
            cleaned = text.str.strip().str.replace(r"\s+", " ", regex=True)
            cleaned = cleaned.mask(cleaned == "")
            result = cleaned.astype(object).where(cleaned.notna(), None)
            changed += _changed(s, result)
            out[col] = result
    return out, AuditEntry("trim_text", f"Trimmed spaces in {changed:,} text values", len(df), len(out))


def unify_case(df: pd.DataFrame, max_distinct: int = 50) -> tuple[pd.DataFrame, AuditEntry]:
    """Merge category labels that differ only by case ('london' vs 'London')."""
    out = df.copy()
    fixed = 0
    for col, kind in column_types(out).items():
        if kind != "category":
            continue
        s = out[col]
        counts = s.dropna().astype(str).value_counts()
        if len(counts) > max_distinct or len(counts) == 0:
            continue
        # most common spelling wins within each case-insensitive group (works on uniques, not rows)
        canonical: dict[str, str] = {}
        for value in counts.index:  # value_counts is sorted most common first
            canonical.setdefault(value.casefold(), value)
        mapping = {v: canonical[v.casefold()] for v in counts.index if canonical[v.casefold()] != v}
        if not mapping:
            continue
        mapped = s.where(~s.astype(str).isin(mapping.keys()), s.astype(str).map(mapping))
        fixed += int(s.astype(str).isin(mapping.keys()).sum())
        out[col] = mapped
    return out, AuditEntry("unify_case", f"Merged {fixed:,} labels that only differed by capitalisation", len(df), len(out))


def coerce_numeric(df: pd.DataFrame, threshold: float = 0.95) -> tuple[pd.DataFrame, AuditEntry]:
    """Convert text columns that are almost all numbers ('£1,200') into numbers."""
    out = df.copy()
    converted: list[str] = []
    for col in out.columns:
        s = out[col]
        if pd.api.types.is_numeric_dtype(s) or pd.api.types.is_datetime64_any_dtype(s):
            continue
        present = s.dropna()
        if present.empty:
            continue
        probe = present.sample(min(len(present), 2000), random_state=0) if len(present) > 2000 else present
        if pd.to_numeric(probe.astype(str).str.replace(_CURRENCY, "", regex=True), errors="coerce").notna().mean() < threshold:
            continue  # clearly not a number column; skip the full pass
        nums = pd.to_numeric(present.astype(str).str.replace(_CURRENCY, "", regex=True), errors="coerce")
        if nums.notna().mean() >= threshold:
            full = pd.to_numeric(s.astype(str).str.replace(_CURRENCY, "", regex=True), errors="coerce")
            out[col] = full.where(s.notna())
            converted.append(col)
    msg = (f"Converted {len(converted)} text column{'s' if len(converted) != 1 else ''} to numbers: {', '.join(converted)}"
           if converted else "No text columns needed converting to numbers")
    return out, AuditEntry("coerce_numeric", msg, len(df), len(out))


def parse_dates(df: pd.DataFrame) -> tuple[pd.DataFrame, AuditEntry]:
    out = df.copy()
    parsed: list[str] = []
    for col, kind in column_types(out).items():
        if kind == "date" and not pd.api.types.is_datetime64_any_dtype(out[col]):
            out[col] = pd.to_datetime(out[col], errors="coerce", format="mixed")
            parsed.append(col)
    msg = (f"Read {len(parsed)} column{'s' if len(parsed) != 1 else ''} as dates: {', '.join(parsed)}"
           if parsed else "No columns needed reading as dates")
    return out, AuditEntry("parse_dates", msg, len(df), len(out))


def drop_duplicates(df: pd.DataFrame) -> tuple[pd.DataFrame, AuditEntry]:
    out = df.drop_duplicates().reset_index(drop=True)
    return out, AuditEntry("drop_duplicates", f"Removed {len(df) - len(out):,} duplicate rows", len(df), len(out))


def fill_missing(df: pd.DataFrame, plan: dict[str, FillMethod]) -> tuple[pd.DataFrame, AuditEntry]:
    """Apply a per-column strategy. Columns not in the plan are left alone."""
    out = df.copy()
    parts: list[str] = []
    drop_cols = [c for c, m in plan.items() if m == "drop_rows" and c in out.columns]
    for col, method in plan.items():
        if col not in out.columns or method in ("leave", "drop_rows"):
            continue
        n = int(out[col].isna().sum())
        if not n:
            continue
        s = out[col]
        if method in ("median", "mean", "zero") and not pd.api.types.is_numeric_dtype(s):
            raise ValueError(f"'{col}' is not numeric, so it can't be filled with the {method}.")
        if method == "median":
            value = s.median()
        elif method == "mean":
            value = s.mean()
        elif method == "zero":
            value = 0
        elif method == "mode":
            m = s.mode(dropna=True)
            if m.empty:
                continue
            value = m.iloc[0]
        else:  # unknown
            value = "Unknown"
        out[col] = s.fillna(value)
        parts.append(f"{col} ({n:,} → {method})")
    if drop_cols:
        before = len(out)
        out = out.dropna(subset=drop_cols).reset_index(drop=True)
        parts.append(f"dropped {before - len(out):,} rows missing {', '.join(drop_cols)}")
    msg = "Filled missing values: " + "; ".join(parts) if parts else "No missing values changed"
    return out, AuditEntry("fill_missing", msg, len(df), len(out))


def drop_negative(df: pd.DataFrame, columns: list[str]) -> tuple[pd.DataFrame, AuditEntry]:
    cols = [c for c in columns if c in df.columns and pd.api.types.is_numeric_dtype(df[c])]
    if not cols:
        return df.copy(), AuditEntry("drop_negative", "No numeric columns chosen for the negative-value check", len(df), len(df))
    mask = (df[cols] < 0).any(axis=1)
    out = df.loc[~mask].reset_index(drop=True)
    return out, AuditEntry(
        "drop_negative", f"Removed {int(mask.sum()):,} rows with negative {', '.join(cols)}", len(df), len(out)
    )


def recommended_plan(df: pd.DataFrame) -> dict[str, FillMethod]:
    """Default missing-value plan: label missing text 'Unknown', leave numbers alone.

    Numbers are left missing on purpose: guessing a cost or a price changes the
    answer, and the analysis treats a missing number as 'not known' instead.
    """
    types = column_types(df)
    return {c: ("unknown" if types[c] == "category" else "leave") for c in df.columns if df[c].isna().any()}


def clean_recommended(df: pd.DataFrame) -> tuple[pd.DataFrame, list[AuditEntry]]:
    entries: list[AuditEntry] = []
    for step in (standardise_columns, trim_text, unify_case, coerce_numeric, parse_dates, drop_duplicates):
        df, entry = step(df)
        entries.append(entry)
    df, entry = fill_missing(df, recommended_plan(df))
    entries.append(entry)
    return df, entries
