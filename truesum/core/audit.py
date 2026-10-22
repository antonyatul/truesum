"""Audit trail of cleaning and analysis steps (replaces the old Logger/logs.txt)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True)
class AuditEntry:
    step: str
    message: str
    rows_before: int
    rows_after: int
    at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def rows_changed(self) -> int:
        return self.rows_before - self.rows_after

    def meta(self) -> str:
        rows = (
            f"{self.rows_before:,} → {self.rows_after:,} rows"
            if self.rows_before != self.rows_after
            else f"{self.rows_after:,} rows"
        )
        return f"{rows} · {self.at:%H:%M} UTC"
