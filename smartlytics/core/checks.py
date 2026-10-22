"""Data checks: does the maths in the file add up? Each check counts rows and keeps them for download."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime

import pandas as pd

from smartlytics.core.sales import SalesMapping

TOLERANCE = 0.02  # money: allow 2p rounding
EXTRA_SYNONYMS = {
    "price": ("unit_price", "price", "selling_price", "sale_price", "price_each"),
    "gross": ("gross_sales", "gross", "sales", "gross_amount", "line_total"),
    "discount": ("discount_pct", "discount", "discount_percent", "discount_rate"),
}


def _norm(name: str) -> str:
    return re.sub(r"[^0-9a-z]+", "_", str(name).lower()).strip("_")


def find_extra_columns(df: pd.DataFrame, m: SalesMapping) -> dict[str, str]:
    """Columns the checks can use beyond the sales mapping (price, gross, discount)."""
    taken = set(m.columns().values())
    names = {_norm(c): c for c in df.columns if c not in taken and pd.api.types.is_numeric_dtype(df[c])}
    found = {}
    for key, options in EXTRA_SYNONYMS.items():
        for o in options:
            if o in names and names[o] not in found.values():
                found[key] = names[o]
                break
    return found


@dataclass
class Check:
    name: str
    explanation: str
    flagged: int
    checked: int
    rows: pd.DataFrame = field(repr=False, default_factory=pd.DataFrame)

    @property
    def passed(self) -> bool:
        return self.flagged == 0


def _check(df: pd.DataFrame, name: str, explanation: str, mask: pd.Series, applicable: pd.Series | None = None) -> Check:
    mask = mask.fillna(False).astype(bool)
    checked = int(applicable.sum()) if applicable is not None else len(df)
    return Check(name, explanation, int(mask.sum()), checked, df.loc[mask])


def run_checks(df: pd.DataFrame, m: SalesMapping, today: datetime | None = None) -> list[Check]:
    extra = find_extra_columns(df, m)
    out: list[Check] = []
    rev, cost, qty = m.revenue, m.cost, m.quantity
    price, gross, disc = extra.get("price"), extra.get("gross"), extra.get("discount")

    gross_wrong = pd.Series(False, index=df.index)
    if qty and price and gross:
        expected = df[qty] * df[price]
        ok = df[[qty, price, gross]].notna().all(axis=1)
        bad = ok & ((df[gross] - expected).abs() > TOLERANCE + expected.abs() * 0.001)
        gross_wrong = bad
        out.append(_check(df, f"{gross} = {qty} × {price}",
                          f"'{gross}' should equal quantity times price. Mismatches are often typing errors.", bad, ok))
    if rev and gross and disc:
        expected = df[gross] * (1 - df[disc] / 100)
        ok = df[[rev, gross, disc]].notna().all(axis=1) & ~gross_wrong  # can't judge revenue when gross is wrong
        bad = ok & ((df[rev] - expected).abs() > TOLERANCE + expected.abs() * 0.001)
        out.append(_check(df, f"{rev} = {gross} after {disc}",
                          f"'{rev}' should be '{gross}' less the discount (rows with a wrong '{gross}' are skipped).", bad, ok))
    elif rev and gross:
        ok = df[[rev, gross]].notna().all(axis=1)
        bad = ok & (df[rev].abs() > df[gross].abs() + TOLERANCE)
        out.append(_check(df, f"{rev} not above {gross}", f"Net '{rev}' shouldn't be bigger than gross '{gross}'.", bad, ok))
    if disc:
        out.append(_check(df, f"{disc} between 0 and 100", "Discounts outside 0–100% are usually entry errors.",
                          (df[disc] < 0) | (df[disc] > 100)))
    if price and cost and m.cost_is_per_unit:
        ok = df[[price, cost]].notna().all(axis=1)
        out.append(_check(df, f"{price} above {cost}", "Selling below cost loses money on every unit. Check these are intended.",
                          ok & (df[price] < df[cost]), ok))
    if cost:
        out.append(_check(df, f"{cost} present", "Rows without a cost can't have a profit worked out.", df[cost].isna()))
    if qty:
        out.append(_check(df, f"{qty} positive", "Zero or negative quantities are usually returns or mistakes.", df[qty] <= 0))
    if rev:
        out.append(_check(df, f"{rev} positive", "Negative revenue is usually a refund. They're counted in totals.", df[rev] < 0))
    if m.date and pd.api.types.is_datetime64_any_dtype(df[m.date]):
        now = pd.Timestamp(today or datetime.now())
        out.append(_check(df, f"{m.date} not in the future", "Sales dated after today are usually typing errors.",
                          df[m.date] > now))
    return out


def summary(checks: list[Check]) -> pd.DataFrame:
    return pd.DataFrame([{"check": c.name, "rows flagged": c.flagged, "rows checked": c.checked,
                          "result": "OK" if c.passed else "Look at these", "why it matters": c.explanation}
                         for c in checks])
