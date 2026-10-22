"""Plain-English findings from a sales analysis. Rule-based: every sentence is a computed fact."""
from __future__ import annotations

import pandas as pd

from smartlytics.core.sales import SalesResult


def _pct(part: float, whole: float) -> float:
    return part / whole * 100 if whole else 0.0


def findings(r: SalesResult, limit: int = 6) -> list[str]:
    df, m = r.df, r.mapping
    value = "profit" if r.metric == "profit" else m.revenue
    word = "profit" if r.metric == "profit" else "revenue"
    rated = df[df["tier"].notna()]
    total = float(rated[value].sum())
    out: list[str] = []

    if total > 0:
        high = rated[rated["tier"] == "High"]
        out.append(f"The best quarter of sales (High tier) brings in {_pct(float(high[value].sum()), total):.0f}% "
                   f"of all {word}.")

    if m.product and m.product in df.columns and total > 0:
        by = rated.groupby(m.product)[value].agg(["sum", "size"]).sort_values("sum", ascending=False)
        if len(by) > 1:
            top_name, top = by.index[0], by.iloc[0]
            out.append(f"{top_name} earns {_pct(float(top['sum']), total):.0f}% of {word} from "
                       f"{_pct(float(top['size']), len(rated)):.0f}% of sales.")
            worst_name, worst = by.index[-1], by.iloc[-1]
            if worst["sum"] < 0:
                out.append(f"{worst_name} loses money overall ({worst['sum']:,.2f}).")

    if r.metric == "profit":
        losses = df[df["profit"] < 0]
        if len(losses):
            refunds = int((df[m.revenue] < 0).sum())
            out.append(f"{len(losses):,} sales lost money, {abs(losses['profit'].sum()):,.2f} in total"
                       + (f" ({refunds:,} of them refunds)." if refunds else "."))

    if m.customer and m.customer in df.columns:
        spend = df.groupby(m.customer)[m.revenue].sum().sort_values(ascending=False)
        if len(spend) >= 20 and spend.sum() > 0:
            top10 = _pct(float(spend.head(10).sum()), float(spend.sum()))
            if top10 >= 5:
                out.append(f"Your top 10 customers account for {top10:.0f}% of revenue (out of {len(spend):,} customers).")
            else:
                out.append(f"No customer dominates: the top 10 of {len(spend):,} make up {top10:.1f}% of revenue.")

    if m.date and m.date in df.columns and pd.api.types.is_datetime64_any_dtype(df[m.date]):
        monthly = df.dropna(subset=[m.date]).set_index(m.date)[value].resample("MS").sum()
        monthly = monthly[monthly.index.notna()]
        if len(monthly) >= 3:
            best, worst = monthly.idxmax(), monthly.idxmin()
            out.append(f"Best month was {best:%B %Y} ({monthly.max():,.2f} {word}); "
                       f"weakest was {worst:%B %Y} ({monthly.min():,.2f}).")
    return out[:limit]
