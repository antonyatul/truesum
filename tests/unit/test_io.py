import io as _io

import pandas as pd
import pytest

from smartlytics.core import io


def test_F01_H1_sample_loads(sample_raw):
    assert sample_raw.shape == (5040, 11)


def test_F01_H2_xlsx_matches_csv(sample_raw):
    buf = _io.BytesIO()
    sample_raw.head(200).to_excel(buf, index=False)
    df = io.read_table(buf.getvalue(), "data.xlsx")
    assert list(df.columns) == list(sample_raw.columns)
    assert len(df) == 200


def test_F01_E1_empty_file():
    with pytest.raises(io.UploadError, match="empty"):
        io.read_table(b"", "x.csv")


def test_F01_E2_header_only():
    with pytest.raises(io.UploadError, match="no data rows"):
        io.read_table(b"a,b,c\n", "x.csv")


def test_F01_E3_semicolon_delimited():
    df = io.read_table(b"product;revenue\nMouse;10.5\nLaptop;900\n", "x.csv")
    assert list(df.columns) == ["product", "revenue"]
    assert df["revenue"].sum() == 910.5


def test_F01_E4_windows_1252_with_pound_sign():
    text = "product,price\nCafé table,£120\n"
    df = io.read_table(text.encode("cp1252"), "x.csv")
    assert df.iloc[0, 0] == "Café table"
    assert df.iloc[0, 1] == "£120"


def test_F01_E5_emoji_and_accents():
    df = io.read_table("région \U0001f30d,v\nÎle \U0001f3dd,1\n".encode(), "x.csv")
    assert df.columns[0] == "région \U0001f30d"
    assert df.iloc[0, 0] == "Île \U0001f3dd"


def test_F01_E6_long_column_name():
    name = "A very long column name that goes on and on for sixty chars!!"
    df = io.read_table(f"{name},b\n1,2\n".encode(), "x.csv")
    assert df.columns[0] == name


def test_F01_E7_row_limit(monkeypatch):
    monkeypatch.setattr(io, "MAX_ROWS", 10)
    data = pd.DataFrame({"a": range(11)}).to_csv(index=False).encode()
    with pytest.raises(io.UploadError, match="limit"):
        io.read_table(data, "x.csv")


def test_size_limit(monkeypatch):
    monkeypatch.setattr(io, "MAX_BYTES", 5)
    with pytest.raises(io.UploadError, match="larger than"):
        io.read_table(b"a,b\n1,2\n", "x.csv")


def test_F01_E8_wrong_extension():
    with pytest.raises(io.UploadError, match=r"\.csv or \.xlsx"):
        io.read_table(b"%PDF-1.4", "report.pdf")


def test_F01_E9_corrupt_xlsx():
    with pytest.raises(io.UploadError, match="couldn't read"):
        io.read_table(b"PK\x03\x04 definitely not a workbook", "broken.xlsx")


def test_blank_rows_and_columns_dropped():
    df = io.read_table(b"a,b,empty\n1,2,\n,,\n3,4,\n", "x.csv")
    assert list(df.columns) == ["a", "b"]
    assert len(df) == 2


def test_csv_roundtrip(sample_raw):
    back = pd.read_csv(_io.BytesIO(io.to_csv_bytes(sample_raw)))
    assert back.shape == sample_raw.shape
