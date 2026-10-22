# Recon map — Smartlytics (combined app)

Sources: the user's own two repositories. No third-party product is being cloned,
so there are no terms or clean-room limits on reading the code.

| source | commit read | what it gives |
| --- | --- | --- |
| github.com/antonyatul/Smartlytics-Hub (`main`) | 5ef845a | Streamlit web UI: upload, clean, dashboard, insights, charts, HTML report |
| github.com/antonyatul/Smart-Data-Analytics-Tool (`main`) | e503840 | CLI pipeline: OOP processors, sales profit, performance tiers, threshold chart, logging |
| `raw_data/big_sales_data.csv` (100,000 rows) | e503840 | the sample dataset the pipeline was built for |

Note on Smartlytics-Hub branches: `main` is the latest, consolidated single-file app.
`analysis` and `visualization` are earlier side branches whose ideas already live in
`main`, so nothing needs merging.

## 1. Scope (proposed — confirm before architect)

1. **App and platform:** one web app (browser, desktop first, usable on mobile),
   built in Streamlit, in a new repo.
2. **Slice / core loop:** upload a sales spreadsheet → clean it → see profit and
   performance tiers → build charts → export a report.
3. **Who it is for:** both — launch as a free public portfolio demo, structured so
   it can become a product for small businesses later (accounts, pricing).

## 2. What each repo contributes

**Smartlytics-Hub (the shell):** the user-facing product. Generic for any CSV.
Session-only state, no accounts, no persistence.

**Smart-Data-Analytics-Tool (the engine):** a sales-specific analysis pipeline with
a clean class structure (`BaseProcessor` → `Cleaner`, `SalesAnalyzer`), an audit log,
and the profit-tier logic. Has no UI: its `app.py` is empty, and `main.py` only runs
on Windows (hard-coded `C:\Users\...` path and `os.startfile`).

The combined app = Hub's UI and flow + Tool's sales domain logic and audit trail.

## 3. Screen inventory

| ID | screen | how you get there | purpose | key components | states seen |
| --- | --- | --- | --- | --- | --- |
| S01 | Home / Upload | landing, "Home" nav | load a dataset | hero header, file uploader | empty, uploaded (success toast), unreadable file (error) |
| S02 | Dashboard | nav | overview + cleaning | "Clean Data Now" button, stats table, missing-values table, top-customers and repeat-customers panels (column pickers) | raw, cleaned, panels collapsed/expanded |
| S03 | Insights | nav | text summary of dataset | "Generate Summary" button, monospace summary block | not generated, generated |
| S04 | Visuals | nav | build charts, save to report | chart-type select, column selects, Plotly chart, "Save to Report" | chart shown, saved toast, no date column (warning), no numeric/category columns (not handled) |
| S05 | Reports | nav | export | download cleaned CSV, generate + download HTML report | report generated |
| S06 | No-dataset gate | any page except Home with no data | block access | warning banner | shown |
| S07 | Sales analysis (Tool, CLI only today) | `python main.py` | profit, tiers, thresholds, top performers | outputs: cleaned CSV, threshold summary CSV, top performers CSV, 2 PNG charts, logs.txt | success; missing column (crash, not handled) |

S07 has no screen yet; it becomes a new page in the combined app.

## 4. User flows

```
F01 Analyst uploads data and gets an overview
    S01 upload -> S02 dashboard (stats, missing values)
    happy path: 2 clicks (choose file, Dashboard)
    edge: Excel file (uploader only accepts .csv though load_data supports .xlsx),
          unreadable file, very large file

F02 Analyst cleans data
    S02 -> "Clean Data Now" -> cleaned stats
    happy path: 1 click
    edge: forward/back-fill across unrelated rows, numeric coercion of text columns

F03 Analyst finds best and repeat customers
    S02 -> tick panel -> pick customer + amount columns
    happy path: 3-4 clicks
    edge: ticking both panels raises a duplicate-widget error (same "Customer Column" label, no key)

F04 Analyst builds and saves charts
    S04 -> pick chart type -> pick columns -> "Save to Report" (repeat)
    happy path: 3-4 clicks per chart
    edge: no date-like column for Trend Line, no numeric columns

F05 Analyst exports
    S05 -> download cleaned CSV | generate HTML report -> download
    happy path: 2 clicks for the report
    edge: report file written to the server's working directory (collides between users)

F06 Sales manager sees profit and performance tiers (Tool)
    load -> clean column names -> fill missing -> drop negative sales/revenue
    -> profit -> quantile tiers (Low < Q25 <= Medium < Q75 <= High)
    -> threshold summary -> profit histogram with Q25/Q75/mean lines -> top performers
    happy path: 0 clicks today (CLI), target 2 in the combined app
    edge: dataset lacks sales/revenue/cost columns (KeyError crash)
```

## 5. Components

| component | variants / states | used on |
| --- | --- | --- |
| Hero header | with/without logo | all |
| Top nav | 5 tabs, active state not shown visually | all |
| File uploader | idle, uploaded, error | S01 |
| Primary action button | idle, done (toast) | S02, S03, S04, S05 |
| Toast / banner | success, warning, error | all |
| Data table | stats, missing values, ranked list | S02 |
| Column picker (select) | numeric-only, category-only, date-only | S02, S04 |
| Chart | histogram, bar, pie, scatter, correlation heatmap, trend line, profit-threshold histogram (Tool) | S04, S07 |
| Summary block | monospace text | S03 |
| Download button | CSV, HTML | S05 |
| Panel toggle (checkbox) | collapsed, expanded | S02 |

## 6. Inferred data model

Everything lives in the browser session today; nothing is stored.

```
Dataset        id, name, uploaded_at, row_count, column_count, status (raw | cleaned)
               evidence: S01, st.session_state.df          confidence: high
Column         dataset_id, name, dtype (numeric | category | date), missing_count
               evidence: S02 missing table, S04 select_dtypes   confidence: high
CleaningLog    dataset_id, at, message                       (Tool's Logger / logs.txt)
               evidence: logger.py, every processor method       confidence: high
SalesMapping   dataset_id, sales_col, revenue_col, cost_col, quantity_col, date_col, customer_col
               evidence: hard-coded names in cleaner.py/analyzer.py -> needs to become user-mapped
               confidence: medium (guess: required for generic uploads)
TierResult     dataset_id, q25, q75, mean, min, max, row_count, high/medium/low counts
               evidence: export_threshold_summary          confidence: high
SavedChart     report_id, title, type, params, figure_json
               evidence: st.session_state.visuals             confidence: high
Report         id, dataset_id, created_at, sections (overview, stats, missing, insights, charts)
               evidence: generate_html                         confidence: high
```

## 7. Bugs and debts found (fix in build, don't port)

| # | where | issue | evidence |
| --- | --- | --- | --- |
| B1 | Tool `analyzer.py` | Profit = revenue − cost, but `cost` is per unit. Should be revenue − cost × quantity. Overstates mean profit by ~73% (488.95 vs 283.08) and skews every tier | checked on all 100,000 rows: sales = quantity × price on 86% of rows |
| B2 | Tool `cleaner.py` | fills every missing value with 0, so 407 missing costs become free items, 100 missing product names become `0` | `fill_missing_values` |
| B3 | Tool `cleaner.py` / `analyzer.py` | column names hard-coded (`sales`, `revenue`, `cost`); crashes on any other dataset | KeyError path |
| B4 | Tool `main.py` | Windows-only path and `os.startfile` | main.py |
| B5 | Hub `app.py` | two selects with the same label and no key -> DuplicateWidgetID when both customer panels open | lines 237, 245 |
| B6 | Hub `app.py` | `fillna(method=...)` and `to_numeric(errors="ignore")` are deprecated in pandas 2.x | clean_data |
| B7 | Hub `app.py` | logo uses `<img src="logo.png">`, which Streamlit doesn't serve, so it never shows | line 48 |
| B8 | Hub `app.py` | HTML report written to a shared file on disk | generate_html |
| B9 | Hub `requirements.txt` | missing `streamlit`/`pandas`; ships unused heavy deps (fpdf, pmdarima, statsmodels, openai, sqlalchemy) | requirements.txt |
| B10 | Hub "AI Insights" | rule-based `describe()`, not AI. Rename or add a real model call | ai_summary |

## 8. What cannot or should not be carried over

| item | reason |
| --- | --- |
| `big_sales_data.csv` as shipped data | fine as a demo dataset only if you created it; confirm its origin before publishing it |
| "AI" label on the insights page | misleading as built; keep only if a real model is added |
| Windows desktop behaviour (`os.startfile`) | not applicable to a web app |

## 9. Size

- Screens: 7 (6 existing + 1 new sales-analysis page)
- Flows: 6
- Entities: 7
- Hard parts:
  1. Column mapping so the sales engine works on any upload, not just this file
  2. Large files (100k rows works; set and enforce an upload limit)
  3. Report export with embedded charts that stays self-contained and per-user
- Not hard: no realtime, no payments, no third-party integrations unless accounts are added.

**Size: S–M.** A weekend for a solid single-user Streamlit app; a few weeks if it
gets accounts, saved datasets and a separate backend.
