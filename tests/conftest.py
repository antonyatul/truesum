import io as _io
import os
from pathlib import Path

import pandas as pd
import pytest

from truesum.core import cleaning, io, sales

ROOT = Path(__file__).resolve().parents[1]
# Optional regression file: the 100,000-row dataset from the earlier CLI tool. Set REGRESSION_CSV to its path.
ORIGINAL_100K = Path(os.environ.get("REGRESSION_CSV", "/nonexistent"))


@pytest.fixture(scope="session")
def sample_raw() -> pd.DataFrame:
    return io.load_sample()


@pytest.fixture(scope="session")
def sample_clean(sample_raw) -> pd.DataFrame:
    df, _ = cleaning.clean_recommended(sample_raw)
    return df


@pytest.fixture(scope="session")
def sample_result(sample_clean) -> sales.SalesResult:
    return sales.analyse(sample_clean, sales.guess_mapping(sample_clean))


def csv_bytes(df: pd.DataFrame, **kw) -> bytes:
    buf = _io.StringIO()
    df.to_csv(buf, index=False, **kw)
    return buf.getvalue().encode(kw.pop("encoding", "utf-8") if "encoding" in kw else "utf-8")


def tiny_sales() -> pd.DataFrame:
    return pd.DataFrame({
        "revenue": [100.0, 50.0, 200.0, 10.0],
        "unit_cost": [20.0, 10.0, 30.0, None],
        "quantity": [2, 3, 1, 1],
        "customer": ["A", "B", "A", "C"],
    })
