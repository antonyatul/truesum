"""Reading uploads and writing exports. No Streamlit imports in core/."""
from __future__ import annotations

import csv
import io
from pathlib import Path

import pandas as pd

MAX_BYTES = 50 * 1024 * 1024
MAX_ROWS = 250_000  # free hosting has ~1 GB shared by all visitors; each session keeps up to 3 copies
SAMPLE_PATH = Path(__file__).resolve().parents[2] / "sample_data" / "sales_sample.csv"


class UploadError(ValueError):
    """A problem with the user's file, worded so it can be shown to them as-is."""


def _decode(data: bytes) -> str:
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise UploadError("We couldn't read the text in this file. Save it as UTF-8 CSV and try again.")


def _sniff_delimiter(text: str) -> str:
    try:
        return csv.Sniffer().sniff(text[:65536], delimiters=",;\t|").delimiter
    except csv.Error:
        return ","


def read_table(data: bytes, name: str) -> pd.DataFrame:
    """Read a CSV or Excel upload into a DataFrame, enforcing size limits."""
    if not data:
        raise UploadError("This file is empty.")
    if len(data) > MAX_BYTES:
        raise UploadError(f"This file is larger than {MAX_BYTES // (1024 * 1024)} MB. Split it or remove unused columns.")

    suffix = Path(name).suffix.lower()
    try:
        if suffix in (".xlsx", ".xlsm"):
            df = pd.read_excel(io.BytesIO(data), sheet_name=0, engine="openpyxl")
        elif suffix in (".csv", ".txt", ".tsv"):
            text = _decode(data)
            df = pd.read_csv(io.StringIO(text), sep=_sniff_delimiter(text), low_memory=False)
        else:
            raise UploadError("Upload a .csv or .xlsx file.")
    except UploadError:
        raise
    except Exception as exc:  # pandas raises many types for malformed files
        raise UploadError(f"We couldn't read this file as a table ({type(exc).__name__}). Check it opens in Excel.") from exc

    df = df.dropna(axis=1, how="all").dropna(axis=0, how="all")
    df.columns = [str(c) for c in df.columns]
    if df.empty or len(df.columns) == 0:
        raise UploadError("This file has no data rows.")
    if len(df) > MAX_ROWS:
        raise UploadError(f"This file has {len(df):,} rows; the limit is {MAX_ROWS:,}.")
    return df.reset_index(drop=True)


def load_sample() -> pd.DataFrame:
    return read_table(SAMPLE_PATH.read_bytes(), SAMPLE_PATH.name)


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")
