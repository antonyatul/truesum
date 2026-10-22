"""Typed access to st.session_state. Pages never touch session_state keys directly."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

import pandas as pd
import streamlit as st

from smartlytics.core.audit import AuditEntry
from smartlytics.core.report import SavedChart
from smartlytics.core.sales import SalesMapping, SalesResult

_KEY = "smartlytics"


@dataclass
class AppState:
    name: str | None = None
    raw: pd.DataFrame | None = None
    df: pd.DataFrame | None = None
    cleaned: bool = False
    version: int = 0                     # bumps on every data change; used as a cache key
    loaded_at: datetime | None = None
    audit: list[AuditEntry] = field(default_factory=list)
    mapping: SalesMapping | None = None
    result: SalesResult | None = None
    charts: list[SavedChart] = field(default_factory=list)

    @property
    def has_data(self) -> bool:
        return self.df is not None

    def load(self, name: str, df: pd.DataFrame) -> None:
        self.__init__()  # reset everything for a new dataset
        self.name, self.raw, self.df = name, df, df
        self.loaded_at = datetime.now(UTC)
        self.version = 1

    def replace_data(self, df: pd.DataFrame, entries: list[AuditEntry], cleaned: bool = True) -> None:
        self.df = df
        self.audit.extend(entries)
        self.cleaned = self.cleaned or cleaned
        self.version += 1
        self.mapping, self.result = None, None  # column names may have changed

    def reset_to_original(self) -> None:
        name, raw = self.name, self.raw
        charts = self.charts
        self.load(name, raw)
        self.charts = charts

    def add_chart(self, chart: SavedChart) -> bool:
        if any(c.title == chart.title for c in self.charts):
            return False
        self.charts.append(chart)
        return True


def get() -> AppState:
    if _KEY not in st.session_state:
        st.session_state[_KEY] = AppState()
    return st.session_state[_KEY]
