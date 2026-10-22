# Build log — Smartlytics

All screens built and checked on 2026-10-22 with `tests/e2e/flow.py` at 1440px and
390px: no Streamlit exceptions, no browser console errors, clean server log.
Screenshots in `replica/clone-screens/`.

| ID | screen | status | missing | harder than expected |
| --- | --- | --- | --- | --- |
| S01 | Upload | done | multi-sheet Excel picks the first sheet only | — |
| S06 | No-dataset gate | done | — | — |
| S02 | Overview & clean (incl. S03 summary) | done | — | counting "changed" cells: missing values compared as changed until fixed with a both-missing check |
| S07 | Sales performance (new) | done | — | profit formula needed the per-unit fix (B1); threshold labels collided on the gallery and were staggered |
| — | Customers (split from S02) | done | — | — |
| S04 | Chart builder | done | — | raw histograms shipped every value (1 MB per chart at 100k rows); now pre-binned (~10 KB) |
| S05 | Report & export | done | — | report and CSVs regenerated on every rerun; now built only on click (lazy download) |

## Decisions made during the build

- **Sample data:** the 100,000-row `big_sales_data.csv` was not shipped because its origin
  isn't confirmed. `scripts/make_sample.py` generates an original, deterministic 5,000-row
  dataset with the same shape and deliberate mess (missing costs and products, 40 duplicate
  rows, 12 refunds, inconsistent region casing).
- **Missing numbers stay missing** in the recommended clean. The old Tool filled them with 0,
  which made 407 items free and inflated profit.
- **ID columns** (`customer_id` etc.) are treated as categories, not numbers.
- **Navigation** moved from five buttons to a grouped sidebar with real URLs per page.

## Known limitations

- **Phone sidebar:** on narrow screens Streamlit keeps the sidebar open after choosing a
  page, so it has to be closed by hand. This is Streamlit's behaviour, not something the app
  can override reliably. Revisit if mobile use turns out to matter.
- **Report size:** about 5 MB, almost all of it the embedded Plotly library, so the report
  works offline. A CDN version would be ~200 KB but needs internet to open.
- **Session only:** reloading the browser tab starts over. Accounts and saved datasets are v2.

## Numbers on the original 100k-row file (regression reference)

| measure | old Tool | Smartlytics |
| --- | --- | --- |
| mean profit per row | 488.95 | 283.08 |
| rows rated | 100,000 (missing cost = 0) | 99,593 (407 unknown) |
| clean + analyse time | — | ~3 s |
