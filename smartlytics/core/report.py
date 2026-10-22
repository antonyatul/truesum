"""Self-contained HTML report, built in memory (no shared files on disk)."""
from __future__ import annotations

import html
from dataclasses import dataclass
from datetime import UTC, datetime

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from plotly.offline import get_plotlyjs

from smartlytics.core import checks as checks_mod
from smartlytics.core import findings as findings_mod
from smartlytics.core import profile, sales
from smartlytics.core.audit import AuditEntry


@dataclass
class SavedChart:
    title: str
    figure_json: str
    note: str = ""


def _table(df: pd.DataFrame, floatfmt: str = "{:,.2f}") -> str:
    if df.empty:
        return "<p class='muted'>Nothing to show.</p>"
    return df.to_html(index=False, border=0, classes="t", na_rep="—", escape=True,
                      float_format=lambda v: floatfmt.format(v))


def _light(fig_json: str) -> str:
    fig: go.Figure = pio.from_json(fig_json)
    fig.update_layout(template="plotly_white", paper_bgcolor="white", plot_bgcolor="white",
                      font=dict(color="#1f2937"))
    fig.update_xaxes(gridcolor="#e5e7eb", zerolinecolor="#e5e7eb")
    fig.update_yaxes(gridcolor="#e5e7eb", zerolinecolor="#e5e7eb")
    for a in fig.layout.annotations or []:
        a.bgcolor = "rgba(255,255,255,.85)"
    return pio.to_html(fig, full_html=False, include_plotlyjs=False, config={"displaylogo": False})


CSS = """
body{font-family:Inter,system-ui,-apple-system,Segoe UI,sans-serif;color:#111827;margin:0;background:#f8fafc}
main{max-width:1000px;margin:0 auto;padding:32px 20px}
header{background:linear-gradient(135deg,#0A0F2C,#0F2027,#203A43);color:#E7ECF5;border-radius:14px;padding:28px}
header h1{margin:0;font-size:28px}header p{margin:6px 0 0;color:#cbd5e1}
section{background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:20px;margin-top:20px}
h2{font-size:20px;margin:0 0 12px}h3{font-size:16px;margin:20px 0 8px}
.muted{color:#4b5563}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px}
.card{border:1px solid #e5e7eb;border-radius:10px;padding:12px}.card .l{font-size:12px;color:#4b5563;text-transform:uppercase}
.card .v{font-size:22px;font-weight:700;font-variant-numeric:tabular-nums}
table.t{border-collapse:collapse;width:100%;font-size:13px;font-variant-numeric:tabular-nums}
table.t th{background:#0F2027;color:#fff;text-align:left;padding:6px 8px}
table.t td{border-bottom:1px solid #e5e7eb;padding:6px 8px}
ol{padding-left:20px}li{margin:4px 0}footer{color:#6b7280;font-size:12px;margin-top:24px;text-align:center}
@media print{section{break-inside:avoid}}
"""


def build_html(
    dataset_name: str,
    df: pd.DataFrame,
    audit: list[AuditEntry],
    result: sales.SalesResult | None,
    charts: list[SavedChart],
) -> bytes:
    esc = html.escape
    now = datetime.now(UTC).strftime("%d %b %Y, %H:%M UTC")
    ov = profile.overview(df)
    parts = [f"<!doctype html><html lang='en'><head><meta charset='utf-8'>"
             f"<meta name='viewport' content='width=device-width,initial-scale=1'>"
             f"<title>{esc(dataset_name)} · Smartlytics report</title><style>{CSS}</style>"
             f"<script>{get_plotlyjs()}</script></head><body><main>",
             f"<header><h1>{esc(dataset_name)}</h1><p>Smartlytics report · generated {now}</p></header>"]

    cards = [("Rows", f"{ov['rows']:,}"), ("Columns", f"{ov['columns']}"),
             ("Missing cells", f"{ov['missing_pct']:.1f}%"), ("Duplicate rows", f"{ov['duplicate_rows']:,}")]
    parts.append("<section><h2>Dataset</h2><div class='grid'>" + "".join(
        f"<div class='card'><div class='l'>{esc(a)}</div><div class='v'>{esc(b)}</div></div>" for a, b in cards
    ) + "</div><h3>Key observations</h3><ul>" + "".join(f"<li>{esc(x)}</li>" for x in profile.text_summary(df)) + "</ul></section>")

    if result is not None:
        t = result.totals
        sc = [("Revenue", f"{t['revenue']:,.2f}")]
        if result.metric == "profit":
            sc += [("Profit", f"{t['profit']:,.2f}"), ("Margin", f"{t['margin_pct']:.1f}%")]
        sc += [("High-tier rows", f"{t['high_rows']:,}")]
        parts.append("<section><h2>Sales performance</h2><div class='grid'>" + "".join(
            f"<div class='card'><div class='l'>{esc(a)}</div><div class='v'>{esc(b)}</div></div>" for a, b in sc
        ) + "</div>")
        facts = findings_mod.findings(result)
        if facts:
            parts.append("<h3>What stands out</h3><ul>" + "".join(f"<li>{esc(f)}</li>" for f in facts) + "</ul>")
        parts.append(f"<p class='muted'>Rows are rated on {esc(result.metric.replace('_', ' '))}: "
                     "Low below the 25th percentile, High at or above the 75th, Medium between.</p>")
        for w in result.warnings:
            parts.append(f"<p class='muted'>Note: {esc(w)}</p>")
        parts.append("<h3>Tiers</h3>" + _table(sales.tier_summary(result)))
        parts.append("<h3>Tier boundaries</h3>" + _table(sales.threshold_table(result.thresholds))
                     + f"<p class='muted'>{result.thresholds.rated_rows:,} rows rated.</p>")
        top = sales.top_performers(result, 20)
        parts.append("<h3>Top 20 rows</h3>" + _table(top.drop(columns=["tier"])))
        parts.append("</section>")
        found = checks_mod.run_checks(result.df, result.mapping)
        if found:
            parts.append("<section><h2>Data checks</h2><p class='muted'>Rows that don't add up. "
                         "Nothing was changed; these are for a person to judge.</p>"
                         + _table(checks_mod.summary(found)) + "</section>")

    if charts:
        parts.append("<section><h2>Charts</h2>")
        for c in charts:
            parts.append(f"<h3>{esc(c.title)}</h3>{_light(c.figure_json)}")
            if c.note:
                parts.append(f"<p class='muted'>{esc(c.note)}</p>")
        parts.append("</section>")

    parts.append("<section><h2>Missing values</h2>" + _table(profile.missing(df), "{:,.1f}") + "</section>")
    stats = profile.numeric_stats(df)
    if not stats.empty:
        parts.append("<section><h2>Number columns</h2>" + _table(stats.reset_index(names="column")) + "</section>")

    if audit:
        parts.append("<section><h2>Cleaning steps</h2><ol>" + "".join(
            f"<li>{esc(e.message)} <span class='muted'>({esc(e.meta())})</span></li>" for e in audit
        ) + "</ol></section>")

    parts.append("<footer>Made with Smartlytics</footer></main></body></html>")
    return "".join(parts).encode("utf-8")
