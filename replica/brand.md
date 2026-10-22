# Brand — Truesum

Angle (from `fixes.md`, option B): for people who run on spreadsheets but aren't
Excel wizards, Truesum turns a sales file into plain-English answers, checks the
maths, and hands back a workbook they can keep in Excel.

## 1. Name

**Chosen by Atul: Truesum** — "the true sum": accurate numbers, said plainly.

### Why the old name had to go
"Smartlytics" is also the name of **Smartlytics Consultancy Ltd**, a data analytics
and Power BI consultancy at Coventry University Tech Park, founded 2016–17 and listed on
the UK government's G-Cloud marketplace. Same name, same field, same country: a
confusion and trademark risk for the product route, and it wins the search results.
Sources: [G-Cloud listing](https://www.applytosupply.digitalmarketplace.service.gov.uk/g-cloud/supplier/707819),
[CB Insights](https://www.cbinsights.com/company/smartlytics),
[The Manifest](https://themanifest.com/company/smartlytics-consultancy).

### 20 candidates
| style | candidates |
| --- | --- |
| descriptive | Sheetsense, Salescheck, Profit Plain, Ledgerlight |
| compound | Tallywise, Sumwise, Marginwise, Rowsight, Tillsight |
| invented | Numbra, Tallo, Quilto, Vardo |
| metaphor | Plumbline, Lantern, Compass, Truesum |
| verb | Tally, Reckon, Sift |

Cut immediately: Reckon (an established accounting software brand), Tally (Tally/TallyPrime
accounting software), Compass and Lantern (generic, crowded), Ledgerlight and Profit Plain
(long), invented names (say nothing about the angle).

### Shortlist and checks
Web checks are searches for "name + app/software/analytics", run **2026-10-22**. They show
what turned up, not that a name is free. All registry and domain checks are **to run**.

| name | web (2026-10-22) | UK IPO | US (USPTO, cl. 9/42) | EUIPO / TMview | WIPO | domain | app stores | handles |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **Truesum** ✔ | no product found | to run | to run | to run | to run | to run | to run | to run |
| Tillsight | no product found | to run | to run | to run | to run | to run | to run | to run |
| Plumbline | "PlumbLine: Level & Plumb" app (spirit level, different field) | to run | to run | to run | to run | to run | to run | to run |
| Tallywise | no exact match; near Tally / TallyPrime accounting brand | to run | to run | to run | to run | to run | to run | to run |
| Smartlytics | **Smartlytics Consultancy Ltd, UK analytics** | to run | to run | to run | to run | to run | to run | to run |
| Sheetsense | ✗ taken: "SheetSense — Spreadsheet Error Detector" Chrome extension | — | — | — | — | — | — | — |
| Sumwise | ✗ taken: Sumwise AI | — | — | — | — | — | — | — |
| Marginwise | ✗ taken: Marginwise Shopify app (margin analytics) | — | — | — | — | — | — | — |
| Rowsight | close to "Rows", an existing spreadsheet product | — | — | — | — | — | — | — |

**Before spending money on the name** (domain, company, paid launch), run the checks above,
starting with the UK IPO (https://trademarks.ipo.gov.uk) in classes 9 and 42. These are
screening checks, not legal clearance: a trademark attorney should do the real search.

## 2. Palette

Kept from the Hub on purpose: both source apps are Atul's own, so there's no one else's
trade dress to move away from, and the navy-to-teal with a cyan-to-green accent carries
his existing work forward. Tokens: `replica/design/tokens.json`. Contrast re-run after the
rebrand: **24/24 pairs pass AA**, plus primary buttons fixed in the test stage (9.1:1 rest,
5.1:1 hover).

## 3. Logo

**Idea:** an equals sign whose lower bar finishes as a tick — "the sum is true".
**Type:** symbol, used alone in the app and with the wordmark on the social image.
**Made:** drawn in code from the tokens (`scripts/make_brand_assets.py`), so it changes when
the palette does.

| deliverable | file | check |
| --- | --- | --- |
| SVG | `assets/logo.svg` (730 bytes) | vector, `role="img"`, labelled |
| app logo | `assets/logo.png` (512) | used in the app header |
| favicon | `assets/favicon.png` (64) | read clearly at 16, 32, 48 px on light and dark |
| app icon | `assets/app-icon.png` (1024, square, no transparency) | iOS-ready |
| social image | `assets/og-image.png` (1200×630) | text fits (the script asserts it) |

**Brief for a designer, if wanted later:** keep the two-bar idea and the tick; try a custom
wordmark in a humanist sans (Inter is the stand-in); the mark must stay legible at 16 px;
don't add a bar chart or magnifying glass (category clichés).

## 4. Voice

| word | means | doesn't mean |
| --- | --- | --- |
| **Plain** | short sentences, everyday words, numbers with context | dumbed down or vague |
| **Careful** | say what we did, what we didn't, and what's uncertain | fussy, hedging everything |
| **Warm** | talk to a busy person who's good at their job | cute, jokey, exclamation marks |

| do | don't |
| --- | --- |
| "50 rows have no cost, so their profit is unknown." | "Oops! Some data is missing 😅" |
| "Laptop earns 23% of profit from 4% of sales." | "Unlock powerful insights into your product performance." |
| "These are for you to judge. Nothing has been changed." | "We've automatically fixed your errors." |
| "Worked out from your data with fixed rules, not guessed by AI." | "AI-powered analytics." |
| "Your file is used in memory for this visit only. Nothing is saved." | "Enterprise-grade security." |

### The 10 most-seen strings, rewritten

| where | before | after |
| --- | --- | --- |
| hero | Turn a sales spreadsheet into profit tiers, charts and a shareable report in minutes. | Your sales spreadsheet, explained in plain English. |
| upload heading | Start with your data | Add your sales file |
| benefits heading | What you get | What you get back |
| benefit 1 | Clean data: tidy headers, merged labels… | The maths, checked: rows where the numbers don't add up, flagged for you to judge |
| benefit 3 | Customers: your biggest spenders… | What stands out, in sentences, not formulas |
| benefit 4 | Charts and a report: one HTML file… | Your answers back in Excel, plus a report you can email or print |
| no-data gate | Upload a spreadsheet or try the sample sales data to get started. | Add a sales file, or try the sample data, and this page fills in. |
| privacy line | Your data stays in this browser session. Nothing is stored. | Your file is used in memory for this visit only. Nothing is saved. |
| checks passed | All 8 checks passed. | All 8 checks passed. The numbers add up. |
| report footer | Made with Smartlytics | Made with Truesum |

## 5. Sweep

`python3 replica/tools/sweep.py . --config replica/brand.json` → **clean**.
The sweep was tested by planting `SmartlyticsHub`, `"Smartlytics Hub"`, `smartlytics_hub` and a
file named `smartlytics_old.txt`; it caught all of them. It also found one real leftover (a
test pointing at the old tool's folder by path), now an optional `REGRESSION_CSV` setting.
Checked by eye: favicon, page title, report title and footer, social image, app icon.
