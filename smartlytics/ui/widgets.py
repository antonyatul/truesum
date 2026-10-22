"""Page-level helpers shared by several pages (gate, chart rendering, formatting)."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from smartlytics.core.charts import Built, Style
from smartlytics.core.report import SavedChart
from smartlytics.ui import components as ui
from smartlytics.ui import state
from smartlytics.ui.theme import chart_colors, color


def chart_style() -> Style:
    return Style(palette=chart_colors(), text=color("text-muted"), grid=color("border"),
                 low=color("tier-low"), high=color("tier-high"), mean=color("text"))


def require_data() -> state.AppState:
    s = state.get()
    if not s.has_data:
        ui.empty_state("No data loaded yet", "Upload a spreadsheet or try the sample sales data to get started.")
        st.page_link("pages/home.py", label="Go to Upload", icon=":material/upload_file:")
        st.stop()
    return s


def show_chart(built: Built, key: str, caption: str | None = None) -> None:
    """Render a chart with its note and an 'Add to report' button."""
    st.plotly_chart(built.figure, use_container_width=True, key=f"plot_{key}",
                    config={"displaylogo": False})
    lines = [x for x in (caption, built.note) if x]
    if lines:
        st.caption(" ".join(lines))
    if st.button("Add to report", key=f"save_{key}", icon=":material/note_add:"):
        title = built.figure.layout.title.text or "Chart"
        added = state.get().add_chart(SavedChart(title, built.figure.to_json(), built.note))
        st.toast("Added to your report" if added else "That chart is already in your report",
                 icon=":material/check_circle:" if added else ":material/info:")


def table_config(df: pd.DataFrame) -> dict:
    """Column config: thousands separators for numbers, date-only for dates."""
    cfg = {}
    for col in df.columns:
        s = df[col]
        if pd.api.types.is_datetime64_any_dtype(s):
            cfg[col] = st.column_config.DatetimeColumn(format="YYYY-MM-DD")
        elif pd.api.types.is_integer_dtype(s):
            cfg[col] = st.column_config.NumberColumn(format="localized")
        elif pd.api.types.is_float_dtype(s):
            cfg[col] = st.column_config.NumberColumn(format="%,.2f")
    return cfg


def money(v: float) -> str:
    return "—" if pd.isna(v) else f"{v:,.2f}"


def sidebar_status() -> None:
    s = state.get()
    with st.sidebar:
        if s.has_data:
            st.caption("Current data")
            st.markdown(f"**{s.name}**")
            st.caption(f"{len(s.df):,} rows · {s.df.shape[1]} columns · {'cleaned' if s.cleaned else 'not cleaned yet'}")
            if s.charts:
                st.caption(f"{len(s.charts)} chart(s) in report")
        st.caption("Your data stays in this browser session. Nothing is stored.")
