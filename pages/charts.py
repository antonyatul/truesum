"""S04 Chart builder."""
import streamlit as st

from smartlytics.core import charts, profile
from smartlytics.core.charts import ChartError, ChartSpec
from smartlytics.ui import components as ui
from smartlytics.ui.widgets import chart_style, require_data, show_chart

s = require_data()
df = s.result.df if s.result is not None else s.df
st.title("Chart builder")
st.caption("Pick a chart, choose columns, then add it to your report.")

types = profile.column_types(df)
num = [c for c, t in types.items() if t == "numeric"]
preferred = [c for c in ("profit", s.mapping.revenue if s.mapping else None) if c in num]
num = preferred + [c for c in num if c not in preferred]  # most useful measure first
cat = [c for c, t in types.items() if t == "category"]
dates = [c for c, t in types.items() if t == "date"]

KINDS = {
    "bar": ("Bar: compare groups", "Totals or averages per category"),
    "trend": ("Line: change over time", "Needs a date column"),
    "histogram": ("Histogram: spread of values", "How one number is distributed"),
    "scatter": ("Scatter: two numbers", "Does one rise with the other?"),
    "pie": ("Donut: share of a whole", "Best with a handful of groups"),
    "correlation": ("Correlation grid", "Which number columns move together"),
}
kind = st.radio("Chart type", list(KINDS), format_func=lambda k: KINDS[k][0], horizontal=True, key="chart_kind",
                captions=[KINDS[k][1] for k in KINDS])


def need(options: list[str], what: str) -> bool:
    if not options:
        st.warning(f"This chart needs {what}, and none were found. Cleaning may help.", icon=":material/info:")
        return False
    return True


spec = None
a, b, c = st.columns(3)
if kind == "bar" and need(cat, "a text column"):
    x = a.selectbox("Group by", cat, key="bar_x")
    agg = b.selectbox("Measure", ["sum", "mean", "count"], key="bar_agg",
                      format_func={"sum": "Total", "mean": "Average", "count": "Number of rows"}.get)
    y = c.selectbox("Of", num, key="bar_y", disabled=agg == "count") if num else None
    spec = ChartSpec("bar", x=x, y=y, agg=agg)
elif kind == "trend" and need(dates, "a date column") and need(num, "a number column"):
    x = a.selectbox("Date", dates, key="trend_x")
    y = b.selectbox("Value", num, key="trend_y")
    freq = c.selectbox("Per", ["D", "W", "MS"], index=2, key="trend_freq",
                       format_func={"D": "Day", "W": "Week", "MS": "Month"}.get)
    agg = a.selectbox("Measure", ["sum", "mean"], key="trend_agg", format_func={"sum": "Total", "mean": "Average"}.get)
    smooth = b.selectbox("Smoothing line", [0, 3, 5, 7, 12], key="trend_smooth",
                         format_func=lambda n: "None" if n == 0 else f"{n}-period rolling average")
    spec = ChartSpec("trend", x=x, y=y, freq=freq, agg=agg, smooth=smooth)
elif kind == "histogram" and need(num, "a number column"):
    spec = ChartSpec("histogram", x=a.selectbox("Column", num, key="hist_x"))
elif kind == "scatter" and need(num[1:], "two number columns"):
    x = a.selectbox("Across (X)", num, key="sc_x")
    y = b.selectbox("Up (Y)", [n for n in num if n != x], key="sc_y")
    spec = ChartSpec("scatter", x=x, y=y)
elif kind == "pie" and need(cat, "a text column"):
    x = a.selectbox("Slices", cat, key="pie_x")
    y = b.selectbox("Sized by", ["Number of rows"] + num, key="pie_y")
    spec = ChartSpec("pie", x=x, y=None if y == "Number of rows" else y)
elif kind == "correlation":
    spec = ChartSpec("correlation")

if spec is None:
    st.stop()

try:
    built = charts.build(df, spec, chart_style())
except ChartError as err:
    ui.empty_state("Can't draw this chart", str(err))
    st.stop()

show_chart(built, f"builder_{spec.kind}")
