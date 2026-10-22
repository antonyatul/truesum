"""Sales analysis: column mapping, profit, quantile performance tiers.

Ported from Smart-Data-Analytics-Tool's SalesAnalyzer with two fixes:
- profit uses cost × quantity when cost is per unit (B1);
- a missing cost leaves profit unknown instead of treating the item as free (B2).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, fields

import pandas as pd

TIERS = ("High", "Medium", "Low")

# Candidate names per field, best first. Matched against snake_cased headers.
SYNONYMS: dict[str, tuple[str, ...]] = {
    "revenue": ("revenue", "net_revenue", "net_sales", "turnover", "sales_amount", "total_sales",
                "amount", "total", "sales", "gross_sales"),
    "cost": ("unit_cost", "cost", "cost_price", "cogs", "total_cost", "cost_of_goods"),
    "quantity": ("quantity", "qty", "units", "units_sold", "quantity_sold", "count"),
    "date": ("order_date", "date", "invoice_date", "transaction_date", "sale_date"),
    "customer": ("customer_id", "customer", "customer_name", "client", "client_id", "account"),
    "product": ("product", "product_name", "item", "sku", "product_id"),
}


def _norm(name: str) -> str:
    return re.sub(r"[^0-9a-z]+", "_", str(name).lower()).strip("_")


@dataclass
class SalesMapping:
    revenue: str | None = None
    cost: str | None = None
    quantity: str | None = None
    cost_is_per_unit: bool = True
    date: str | None = None
    customer: str | None = None
    product: str | None = None

    def columns(self) -> dict[str, str]:
        return {f.name: getattr(self, f.name) for f in fields(self)
                if f.name != "cost_is_per_unit" and getattr(self, f.name)}


@dataclass(frozen=True)
class Thresholds:
    metric: str
    q25: float
    q75: float
    mean: float
    minimum: float
    maximum: float
    rated_rows: int


@dataclass
class SalesResult:
    df: pd.DataFrame
    mapping: SalesMapping
    metric: str                     # "profit" or "revenue"
    thresholds: Thresholds
    totals: dict[str, float]
    warnings: list[str] = field(default_factory=list)


def guess_mapping(df: pd.DataFrame) -> SalesMapping:
    normalised = {_norm(c): c for c in df.columns}
    m = SalesMapping()
    for key, options in SYNONYMS.items():
        for option in options:
            if option in normalised:
                col = normalised[option]
                if key in ("revenue", "cost", "quantity") and not pd.api.types.is_numeric_dtype(df[col]):
                    continue
                if col in m.columns().values():
                    continue
                setattr(m, key, col)
                break
    if m.cost:
        name = _norm(m.cost)
        m.cost_is_per_unit = not ("total" in name or name == "cogs" or m.quantity is None)
    return m


def validate_mapping(df: pd.DataFrame, m: SalesMapping) -> list[str]:
    problems: list[str] = []
    if not m.revenue:
        problems.append("Choose the column that holds the sale amount (revenue).")
    for key in ("revenue", "cost", "quantity"):
        col = getattr(m, key)
        if col and col not in df.columns:
            problems.append(f"Column '{col}' is no longer in the data.")
        elif col and not pd.api.types.is_numeric_dtype(df[col]):
            problems.append(f"'{col}' must contain numbers to be used as {key}. Clean the data first.")
    if m.cost and m.cost_is_per_unit and not m.quantity:
        problems.append("Cost is set to per unit, so a quantity column is needed too.")
    used = list(m.columns().values())
    if len(used) != len(set(used)):
        problems.append("Each column can only be used for one field.")
    return problems


def compute_profit(df: pd.DataFrame, m: SalesMapping) -> pd.Series:
    revenue = df[m.revenue]
    if m.cost_is_per_unit:
        cost_total = df[m.cost] * df[m.quantity]
    else:
        cost_total = df[m.cost]
    return (revenue - cost_total).rename("profit")  # NaN wherever cost is unknown


def assign_tiers(values: pd.Series) -> tuple[pd.Series, Thresholds]:
    """Low < Q25 <= Medium < Q75 <= High. Unknown values stay unrated (NA)."""
    rated = values.dropna()
    if rated.empty:
        raise ValueError("No rows have a value to rate.")
    q25, q75 = float(rated.quantile(0.25)), float(rated.quantile(0.75))
    tier = pd.Series(pd.NA, index=values.index, dtype="string")
    tier[values >= q75] = "High"
    tier[(values >= q25) & (values < q75)] = "Medium"
    tier[values < q25] = "Low"
    t = Thresholds(
        metric=str(values.name or "value"), q25=q25, q75=q75, mean=float(rated.mean()),
        minimum=float(rated.min()), maximum=float(rated.max()), rated_rows=int(len(rated)),
    )
    return tier.rename("tier"), t


def analyse(df: pd.DataFrame, m: SalesMapping) -> SalesResult:
    problems = validate_mapping(df, m)
    if problems:
        raise ValueError(" ".join(problems))
    out = df.copy()
    warnings: list[str] = []

    if m.cost:
        out["profit"] = compute_profit(out, m)
        metric = "profit"
        unknown = int(out["profit"].isna().sum())
        if unknown:
            warnings.append(
                f"{unknown:,} rows have no cost, so their profit is unknown and they are not rated."
            )
    else:
        metric = m.revenue
        warnings.append("No cost column mapped, so rows are rated on revenue instead of profit.")

    out["tier"], thresholds = assign_tiers(out[metric].rename(metric))

    revenue_total = float(out[m.revenue].sum())
    totals: dict[str, float] = {"rows": len(out), "revenue": revenue_total}
    if metric == "profit":
        known = out["profit"].notna()
        profit_total = float(out.loc[known, "profit"].sum())
        known_revenue = float(out.loc[known, m.revenue].sum())
        totals["profit"] = profit_total
        totals["margin_pct"] = profit_total / known_revenue * 100 if known_revenue else float("nan")
        totals["loss_rows"] = int((out["profit"] < 0).sum())
    for t in TIERS:
        totals[f"{t.lower()}_rows"] = int((out["tier"] == t).sum())
    totals["unrated_rows"] = int(out["tier"].isna().sum())
    if (out[m.revenue] < 0).any():
        warnings.append(
            f"{int((out[m.revenue] < 0).sum()):,} rows have negative revenue (returns or refunds) "
            "and are included in totals."
        )
    return SalesResult(out, m, metric, thresholds, totals, warnings)


def tier_summary(r: SalesResult) -> pd.DataFrame:
    df = r.df[r.df["tier"].notna()]
    agg = {"rows": (r.mapping.revenue, "size"), "revenue": (r.mapping.revenue, "sum")}
    if r.metric == "profit":
        agg["profit"] = ("profit", "sum")
    out = df.groupby("tier").agg(**agg).reindex(list(TIERS)).fillna(0)
    out["share_of_rows_pct"] = out["rows"] / max(out["rows"].sum(), 1) * 100
    return out.reset_index()


def threshold_table(t: Thresholds) -> pd.DataFrame:
    label = t.metric.replace("_", " ")
    return pd.DataFrame({
        "measure": [f"Low / Medium boundary (25th percentile {label})",
                    f"Medium / High boundary (75th percentile {label})",
                    f"Average {label}", f"Lowest {label}", f"Highest {label}"],
        "value": [t.q25, t.q75, t.mean, t.minimum, t.maximum],
    })


def top_performers(r: SalesResult, limit: int | None = None) -> pd.DataFrame:
    top = r.df[r.df["tier"] == "High"].sort_values(r.metric, ascending=False)
    return top.head(limit) if limit else top


def breakdown(r: SalesResult, by: str, limit: int = 15) -> pd.DataFrame:
    values = [r.mapping.revenue] + (["profit"] if r.metric == "profit" else [])
    out = r.df.groupby(by, dropna=False)[values].sum().sort_values(values[-1], ascending=False)
    out.index = out.index.astype(str)
    return out.head(limit).reset_index()
