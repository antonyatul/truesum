"""Generate the bundled demo dataset (synthetic, original, deterministic).

python scripts/make_sample.py  ->  sample_data/sales_sample.csv

Shape mirrors a typical retail sales export: per-unit cost and price, a discount,
gross sales and net revenue. Deliberately messy so cleaning has work to do:
~1% missing cost, ~0.5% missing product, some exact duplicate rows, a few
returns (negative quantity and revenue), inconsistent whitespace/case, and 25 gross
sales figures typed ten times too large.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

SEED = 20251113
ROWS = 5000
OUT = Path(__file__).resolve().parents[1] / "sample_data" / "sales_sample.csv"

# product: (category, unit cost, unit price)
CATALOGUE = {
    "Laptop": ("Electronics", 520.0, 899.0),
    "Monitor": ("Electronics", 95.0, 189.0),
    "Tablet": ("Electronics", 180.0, 329.0),
    "Headphones": ("Audio", 28.0, 79.0),
    "Speaker": ("Audio", 34.0, 89.0),
    "Keyboard": ("Accessories", 14.0, 45.0),
    "Mouse": ("Accessories", 5.5, 19.0),
    "USB-C Hub": ("Accessories", 11.0, 39.0),
    "Webcam": ("Accessories", 21.0, 59.0),
    "Desk Lamp": ("Office", 9.0, 29.0),
    "Office Chair": ("Office", 85.0, 219.0),
    "Notebook Pack": ("Office", 2.2, 8.5),
}
REGIONS = ["Scotland", "North England", "Midlands", "London", "South West", "Wales"]
REGION_WEIGHTS = [0.14, 0.2, 0.18, 0.26, 0.12, 0.1]
DISCOUNTS = [0, 0, 0, 5, 10, 15, 20]


def build() -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    names = list(CATALOGUE)
    popularity = np.array([3, 6, 4, 8, 5, 9, 12, 7, 5, 6, 2, 10], dtype=float)
    product = rng.choice(names, ROWS, p=popularity / popularity.sum())
    category = [CATALOGUE[p][0] for p in product]
    base_cost = np.array([CATALOGUE[p][1] for p in product])
    base_price = np.array([CATALOGUE[p][2] for p in product])
    # small per-row price variation (supplier and promo noise)
    cost = np.round(base_cost * rng.normal(1, 0.04, ROWS), 2)
    price = np.round(base_price * rng.normal(1, 0.03, ROWS), 2)
    quantity = rng.choice([1, 1, 1, 2, 2, 3, 4, 5, 8, 10], ROWS)
    discount = rng.choice(DISCOUNTS, ROWS)
    sales = np.round(quantity * price, 2)
    revenue = np.round(sales * (1 - discount / 100), 2)

    start = np.datetime64("2024-01-01")
    days = rng.integers(0, 730, ROWS)
    date = (start + days.astype("timedelta64[D]")).astype(str)

    # customers: a long tail with a few heavy repeat buyers
    ranks = np.arange(1, 801)
    weights = 1 / ranks**0.9
    customer = 1000 + rng.choice(ranks, ROWS, p=weights / weights.sum())

    df = pd.DataFrame({
        "Order Date": date,
        "Product": product,
        "Category": category,
        "Quantity": quantity,
        "Unit Cost": cost,
        "Unit Price": price,
        "Discount %": discount,
        "Gross Sales": sales,
        "Revenue": revenue,
        "Customer ID": [f"C{c:04d}" for c in customer],
        "Region": rng.choice(REGIONS, ROWS, p=REGION_WEIGHTS),
    }).sort_values("Order Date", kind="stable").reset_index(drop=True)

    # --- deliberate mess ---------------------------------------------------
    df["Unit Cost"] = df["Unit Cost"].astype("float64")
    df.loc[rng.choice(ROWS, 50, replace=False), "Unit Cost"] = np.nan
    df["Product"] = df["Product"].astype(object)
    df.loc[rng.choice(ROWS, 25, replace=False), "Product"] = np.nan
    returns = rng.choice(ROWS, 12, replace=False)
    df.loc[returns, ["Quantity", "Gross Sales", "Revenue"]] *= -1
    messy = rng.choice(ROWS, 60, replace=False)
    df.loc[messy, "Region"] = df.loc[messy, "Region"].map(lambda r: f"  {r.lower()} ")
    dupes = df.sample(40, random_state=SEED)
    df = pd.concat([df, dupes]).sort_values("Order Date", kind="stable").reset_index(drop=True)

    # typing mistakes in Gross Sales on 25 rows that aren't duplicated, so the data checks
    # have something to find. Separate RNG so nothing above changes.
    rng2 = np.random.default_rng(SEED + 1)
    candidates = df.index[~df.duplicated(keep=False) & (df["Quantity"] > 0)]
    typo = rng2.choice(candidates, 25, replace=False)
    df.loc[typo, "Gross Sales"] = (df.loc[typo, "Gross Sales"] * 10).round(2)
    return df


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    data = build()
    data.to_csv(OUT, index=False)
    print(f"wrote {OUT} ({len(data):,} rows)")
