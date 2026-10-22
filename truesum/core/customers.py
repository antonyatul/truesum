"""Customer views: who spends most, who comes back."""
from __future__ import annotations

import pandas as pd


def top_customers(df: pd.DataFrame, customer: str, amount: str, n: int = 10) -> pd.DataFrame:
    if not pd.api.types.is_numeric_dtype(df[amount]):
        raise ValueError(f"'{amount}' must contain numbers.")
    total = df[amount].sum()
    out = (
        df.groupby(customer, dropna=True)[amount]
        .agg(total="sum", orders="size")
        .sort_values("total", ascending=False)
        .head(n)
    )
    out["share_pct"] = out["total"] / total * 100 if total else 0.0
    out.index = out.index.astype(str)
    return out.reset_index().rename(columns={customer: "customer"})


def repeat_customers(df: pd.DataFrame, customer: str) -> tuple[pd.DataFrame, dict[str, float]]:
    counts = df[customer].dropna().astype(str).value_counts()
    repeat = counts[counts > 1]
    stats = {
        "customers": int(len(counts)),
        "repeat_customers": int(len(repeat)),
        "repeat_pct": float(len(repeat) / len(counts) * 100) if len(counts) else 0.0,
        "orders_from_repeat_pct": float(repeat.sum() / counts.sum() * 100) if counts.sum() else 0.0,
    }
    table = repeat.rename("orders").rename_axis("customer").reset_index()
    return table, stats
