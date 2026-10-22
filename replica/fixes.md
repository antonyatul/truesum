# Fixes and angle — Smartlytics

**Sample:** 92 public comments from 6 sources (Capterra ×50, Software Finder ×20,
UK Business Forums ×11, Hacker News ×8, AccountingWEB ×2, Indie Hackers ×1),
dated 2011–2026; 59 are from the last 18 months. Products discussed: Excel (61),
Power BI (22), a forecasting app and an AI spreadsheet tool (9).
Every row is linked in `replica/reviews.csv`; excerpts there are verbatim and under
15 words, with a paraphrase alongside. Ranking: `replica/feedback.md`.

**Limits of this sample, plainly:** these are general Excel and Power BI users, not
specifically small sales teams, and Capterra reviews skew 5★ (complaints are in
the "cons" field of positive reviews). No source about Smartlytics itself exists yet.
Reddit wasn't reachable from here. Treat ranks as direction, not proof.

## 1. What they hate

| # | problem | comments | sources | example |
| --- | --- | --- | --- | --- |
| 1 | Large files get slow, freeze or crash | 28 | 4 | a sales director says Excel hangs on very large spreadsheets ([Capterra](https://www.capterra.com/p/176574/Excel/reviews/?page=2)) |
| 2 | Anything past basics needs an expert | 22 | 4 | an accounts officer felt Excel expected them to "think like a programmer" ([Capterra](https://www.capterra.com/p/176574/Excel/reviews/?page=3)) |
| 3 | Mistakes are hard to spot or trace | 13 | 3 | small firms end up with messy spreadsheet models ([HN](https://news.ycombinator.com/item?id=2925276)) |
| 4 | Building reports and the right metrics is hard work | 12 | 4 | Power BI users: right metrics hard, detailed reports need technical knowledge ([Software Finder](https://softwarefinder.com/analytics-software/microsoft-power-bi/reviews?page=42)) |
| 5 | Sharing and handing over work | 10 | 4 | Python analysis is hard to hand over without a developer ([UK Business Forums](https://www.ukbusinessforums.co.uk/threads/i-am-interested-in-learning-how-small-businesses-use-data-and-tools-like-excel.399271/post-2944037)) |
| 6 | Mobile and web versions are weak | 10 | 2 | thin on sources (two) |
| 7 | Subscription cost | 7 | 3 | |

## 2. What is missing (asked for by name)

| request | comments | sources | note |
| --- | --- | --- | --- |
| Guidance on which formula/chart to use, possibly AI help | 3 | 2 | thin |
| Start from my real numbers, add data over time | 2 | 1 | thin (HN, 2011) |
| Line charts / trends | 1 | 1 | thin; already built |

## 3. What is unsolved

| job / group | evidence |
| --- | --- |
| **People who like Excel and won't leave it.** Half the UK small-business replies are content with Excel; one tried a dedicated tool and went back. | 6 of 11 UK Business Forums replies; 3 Capterra "no cons" |
| **"Not an Excel wizard" owners who still need answers.** | learning-curve theme, 22 comments, 4 sources |
| **AI spreadsheet tools are hard to tell apart from a general chatbot.** | 1 comment (thin), Indie Hackers 2025 |

## Fix plan

| # | fix | evidence | size | status |
| --- | --- | --- | --- | --- |
| X1 | **Plain-English findings** at the top of Sales performance: "Laptops earn 28% of profit from 9% of rows", "12 refunds", "top 10 customers = 31% of revenue". No formulas, no chart reading needed. | learning curve (22/4), reports hard (12/4), guidance (6/4) | M | done |
| X2 | **Data checks**: test the maths in the file — gross ≠ quantity × price, revenue above gross, discounts outside 0–100%, negative quantities, dates in the future — with counts and the rows to download. | errors hard to trace (13/3), can't trust numbers (5/3) | M | done |
| X3 | **Excel workbook download**: one .xlsx with Summary, Tiers, Top performers, Data checks and the cleaned data, so people take the answers back into Excel. | unsolved #1, handover (10/4) | S | done |
| X4 | **Next-step links** at the foot of every page, so phone users rarely need the sidebar. | mobile (10/2, thin); known phone-sidebar issue | S | done |
| X5 | **Speed and limits stated honestly** on Upload ("250,000 rows; 200,000 rows clean and analyse in about 2 seconds"). Measured, not guessed. | slow/crash (28/4) | S | done |
| X6 | **Session-only notice + clearer failed-upload message** | bugs.md to-check | S | done |
| X7 | Optional AI narrative (could) | guidance (thin) + unsolved #3 (thin) | M | not now: thin evidence, needs an API key and cost decision |

## The angle

**A.** For small business owners whose spreadsheets slow down and hide mistakes,
Smartlytics checks the maths and rates every sale in seconds.
Evidence: slow (28 comments, 4 sources) + errors (13, 3).

**B. (recommended)** For people who run on spreadsheets but aren't Excel wizards,
Smartlytics turns a sales file into plain-English answers (which sales make money,
which don't, and what looks wrong) and hands back a workbook you can keep in Excel.
Evidence: learning curve (22 comments, 4 sources) + errors (13, 3) + the
"happy with Excel" group (9 comments, 2 sources).

**C.** For analysts who keep rebuilding the same sales report, one upload gives
profit tiers, charts and a shareable report. Evidence: reports hard work (12, 4).

**Why B:** it's the largest pain the app can honestly fix (we can't make Excel faster,
but we can remove the formulas), it makes Excel an ally rather than an enemy, and
for a portfolio it shows judgement as well as code: data quality checks, plain
language, a clear user.
