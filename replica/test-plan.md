# Test plan — Smartlytics

Flows from `replica/recon.md`. Automation: **U** = pytest unit (`tests/unit`), **A** = Streamlit
AppTest page test (`tests/app`), **E** = Playwright browser (`tests/e2e/flow.py`),
**D** = Postgres RLS test (`tests/db`), **M** = manual.
Payments, email and OAuth don't exist in v1, so their negative cases are out of scope.

## F01 Upload and overview

| ID | case | expected | how |
| --- | --- | --- | --- |
| F01-H1 | upload sample CSV | preview shows 5,040 rows, 11 columns | U, A, E |
| F01-H2 | upload .xlsx | same table as the CSV | U |
| F01-E1 | empty file (0 bytes) | "This file is empty." | U |
| F01-E2 | header row only | "This file has no data rows." | U |
| F01-E3 | semicolon-delimited CSV | columns split correctly | U |
| F01-E4 | Windows-1252 file with £ and accents | reads without error, £ intact | U |
| F01-E5 | emoji and accents in headers and values | kept, escaped in report HTML | U |
| F01-E6 | 60-character column name | displayed, cleaned to snake_case, no crash | U, A |
| F01-E7 | over 250,000 rows | friendly row-limit error | U |
| F01-E8 | wrong extension (.pdf) | "Upload a .csv or .xlsx file." | U |
| F01-E9 | corrupt .xlsx | friendly "couldn't read" error, no traceback | U |
| F01-E10 | upload a second file | everything from the first file is reset | A |
| F01-E11 | refresh mid-flow | starts over (session-only by design) | M |
| F01-E12 | two tabs / two visitors | sessions don't share data | A |
| F01-N1 | open any page with no data | gate with link to Upload | A, E |
| F01-M1 | mobile 390px | usable, no horizontal overflow except tables | E |

## F02 Clean

| ID | case | expected | how |
| --- | --- | --- | --- |
| F02-H1 | recommended clean on sample | 40 duplicates removed, 60 regions merged, dates read, product gaps → Unknown | U, A, E |
| F02-H2 | missing cost stays missing | unit_cost NaN count unchanged | U |
| F02-E1 | double click "Clean" | runs once; button disabled after | A |
| F02-E2 | "£1,200" text amounts | converted to numbers | U |
| F02-E3 | duplicate header names after snake_case | made unique (`x`, `x_2`) | U |
| F02-E4 | fill median on a text column | clear error, data unchanged | U |
| F02-E5 | drop negative rows | refund rows removed and logged | U |
| F02-E6 | undo all cleaning | back to original upload, charts kept | A |
| F02-E7 | clean is pure | input DataFrame not mutated | U |

## F03 Customers

| ID | case | expected | how |
| --- | --- | --- | --- |
| F03-H1 | top customers by revenue | sorted, shares add up | U, A |
| F03-H2 | repeat customers | counts > 1 only; stats correct | U |
| F03-E1 | no repeat customers | empty state | U |
| F03-E2 | numeric customer IDs | treated as categories | U |
| F03-N1 | non-numeric amount | clear error | U |

## F04 Charts

| ID | case | expected | how |
| --- | --- | --- | --- |
| F04-H1 | each chart type on sample | figure built, no exception | U |
| F04-H2 | add to report twice | second time says already added | A |
| F04-E1 | trend with no date column | warning, no crash | U, A |
| F04-E2 | scatter on 100k rows | sampled to 5,000 with a note | U |
| F04-E3 | bar with 40k categories | top 20 with a note | U |
| F04-E4 | correlation with < 2 number columns | ChartError | U |
| F04-E5 | histogram payload stays small | < 50 KB JSON on 100k rows | U |

## F05 Report

| ID | case | expected | how |
| --- | --- | --- | --- |
| F05-H1 | download report | valid HTML with sales, charts, cleaning steps | U, E |
| F05-H2 | report without sales analysis | no sales section, no error | U |
| F05-E1 | malicious dataset name / column `<script>` | escaped in report | U |
| F05-E2 | reorder and remove charts | order changes, removal sticks | A |
| F05-E3 | report opens offline | Plotly JS embedded once | U |

## F06 Sales analysis

| ID | case | expected | how |
| --- | --- | --- | --- |
| F06-H1 | auto mapping on sample | revenue, unit_cost, quantity, per unit | U |
| F06-H2 | profit uses cost × quantity (B1 regression) | matches hand calculation | U |
| F06-H3 | tiers split 25/50/25 | counts and boundaries correct | U |
| F06-E1 | no cost column | rated on revenue with a warning | U |
| F06-E2 | cost is a row total | per-unit off → revenue − cost | U |
| F06-E3 | all values identical | no crash, everything High, documented | U |
| F06-E4 | missing cost | profit unknown, row unrated (B2 regression) | U |
| F06-E5 | per unit chosen but no quantity | validation error, analysis blocked | U, A |
| F06-E6 | same column used twice | validation error | U |
| F06-E7 | original Tool dataset (100k) | mean profit 283.08, 407 unrated | U |
| F06-E8 | clean after analysis | analysis cleared (column names may change) | A |
| F06-N1 | revenue column is text | validation error | U |

## Cross-cutting

| ID | case | how |
| --- | --- | --- |
| X-1 | no browser console errors on any screen | E |
| X-2 | automated accessibility scan (axe) on every screen, no serious/critical issues | E |
| X-3 | keyboard only: complete upload sample → clean → analyse | E |
| X-4 | v2: second user can't read/write first user's rows | D |
