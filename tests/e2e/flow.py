"""End-to-end flow in a real browser. Needs the app running:

    streamlit run app.py --server.headless true --server.port 8601
    python tests/e2e/flow.py http://localhost:8601 replica/clone-screens

Walks the core loop, saves a screenshot per screen at desktop and mobile width,
and exits non-zero on any Streamlit exception or browser console error.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from playwright.sync_api import Page, expect, sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8601"
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else "replica/clone-screens")
OUT.mkdir(parents=True, exist_ok=True)


def settle(page: Page) -> None:
    page.wait_for_timeout(600)
    page.wait_for_function("() => !document.querySelector('[data-testid=\"stStatusWidget\"]')", timeout=30000)
    page.wait_for_timeout(400)


def shot(page: Page, name: str) -> None:
    """Full-length screenshot: Streamlit scrolls inside stMain, so grow the viewport to fit it."""
    size = page.viewport_size
    height = page.evaluate(
        "() => { const m = document.querySelector('[data-testid=\"stMain\"]');"
        " return m ? m.scrollHeight : document.body.scrollHeight; }"
    )
    page.set_viewport_size({"width": size["width"], "height": max(size["height"], min(int(height) + 40, 6000))})
    page.wait_for_timeout(500)
    page.screenshot(path=str(OUT / f"{name}.png"))
    page.set_viewport_size(size)
    page.wait_for_timeout(200)


def nav(page: Page, label: str) -> None:
    page.get_by_test_id("stSidebarNav").get_by_text(label, exact=True).click()
    settle(page)


def check(page: Page, errors: list[str], where: str) -> None:
    exc = page.get_by_test_id("stException")
    if exc.count():
        errors.append(f"{where}: exception: {exc.first.inner_text()[:300]}")


def run(width: int, height: int, suffix: str) -> list[str]:
    errors: list[str] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height}, accept_downloads=True)
        page.on("console", lambda m: errors.append(f"console: {m.text}") if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
        page.goto(URL)
        page.get_by_test_id("stApp").wait_for()
        settle(page)
        mobile = width < 700

        def go(label: str) -> None:
            if mobile and not page.get_by_test_id("stSidebarNav").is_visible():
                page.get_by_test_id("stExpandSidebarButton").click()
                page.wait_for_timeout(400)
            nav(page, label)
            if mobile and page.get_by_test_id("stSidebarNav").is_visible():
                # Streamlit keeps the sidebar open on phones after navigating; close it like a user would
                page.get_by_test_id("stSidebarCollapseButton").click()
                page.wait_for_timeout(400)

        # gate: no data yet
        go("Sales performance")
        expect(page.get_by_text("No data loaded yet")).to_be_visible()
        shot(page, f"S06-gate{suffix}")
        check(page, errors, "S06")

        go("Upload")
        shot(page, f"S01-empty{suffix}")
        page.get_by_role("button", name="Try the sample sales data").click()
        settle(page)
        expect(page.get_by_text("Preview · Sample sales (synthetic)")).to_be_visible()
        shot(page, f"S01-loaded{suffix}")
        check(page, errors, "S01")

        go("Overview & clean")
        expect(page.get_by_text("not cleaned yet").first).to_be_visible()
        page.get_by_role("button", name="Clean with recommended settings").click()
        settle(page)
        expect(page.get_by_text("Recommended clean applied")).to_be_visible()
        expect(page.get_by_text("Removed 40 duplicate rows")).to_be_visible()
        shot(page, f"S02-cleaned{suffix}")
        check(page, errors, "S02")

        go("Sales performance")
        page.get_by_role("button", name="Run analysis").click()
        settle(page)
        expect(page.get_by_text("Performance tiers")).to_be_visible()
        expect(page.get_by_text("50 rows have no cost")).to_be_visible()
        fits = page.evaluate("() => [...document.querySelectorAll('.sl-metric .value')]"
                             ".every(v => v.scrollWidth <= v.clientWidth + 1 && v.getBoundingClientRect().height < 50)")
        if not fits:
            errors.append(f"S07 at {width}px: a metric number overflows or wraps inside its card")
        page.get_by_role("button", name="Add to report").first.click()
        settle(page)
        shot(page, f"S07-sales{suffix}")
        check(page, errors, "S07")

        go("Customers")
        expect(page.get_by_text("Top customers")).to_be_visible()
        shot(page, f"S08-customers{suffix}")
        check(page, errors, "Customers")

        go("Chart builder")
        page.get_by_text("Line: change over time").click()
        settle(page)
        page.get_by_role("button", name="Add to report").click()
        settle(page)
        shot(page, f"S04-charts{suffix}")
        check(page, errors, "S04")

        go("Report & export")
        expect(page.get_by_text("Profit per row, with tier boundaries")).to_be_visible()
        expect(page.get_by_text(re.compile(r"per month \(sum\)"))).to_be_visible()
        with page.expect_download() as dl:
            page.get_by_role("button", name="Report (HTML)").click()
        path = dl.value.path()
        size = Path(path).stat().st_size
        html = Path(path).read_text(encoding="utf-8")
        if "Sales performance" not in html or "Tier boundaries" not in html or size < 1_000_000:
            errors.append(f"report: unexpected content (size {size})")
        shot(page, f"S05-report{suffix}")
        check(page, errors, "S05")
        print(f"[{suffix or 'desktop'}] report {size / 1e6:.1f} MB")
        browser.close()
    return errors


if __name__ == "__main__":
    problems = run(1440, 1000, "") + run(820, 1000, "-tablet") + run(390, 900, "-mobile")
    for p_ in problems:
        print("PROBLEM:", p_)
    print("OK" if not problems else f"{len(problems)} problem(s)")
    sys.exit(1 if problems else 0)
