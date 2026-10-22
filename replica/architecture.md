# Architecture — Smartlytics

Inputs: `replica/recon.md`, `replica/features.csv`.
Decisions from the user: Streamlit, new repo, free public demo first, built so it
can become a small-business product later.

## 1. Stack

| layer | choice | why |
| --- | --- | --- |
| language | Python 3.12 | both source repos are Python; 3.12 is the newest version Streamlit Community Cloud and every dependency here support well |
| web app | Streamlit 1.66 (multipage via `st.navigation`) | user's chosen stack; reuses existing code; one process, no frontend build |
| data | pandas 3.x | already used; note 3.x removed `fillna(method=)` and `applymap`, both used in the old code |
| charts | Plotly 7 | already used in the Hub; interactive in-app and embeddable in the HTML report. Replaces the Tool's matplotlib |
| Excel | openpyxl | read .xlsx uploads |
| styling | `.streamlit/config.toml` theme + one small CSS block, tokens from replica-design | Streamlit's theming covers most of it |
| storage (v1) | none: `st.session_state` per browser session | a public demo shouldn't keep strangers' data; nothing to secure or delete |
| storage (v2, product) | Postgres on Supabase + Supabase Storage for uploaded files | only when accounts are added; schema in `replica/schema.sql` |
| auth (v2) | Supabase Auth | same vendor as the database; row level security does authorisation |
| payments (v2) | Stripe Checkout | only if the product route goes ahead |
| tests | pytest | the core is plain Python, so it is tested without Streamlit |
| hosting | Streamlit Community Cloud (free, deploys from GitHub `main`) | zero cost, built for exactly this; swap for Render/Fly if v2 needs a database connection pool or more RAM |
| CI | GitHub Actions: ruff + pytest on push | catches breakage before Community Cloud redeploys |

One process, one repo, no microservices.

### The rule that makes v2 possible

All logic lives in `smartlytics/core/`, a package that **never imports streamlit**.
Pages only gather input, call core functions and render results. In v2 the same
core can sit behind a FastAPI service or a background job without rewriting it,
and it is fully unit-testable today.

## 2. Repo layout

```
smartlytics/
  app.py                     entry: page config, theme CSS, st.navigation
  pages/
    home.py                  S01 upload + demo dataset
    overview.py              S02 stats, missing values, cleaning (+ S03 summary)
    sales.py                 S07 column mapping, profit, tiers, top performers
    customers.py             top + repeat customers (split out of S02, fixes B5)
    charts.py                S04 chart builder, save to report
    report.py                S05 downloads
  smartlytics/core/
    io.py                    read CSV/XLSX, size and row limits
    profile.py               column types, stats, missing values, text summary
    cleaning.py              cleaning steps, each returns (df, AuditEntry)
    audit.py                 AuditLog (replaces Tool's Logger / logs.txt)
    sales.py                 SalesMapping, guess_mapping, compute_profit, tiers, top performers
    customers.py             top customers, repeat customers
    charts.py                chart specs -> Plotly figures (incl. profit threshold chart)
    report.py                build self-contained HTML report in memory
  smartlytics/ui/
    state.py                 typed accessors for st.session_state
    components.py            shared widgets (header, empty states, metric cards)
  assets/logo.png
  sample_data/sales_sample.csv   5,000-row demo cut (origin to be confirmed)
  tests/
  .streamlit/config.toml
  requirements.txt           pinned
  .github/workflows/ci.yml
```

## 3. Data model

### v1 (session state, per browser tab)

```
session.dataset        DatasetState: name, df_raw, df, status (raw|cleaned), uploaded_at
session.audit          AuditLog: list[AuditEntry(at, step, message, rows_before, rows_after)]
session.sales_mapping  SalesMapping | None
session.sales_result   SalesResult | None: df with profit + tier, Thresholds(q25, q75, mean, min, max, n)
session.saved_charts   list[SavedChart(title, kind, params, figure_json)]
```

Uploading a new file resets all of it. Nothing is written to disk (fixes B8).

### v2 (Postgres) — see `replica/schema.sql`

8 tables: `profiles`, `datasets`, `dataset_columns`, `audit_entries`,
`sales_mappings`, `tier_results`, `saved_charts`, `reports`.
Every user-owned row carries `user_id`; access is enforced with **Supabase row
level security** (`user_id = auth.uid()`), not in application code. Raw files live
in Supabase Storage under `{user_id}/{dataset_id}`; the table only stores the path.

## 4. Core API (the "routes")

Streamlit has no HTTP routes; the contract is the core package. Every function is
pure (DataFrame in, value out) and called by exactly one page.

### F01 Upload and overview

| function | does | input | output |
| --- | --- | --- | --- |
| `io.read_table(file, name)` | read CSV or XLSX, enforce limits | file-like, name | DataFrame or `UploadError` |
| `io.load_sample()` | load bundled demo data | – | DataFrame |
| `profile.column_types(df)` | numeric / category / date per column | df | dict |
| `profile.summary_stats(df)` | describe(include="all") | df | DataFrame |
| `profile.missing(df)` | missing count and % per column | df | DataFrame |
| `profile.text_summary(df)` | the old "AI insights" text, rule-based | df | str |

### F02 Clean

| function | does | output |
| --- | --- | --- |
| `cleaning.standardise_columns(df)` | trim, lower, snake_case | (df, AuditEntry) |
| `cleaning.trim_text(df)` | strip whitespace in text columns | (df, AuditEntry) |
| `cleaning.coerce_numeric(df)` | convert columns that are ≥95% numeric after removing `,`/`£`/`$` | (df, AuditEntry) |
| `cleaning.fill_missing(df, strategy)` | per-column: drop row, median, mode, constant, leave | (df, AuditEntry) |
| `cleaning.drop_duplicates(df)` | exact duplicates | (df, AuditEntry) |
| `cleaning.drop_negative(df, cols)` | rows with negative values in chosen columns | (df, AuditEntry) |

Default pipeline ("Clean with recommended settings"): standardise → trim → coerce →
drop duplicates → fill missing (numeric: leave for sales fields, median elsewhere;
text: "Unknown"). Never fills cost with 0 (B2).

### F06 Sales analysis

| function | does | output |
| --- | --- | --- |
| `sales.guess_mapping(df)` | match columns by name (`revenue`, `turnover`, `qty`...) | SalesMapping (fields may be None) |
| `sales.validate_mapping(df, m)` | required: revenue, plus cost (with optional quantity, and whether cost is per unit) | list of problems |
| `sales.compute_profit(df, m)` | profit = revenue − cost × quantity when cost is per unit, else revenue − cost; rows missing cost get NaN, not 0 (B1, B2) | df with `profit` |
| `sales.assign_tiers(df)` | Low < Q25 ≤ Medium < Q75 ≤ High | df with `tier`, Thresholds |
| `sales.top_performers(df)` | High tier rows | df |
| `sales.threshold_table(t)` | the Tool's threshold summary | DataFrame |

### F03 Customers

| `customers.top_customers(df, customer_col, amount_col, n=10)` | ranked sum |
| `customers.repeat_customers(df, customer_col)` | customers with >1 row, with counts |

### F04 Charts

| `charts.build(df, ChartSpec)` | histogram, bar (aggregated, not raw rows), pie (top 10 + Other), scatter (sampled to 5k points), correlation, trend (date resampled by day/week/month) | plotly Figure |
| `charts.profit_thresholds(df, t)` | profit histogram + Q25/Q75/mean lines | Figure |
| `charts.sales_vs_profit(df, m)` | scatter | Figure |

### F05 Report

| `report.build_html(dataset, audit, sales_result, saved_charts)` | self-contained HTML, Plotly JS embedded once | bytes |
| `io.to_csv_bytes(df)` | cleaned CSV | bytes |

### Webhooks and jobs

None in v1. v2: a nightly job deleting datasets of deleted accounts (GDPR), Stripe
webhook for subscription status (idempotent on event id).

## 5. The parts that bite

- **File size / memory:** Community Cloud gives ~1 GB RAM. Limit uploads to 50 MB
  and 500,000 rows; read once, keep one cleaned copy plus the raw copy.
- **Plot size:** 100k-point scatter or raw bar charts freeze the browser and bloat the
  report. Sample scatters, aggregate bars, cap pie slices.
- **Report size:** embed Plotly JS once, not per chart (the Hub embeds it per chart:
  ~3.5 MB each).
- **Reruns:** Streamlit reruns the script on every click. Cache pure core calls with
  `st.cache_data` keyed on the DataFrame; give every widget a unique `key` (B5).
- **Dates and time zones:** parse with `errors="coerce"`, treat as naive dates; no
  time-zone logic needed for daily sales.
- **Money:** pandas floats are fine for analysis; display with 2 dp. In v2 store only
  derived summaries, never money as floats in Postgres (integer pence if ever needed).
- **Privacy:** public demo processes data in memory only; say so on the upload page.
  v2 needs a privacy notice and account deletion.
- **Multi-tenancy (v2):** RLS on every table; storage bucket policies by user folder.
- **Messy inputs:** non-UTF-8 CSVs (try utf-8, fall back to latin-1), `;` delimiters
  (sniff), Excel with multiple sheets (first sheet, let user pick in a later version).

## 6. Build order

| milestone | screens | core modules | done when |
| --- | --- | --- | --- |
| M1 vertical slice | S01, S07 | io, cleaning (recommended pipeline), sales | upload sample → profit tiers + threshold chart on screen, correct profit (B1 test passes) |
| M2 must-haves | S01, S02, S06, S07, S04, S05 | profile, audit, charts, report | every `must` row in features.csv works |
| M3 should-haves | + customers page, S03 | customers, text summary | every `should` row works |
| M4 polish + could | all | – | design tokens applied, empty/error states, demo dataset, CI green |
| M5 fixes | – | – | items from replica-entrepreneur |
| v2 (later, separate decision) | + sign in, my datasets | Supabase client | schema.sql applied, RLS verified |

## Summary

- **Stack:** Streamlit + pandas + Plotly, pure-Python core package, pytest, Streamlit
  Community Cloud; Supabase Postgres + Auth reserved for v2.
- **Tables:** 0 in v1 (session only), 8 designed for v2.
- **"Routes":** 26 core functions across 5 flows.
- **Riskiest parts:** memory and chart size on 100k-row files; a column-mapping step
  that is simple enough for non-analysts; keeping the core free of Streamlit so v2 is
  a backend swap, not a rewrite.
- **Next:** `/replica-design`.
