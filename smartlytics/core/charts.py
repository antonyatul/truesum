"""Chart specs -> Plotly figures. Large data is sampled or aggregated so charts stay fast."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from smartlytics.core.sales import SalesResult, Thresholds

ChartKind = Literal["histogram", "bar", "pie", "scatter", "correlation", "trend"]
SCATTER_MAX = 5000
BAR_MAX = 20
PIE_MAX = 10


class ChartError(ValueError):
    """The chart can't be drawn with these columns; message is shown to the user."""


@dataclass
class Style:
    palette: list[str] = field(default_factory=lambda: ["#22C3EE", "#8EF0A0", "#A78BFA", "#FBBF24", "#F472B6", "#60A5FA"])
    text: str = "#9BA8C2"
    grid: str = "#26324D"
    low: str = "#F87171"
    high: str = "#4ADE80"
    mean: str = "#E7ECF5"
    background: str = "rgba(0,0,0,0)"


@dataclass
class ChartSpec:
    kind: ChartKind
    x: str | None = None
    y: str | None = None
    agg: Literal["sum", "mean", "count"] = "sum"
    freq: Literal["D", "W", "MS"] = "MS"
    smooth: int = 0  # trend only: rolling-average window in periods, 0 = off
    title: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Built:
    figure: go.Figure
    note: str = ""  # e.g. "Showing a random 5,000 of 99,612 points"


def _binned_histogram(values: pd.Series, colour: str, bins: int = 50) -> go.Figure:
    """Histogram from pre-computed bins, so only ~50 bars reach the browser."""
    v = values.dropna().to_numpy(dtype=float)
    if v.size == 0:
        raise ChartError("There are no values to plot.")
    counts, edges = np.histogram(v, bins=bins)
    centres = (edges[:-1] + edges[1:]) / 2
    fig = go.Figure(go.Bar(x=centres, y=counts, width=np.diff(edges), marker_color=colour,
                           customdata=np.stack([edges[:-1], edges[1:]], axis=1),
                           hovertemplate="%{customdata[0]:,.2f} to %{customdata[1]:,.2f}<br>%{y:,} rows<extra></extra>"))
    fig.update_layout(bargap=0.02)
    return fig


def _style(fig: go.Figure, s: Style, title: str, height: int = 380) -> go.Figure:
    fig.update_layout(
        title=dict(text=title[:1].upper() + title[1:], x=0, font=dict(size=15)),
        paper_bgcolor=s.background, plot_bgcolor=s.background, font=dict(color=s.text),
        margin=dict(l=8, r=8, t=48, b=8), height=height, legend_title_text="",
        colorway=s.palette,
    )
    fig.update_xaxes(gridcolor=s.grid, zerolinecolor=s.grid)
    fig.update_yaxes(gridcolor=s.grid, zerolinecolor=s.grid)
    return fig


def _need(df: pd.DataFrame, col: str | None, numeric: bool | None, label: str) -> str:
    if not col or col not in df.columns:
        raise ChartError(f"Choose a column for {label}.")
    if numeric is True and not pd.api.types.is_numeric_dtype(df[col]):
        raise ChartError(f"'{col}' needs to contain numbers for {label}.")
    return col


def build(df: pd.DataFrame, spec: ChartSpec, style: Style | None = None) -> Built:
    s = style or Style()
    k = spec.kind
    note = ""
    if k == "histogram":
        x = _need(df, spec.x, True, "the histogram")
        fig = _binned_histogram(df[x], s.palette[0])
        fig.update_xaxes(title_text=x)
        fig.update_yaxes(title_text="rows")
        title = spec.title or f"Distribution of {x}"
    elif k == "bar":
        x = _need(df, spec.x, None, "categories")
        if spec.agg == "count":
            data = df[x].astype(str).value_counts().rename("rows").reset_index()
            y_label = "rows"
        else:
            y = _need(df, spec.y, True, "values")
            data = df.groupby(df[x].astype(str))[y].agg(spec.agg).sort_values(ascending=False).reset_index()
            y_label = y
        if len(data) > BAR_MAX:
            note = f"Showing the top {BAR_MAX} of {len(data):,} {x} values."
            data = data.head(BAR_MAX)
        fig = px.bar(data, x=x, y=y_label, color_discrete_sequence=s.palette)
        title = spec.title or (f"{spec.agg.title()} of {y_label} by {x}" if spec.agg != "count" else f"Rows by {x}")
    elif k == "pie":
        x = _need(df, spec.x, None, "slices")
        if spec.y:
            y = _need(df, spec.y, True, "slice size")
            data = df.groupby(df[x].astype(str))[y].sum().sort_values(ascending=False)
        else:
            data = df[x].astype(str).value_counts()
        if len(data) > PIE_MAX:
            note = f"The smallest {len(data) - PIE_MAX + 1:,} groups are combined as Other."
            data = pd.concat([data.head(PIE_MAX - 1), pd.Series({"Other": data.iloc[PIE_MAX - 1:].sum()})])
        fig = px.pie(names=data.index, values=data.values, hole=0.45, color_discrete_sequence=s.palette)
        title = spec.title or f"Share by {x}"
    elif k == "scatter":
        x = _need(df, spec.x, True, "the X axis")
        y = _need(df, spec.y, True, "the Y axis")
        data = df[[x, y]].dropna()
        if len(data) > SCATTER_MAX:
            note = f"Showing a random {SCATTER_MAX:,} of {len(data):,} points."
            data = data.sample(SCATTER_MAX, random_state=0)
        fig = px.scatter(data, x=x, y=y, opacity=0.55, color_discrete_sequence=s.palette)
        title = spec.title or f"{y} against {x}"
    elif k == "correlation":
        num = df.select_dtypes("number")
        if num.shape[1] < 2:
            raise ChartError("A correlation chart needs at least two number columns.")
        if num.shape[1] > 15:
            note = "Showing the first 15 number columns."
            num = num.iloc[:, :15]
        corr = num.corr().round(2)
        fig = px.imshow(corr, text_auto=True, zmin=-1, zmax=1, color_continuous_scale=["#F87171", "#121B2E", "#22C3EE"])
        title = spec.title or "How number columns move together"
    elif k == "trend":
        x = _need(df, spec.x, None, "dates")
        if not pd.api.types.is_datetime64_any_dtype(df[x]):
            raise ChartError(f"'{x}' isn't read as a date yet. Run the clean step first.")
        y = _need(df, spec.y, True, "values")
        data = (
            df[[x, y]].dropna().set_index(x)[y].resample(spec.freq).agg(spec.agg if spec.agg != "count" else "size")
        ).reset_index()
        label = {"D": "day", "W": "week", "MS": "month"}[spec.freq]
        fig = px.line(data, x=x, y=y, markers=len(data) <= 60, color_discrete_sequence=s.palette)
        if spec.smooth > 1:
            rolled = data[y].rolling(spec.smooth, min_periods=1).mean()
            fig.data[0].name = y
            fig.data[0].showlegend = True
            fig.add_scatter(x=data[x], y=rolled, mode="lines", name=f"{spec.smooth}-{label} average",
                            line=dict(color=s.palette[1], width=3, dash="dot"))
        title = spec.title or f"{y} per {label} ({spec.agg})"
    else:
        raise ChartError(f"Unknown chart type '{k}'.")
    return Built(_style(fig, s, title), note)


def profit_thresholds(r: SalesResult, style: Style | None = None) -> Built:
    s = style or Style()
    t: Thresholds = r.thresholds
    values = r.df[r.metric].dropna()
    lo, hi = values.quantile(0.005), values.quantile(0.995)
    clipped = values[(values >= lo) & (values <= hi)]
    note = ""
    if len(clipped) < len(values):
        note = f"The most extreme 1% of rows ({len(values) - len(clipped):,}) are left off the chart so the shape is readable."
    fig = _binned_histogram(clipped, s.palette[0], bins=60)
    # labels at three heights so close values never collide
    lines = [(t.q25, "Low / Medium", s.low, 1.0), (t.mean, "Average", s.mean, 0.86), (t.q75, "Medium / High", s.high, 0.72)]
    for x, name, colour, ypos in lines:
        fig.add_vline(x=x, line_dash="dash", line_color=colour, line_width=2)
        fig.add_annotation(x=x, y=ypos, yref="paper", text=f"{name} {x:,.0f}", showarrow=False,
                           xanchor="left", xshift=4, font=dict(color=colour, size=12),
                           bgcolor="rgba(11,18,32,.75)")
    label = r.metric.replace("_", " ")
    fig.update_xaxes(title_text=f"{label} per row")
    fig.update_yaxes(title_text="rows")
    return Built(_style(fig, s, f"{label.title()} per row, with tier boundaries", 400), note)


def sales_vs_profit(r: SalesResult, style: Style | None = None) -> Built:
    if r.metric != "profit":
        raise ChartError("Map a cost column to compare revenue with profit.")
    s = style or Style()
    data = r.df[[r.mapping.revenue, "profit", "tier"]].dropna()
    note = ""
    if len(data) > SCATTER_MAX:
        note = f"Showing a random {SCATTER_MAX:,} of {len(data):,} rows."
        data = data.sample(SCATTER_MAX, random_state=0)
    fig = px.scatter(
        data, x=r.mapping.revenue, y="profit", color="tier", opacity=0.6,
        category_orders={"tier": ["High", "Medium", "Low"]},
        color_discrete_map={"High": s.high, "Medium": s.palette[3], "Low": s.low},
        symbol="tier", symbol_map={"High": "triangle-up", "Medium": "circle", "Low": "triangle-down"},
    )
    return Built(_style(fig, s, "Revenue against profit, by tier"), note)


def breakdown_bar(data: pd.DataFrame, by: str, value: str, style: Style | None = None) -> Built:
    s = style or Style()
    fig = px.bar(data, x=by, y=value, color_discrete_sequence=s.palette)
    return Built(_style(fig, s, f"{value.replace('_', ' ').title()} by {by.replace('_', ' ')}"))
