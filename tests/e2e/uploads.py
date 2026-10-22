"""Real file-uploader checks (AppTest can't drive st.file_uploader).

    python tests/e2e/uploads.py http://localhost:8601
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pandas as pd
from playwright.sync_api import Page, sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8601"
ROOT = Path(__file__).resolve().parents[2]


def settle(page: Page) -> None:
    page.wait_for_timeout(800)
    page.wait_for_function("() => !document.querySelector('[data-testid=\"stStatusWidget\"]')", timeout=30000)
    page.wait_for_timeout(500)


def main() -> int:
    tmp = Path(tempfile.mkdtemp())
    pd.read_csv(ROOT / "sample_data" / "sales_sample.csv").head(300).to_excel(tmp / "sales.xlsx", index=False)
    (tmp / "broken.xlsx").write_bytes(b"PK\x03\x04 not really a workbook")
    (tmp / "données 📊.csv").write_text("région 🌍,montant\nÎle,12\nParis,30\n", encoding="utf-8")
    (tmp / "empty.csv").write_bytes(b"")
    cases = [  # (file, text that must appear)  F01-H2, F01-E9, F01-E5, F01-E1
        ("sales.xlsx", "Preview · sales.xlsx"),
        ("broken.xlsx", "couldn't read this file"),
        ("données 📊.csv", "Preview · données 📊.csv"),
        ("empty.csv", "This file is empty"),
    ]
    problems: list[str] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        page.on("console", lambda m: problems.append(f"console: {m.text}") if m.type == "error" else None)
        page.goto(URL)
        page.get_by_test_id("stApp").wait_for()
        settle(page)
        uploader = page.get_by_test_id("stFileUploaderDropzoneInput")
        for name, expected in cases:
            uploader.set_input_files(str(tmp / name))
            settle(page)
            if not page.get_by_text(expected).count():
                problems.append(f"{name}: expected '{expected}'")
            if page.get_by_test_id("stException").count():
                problems.append(f"{name}: Streamlit exception")
            print(f"checked {name}")
        browser.close()
    for pr in problems:
        print("PROBLEM:", pr)
    print("OK" if not problems else f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
