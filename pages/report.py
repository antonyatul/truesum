"""S05 Report & export."""
import re

import streamlit as st

from smartlytics.core import io, report, sales
from smartlytics.ui import components as ui
from smartlytics.ui.widgets import require_data

s = require_data()
st.title("Report & export")

st.header("Charts in your report")
if not s.charts:
    ui.empty_state("No charts in your report yet",
                   "Use “Add to report” under any chart on the Sales or Chart builder pages.")
else:
    for i, chart in enumerate(list(s.charts)):
        a, b, c, d = st.columns([6, 1, 1, 1])
        a.markdown(f"{i + 1}\\. {chart.title}")
        if b.button("", key=f"up_{i}", icon=":material/arrow_upward:", disabled=i == 0, help="Move up"):
            s.charts[i - 1], s.charts[i] = s.charts[i], s.charts[i - 1]
            st.rerun()
        if c.button("", key=f"down_{i}", icon=":material/arrow_downward:", disabled=i == len(s.charts) - 1, help="Move down"):
            s.charts[i + 1], s.charts[i] = s.charts[i], s.charts[i + 1]
            st.rerun()
        if d.button("", key=f"rm_{i}", icon=":material/delete:", help="Remove from report"):
            s.charts.pop(i)
            st.rerun()

st.header("Download")
include_sales = st.toggle("Include sales performance", value=s.result is not None, disabled=s.result is None,
                          key="inc_sales", help="Run the analysis on the Sales performance page first."
                          if s.result is None else None)

slug = re.sub(r"[^a-z0-9]+", "-", (s.name or "data").lower().rsplit(".", 1)[0]).strip("-") or "data"
a, b, c = st.columns(3)
with a:
    name, df, audit, result, saved = s.name or "Your data", s.df, list(s.audit), s.result if include_sales else None, list(s.charts)
    st.download_button("Report (HTML)", lambda: report.build_html(name, df, audit, result, saved),
                       f"{slug}-report.html", mime="text/html", type="primary",
                       key="dl_report", icon=":material/description:", use_container_width=True)
    st.caption("One file, about 5 MB. Opens in any browser, works offline, prints to PDF.")
with b:
    current = s.df
    st.download_button("Cleaned data (CSV)" if s.cleaned else "Data (CSV)", lambda: io.to_csv_bytes(current),
                       f"{slug}-{'cleaned' if s.cleaned else 'data'}.csv", mime="text/csv",
                       key="dl_clean", icon=":material/table:", use_container_width=True)
    st.caption("Your data after every cleaning step." if s.cleaned else "Not cleaned yet. See Overview & clean.")
with c:
    if s.result is not None:
        tiered = s.result.df
        st.download_button("Data with profit and tiers (CSV)", lambda: io.to_csv_bytes(tiered), f"{slug}-tiers.csv",
                           mime="text/csv", key="dl_tiers", icon=":material/workspace_premium:", use_container_width=True)
        st.caption(f"{len(sales.top_performers(s.result)):,} High-tier rows inside.")
