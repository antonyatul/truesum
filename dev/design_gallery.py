"""Design system check. Run: streamlit run dev/design_gallery.py  (not deployed)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import plotly.express as px  # noqa: E402
import streamlit as st  # noqa: E402

from smartlytics.ui import components as ui  # noqa: E402
from smartlytics.ui.theme import chart_colors, color  # noqa: E402

st.set_page_config(page_title="Design gallery · Smartlytics", page_icon="assets/favicon.png", layout="wide")
ui.inject_theme()
ui.hero("Smartlytics", "Sales analytics you can explain to your boss.")

st.subheader("Metric cards")
c = st.columns(4)
with c[0]:
    ui.metric("Revenue", "£4,812,330", "100,000 rows")
with c[1]:
    ui.metric("Profit", "£2,830,412", "58.8% margin")
with c[2]:
    ui.metric("High tier", "25.0%", "profit ≥ £412.07")
with c[3]:
    ui.metric("Missing costs", "—", "Map a cost column first")

st.subheader("Tier badges")
st.markdown(" ".join(ui.tier_badge(t) for t in ["High", "Medium", "Low"]), unsafe_allow_html=True)

st.subheader("Buttons")
b = st.columns(4)
b[0].button("Run analysis", type="primary", key="g_primary")
b[1].button("Try sample data", key="g_secondary")
b[2].button("Clear", type="tertiary", key="g_tertiary")
b[3].button("Disabled", disabled=True, key="g_disabled")

st.subheader("Inputs")
i = st.columns(3)
i[0].selectbox("Revenue column", ["revenue", "sales"], key="g_sel", help="Numeric columns only")
i[1].selectbox("Date column", [], key="g_sel_empty", disabled=True, placeholder="No date columns found")
i[2].toggle("Cost is per unit", value=True, key="g_toggle")
st.file_uploader("Upload a CSV or Excel file", type=["csv", "xlsx"], key="g_up",
                 help="Your file stays in this browser session and is never stored.")

st.subheader("Alerts")
st.success("Cleaned: 100,000 → 99,612 rows (388 duplicates removed).")
st.warning("407 rows have no cost, so their profit is left blank rather than guessed.")
st.error("Revenue column must be numeric. ‘region’ contains text.")

st.subheader("Empty state")
ui.empty_state("No charts in your report yet", "Build a chart on the Charts page and choose “Add to report”.")

st.subheader("Step list")
ui.step_list([("Standardised column names", "11 columns · 19:31"),
              ("Removed duplicate rows", "100,000 → 99,612 · 19:31")])

st.subheader("Chart")
rng = np.random.default_rng(1)
df = pd.DataFrame({"profit": rng.gamma(2, 150, 3000)})
fig = px.histogram(df, x="profit", nbins=50, color_discrete_sequence=chart_colors())
q25, q75, mean = df.profit.quantile(.25), df.profit.quantile(.75), df.profit.mean()
for x, name, col in [(q25, "Q25", color("tier-low")), (q75, "Q75", color("tier-high")), (mean, "Mean", color("text"))]:
    fig.add_vline(x=x, line_dash="dash", line_color=col, annotation_text=f"{name} £{x:,.0f}",
                  annotation_font_color=col)
fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color=color("text-muted"),
                  margin=dict(l=8, r=8, t=24, b=8), height=320)
fig.update_xaxes(gridcolor=color("border"))
fig.update_yaxes(gridcolor=color("border"))
st.plotly_chart(fig, use_container_width=True)
st.dataframe(pd.DataFrame({"product": ["Monitor", "Mouse"], "profit": [512.4, 20.9],
                           "tier": ["High", "Low"]}), hide_index=True)
