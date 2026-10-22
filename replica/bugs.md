# Bugs — Smartlytics

Only reproduced bugs are listed. Severity: S1 data loss/security/core flow blocked,
S2 feature broken, S3 broken with a workaround or visibly wrong, S4 cosmetic.

## Found and fixed during build (before this test pass)

| ID | sev | summary | fix |
| --- | --- | --- | --- |
| BUG-01 | S1 | Profit ignored quantity (old Tool B1): profit overstated ~73% on the original data, every tier wrong | `sales.compute_profit`; regression test `test_F06_H2`, `test_F06_E7` |
| BUG-02 | S1 | Missing cost filled with 0 (old Tool B2): 407 items treated as free | recommended clean leaves numbers blank; `test_F06_E4`, `test_F02_H2` |
| BUG-03 | S3 | Cleaning log over-counted changes (missing values counted as "changed") | `_changed` helper; `test_trim_counts_only_real_changes` |
| BUG-04 | S3 | Numeric ID columns treated as numbers (charted, summed) | `profile._is_identifier`; `test_identifier_columns_are_categories` |
| BUG-05 | S3 | Histograms shipped every raw value (~1 MB per chart at 100k rows) | pre-binned; `test_F04_E5_histogram_payload_small` |
| BUG-06 | S3 | Report + CSVs rebuilt on every rerun of the Report page | lazy download callables |
| BUG-07 | S3 | Sidebar opened over the content on phones at first load | `initial_sidebar_state="auto"` |
| BUG-08 | S4 | Numbers without thousands separators, dates showing 00:00:00 | `widgets.table_config` |

## Found in this test pass

### BUG-09 · S3 · Primary buttons fail text contrast — fixed
- **Steps:** load the app, look at any primary button (e.g. "Clean with recommended settings").
- **Expected:** text contrast ≥ 4.5:1 (tokens specify `on-accent` #06111F on `accent`, 9.1:1).
- **Actual:** Streamlit draws light text on the accent, ~2:1; axe `color-contrast` (serious) on "Report (HTML)".
- **Evidence:** `tests/e2e/a11y.py` output; computed colour before fix was light.
- **Fix:** CSS in `ui/theme.py` forces `on-accent` on primary and form-submit buttons. Measured after fix: 9.1:1 at rest, 5.1:1 on hover (white text would be 3.7:1 on hover). a11y scan: 0 blocking.

### BUG-10 · S4 · Heading levels skip from h1 to h3 — fixed
- **Steps:** any page; inspect section headings.
- **Actual:** `st.subheader` renders h3 directly under the page h1; axe `heading-order` (moderate).
- **Fix:** sections use `st.header` (h2), restyled to subheading size.

## Upstream (Streamlit's own markup; can't be fixed in the app)

| item | impact | note |
| --- | --- | --- |
| sidebar nav `ul`/`li` structure (axe `list`, `listitem`) | serious per axe | screen readers still announce the links; report upstream to Streamlit |
| toast container without an accessible name (axe `aria-dialog-name`) | serious per axe | toasts are supplementary; every action also changes visible page state |
| sidebar stays open after navigating on phones | S3, workaround: close it | documented in build-log; revisit if mobile matters |

## To check (not reproduced as bugs)

- **CSV formula injection:** exported CSVs return the user's own values unchanged, so a cell starting with `=` stays a formula in Excel. Not a bug in v1 (it's the user's own data); revisit for v2 sharing.
- **Refresh mid-flow** starts over. Intended (session-only), but users may not expect it; the sidebar says data isn't stored. Consider a line on the Upload page.
- **Upload error keeps the previous dataset:** uploading a broken file after a good one shows the error and keeps the earlier data loaded. Reasonable, but the preview heading still names the earlier file, which could confuse.

## Summary

- Cases: 88 automated unit/page tests + 4 upload checks + full browser flow at 1440px and 390px + axe scan of 7 screens + keyboard-only core loop + v2 RLS test.
- Result: all passing. Open bugs: **0 S1, 0 S2, 0 S3 in our code, 0 S4.**
