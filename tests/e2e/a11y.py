"""Accessibility scan (axe-core) of every screen, plus a keyboard-only run of the core loop.

    streamlit run app.py --server.headless true --server.port 8601
    AXE_JS=path/to/axe.min.js python tests/e2e/a11y.py http://localhost:8601

Prints every violation; exits 1 on any serious or critical violation in our own UI.
Violations that sit entirely inside Streamlit's own widgets are reported separately,
because the app can't change that markup.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8601"
AXE = Path(os.environ["AXE_JS"]).read_text()
PAGES = ["Upload", "Overview & clean", "Sales performance", "Customers", "Chart builder", "Report & export"]
OURS = ("sl-", "stMarkdown", "stHeading", "stCaption")  # markup the app writes itself


def settle(page: Page) -> None:
    page.wait_for_timeout(500)
    page.wait_for_function("() => !document.querySelector('[data-testid=\"stStatusWidget\"]')", timeout=30000)
    page.wait_for_timeout(500)


def scan(page: Page, label: str) -> list[dict]:
    page.add_script_tag(content=AXE)
    result = page.evaluate("async () => await axe.run(document, {resultTypes: ['violations']})")
    found = []
    for v in result["violations"]:
        for node in v["nodes"]:
            html = node["html"]
            found.append({"screen": label, "rule": v["id"], "impact": v["impact"], "help": v["help"],
                          "ours": any(o in html or o in " ".join(map(str, node["target"])) for o in OURS),
                          "html": html[:140]})
    return found


def keyboard_core_loop(page: Page) -> list[str]:
    """Load sample → clean → run analysis using only Tab/Enter."""
    problems = []

    def press_on(name: str, max_tabs: int = 120) -> bool:
        for _ in range(max_tabs):
            page.keyboard.press("Tab")
            tag, text = page.evaluate(
                "() => { const e = document.activeElement; if (!e) return ['', ''];"
                " return [e.tagName, (e.innerText || e.getAttribute('aria-label') || '').trim()]; }")
            if tag in ("A", "BUTTON", "SUMMARY", "INPUT") and text.endswith(name):
                page.keyboard.press("Enter")
                settle(page)
                return True
        problems.append(f"keyboard: never reached '{name}' by tabbing")
        return False

    page.goto(URL)
    page.get_by_test_id("stApp").wait_for()
    settle(page)
    press_on("Try the sample sales data")
    press_on("Overview & clean")
    press_on("Clean with recommended settings")
    if not page.get_by_text("Recommended clean applied").count():
        problems.append("keyboard: clean did not run")
    press_on("Sales performance")
    press_on("Run analysis")
    if not page.get_by_text("Performance tiers").count():
        problems.append("keyboard: analysis did not run")
    return problems


def main() -> int:
    violations: list[dict] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        page.goto(URL)
        page.get_by_test_id("stApp").wait_for()
        settle(page)
        violations += scan(page, "Upload (empty)")
        page.get_by_role("button", name="Try the sample sales data").click()
        settle(page)
        for label in PAGES:
            page.get_by_test_id("stSidebarNav").get_by_text(label, exact=True).click()
            settle(page)
            if label == "Overview & clean" and page.get_by_role("button", name="Clean with recommended settings").is_enabled():
                page.get_by_role("button", name="Clean with recommended settings").click()
                settle(page)
            if label == "Sales performance":
                page.get_by_role("button", name="Run analysis").click()
                settle(page)
            violations += scan(page, label)
        keyboard = keyboard_core_loop(browser.new_page(viewport={"width": 1440, "height": 1000}))
        browser.close()

    blocking = [v for v in violations if v["ours"] and v["impact"] in ("serious", "critical")]
    print(json.dumps(sorted({(v["rule"], v["impact"], v["ours"]) for v in violations}), indent=0))
    for v in violations:
        print(f"{'OURS ' if v['ours'] else 'st   '} {v['impact']:9} {v['rule']:28} {v['screen']:20} {v['html']}")
    for k in keyboard:
        print("PROBLEM:", k)
    print(f"\n{len(violations)} violation nodes, {len(blocking)} blocking in our markup, keyboard problems: {len(keyboard)}")
    return 1 if blocking or keyboard else 0


if __name__ == "__main__":
    sys.exit(main())
