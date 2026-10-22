# Parity — Smartlytics vs its two originals

Originals: **Smartlytics-Hub** `main` @ 5ef845a (run locally with the same sample data)
and **Smart-Data-Analytics-Tool** `main` @ e503840 (CLI, no screens).
Tools: `replica/tools/parity.py`, `replica/tools/imgdiff.py`. Diff images in `replica/diffs/`.

## Scores

| measure | score |
| --- | --- |
| **Feature parity** | **100%** (weighted; 32 scored rows) |
| Must-haves | **20 / 20** |
| Open bugs | 0 S1, 0 S2 |
| Layout, desktop (mean of 6 screens) | 26.8 — different |
| Layout, mobile (mean of 6 screens) | 14.6 — different |

Feature parity is 100% because everything both originals could do is done. That's
not "complete": two *new* ideas (a real AI summary, accounts) are deliberately
not built and are left out of the score because neither original had them.

### Layout per screen

| original screen | clone screen | desktop | mobile | main differences |
| --- | --- | --- | --- | --- |
| S01 upload (empty) | S01 upload | 35 | 13 | sidebar nav replaces five top buttons; compact hero; "what you get" column; sample-data button |
| S01 upload (loaded) | S01 upload | 26 | 10 | clone adds a 20-row preview and next-step links (page 1.4× taller) |
| S02 dashboard (after clean) | S02 overview & clean | 28 | 18 | original shows a crash here (see below); clone adds metric cards, step log, tabs |
| S03 insights | S02 summary tab | 24 | 17 | merged into the overview page |
| S04 visuals | S04 chart builder | 23 | 13 | chart types as labelled options with captions instead of a dropdown |
| S05 reports | S05 report & export | 25 | 17 | chart list with reorder/remove; three downloads |

**Why the layout scores are low, and why that's fine:** the scorer compares where
content sits. The new app intentionally moved navigation into a sidebar, shrank the
hero from every page to the Upload page only, and added content (previews, metrics,
the sales page). Pixel or layout parity with the Hub was never a goal: both apps are
yours, and the Hub's layout was the thing being improved. Colour is ignored by the scorer;
the visible change there is dark theme vs the Hub's default light theme.

## Behaviour differences

| flow | original does | clone does | keep / fix |
| --- | --- | --- | --- |
| F02 clean | **Hub crashes** on "Clean Data Now" with current pandas (`fillna(method=…)` was removed in pandas 3). Reproduced 2026-10-22. | recommended clean runs, every step logged, undo available | keep (fixed) |
| F02 clean | fills gaps by copying neighbouring rows (Hub) or with 0 (Tool) | leaves numbers blank, labels text "Unknown", per-column choice | keep |
| F06 profit tiers | only in the Tool: edit a hard-coded Windows path in `main.py`, run from a terminal, open PNG/CSV files; profit formula wrong | web page: auto-mapped columns, correct profit, tiers, charts, downloads | keep |
| F01 upload | Hub accepts CSV only; any problem shows "Could not read file." | CSV or Excel; specific messages (empty, too big, bad encoding, wrong type) | keep |
| F01 logo | broken-image icon in the hero | logo shows | keep |
| F03 customers | both panels open → duplicate-widget error | separate page, no clash | keep |
| F05 report | written to a shared file on the server; Plotly embedded once per chart (~3.5 MB each) | built in memory per user; Plotly embedded once (~5 MB total) | keep |
| core loop clicks | Hub: upload → Dashboard → Clean (crash) → Visuals → Save → Reports → Generate → Download = **7 clicks, no profit tiers, blocked at clean** | sample → Overview → Clean → Sales → Run analysis → Add to report → Report → Download = **8 clicks including profit tiers** | keep; one extra click buys the whole sales analysis |
| remembered between visits | nothing | nothing | same (v2 adds accounts) |
| phone navigation | top buttons wrap into a column | sidebar must be closed by hand after choosing a page | **fix candidate** (Streamlit limitation) |

## Verdict

**Shippable.** All must-haves done, feature parity 100%, no open S1 or S2 bugs.
"Better than the original" is already true on correctness (profit, cleaning, crashes
fixed); `replica-entrepreneur` should now decide what makes it worth choosing over
a spreadsheet, since that's the real competitor.

## Top five to build next

1. **Phone navigation:** add next/previous page links at the bottom of each page so phone users rarely need the sidebar.
2. **Upload error clarity:** when a new upload fails, say that the previous file is still loaded (to-check item in bugs.md).
3. **"Session only" notice on Upload:** say that refreshing starts over, before people lose work.
4. **Plain-English findings on the Sales page:** e.g. "Laptops make 23% of profit from 6% of orders" — the insight a manager actually wants.
5. **Optional real AI summary** (could-have): needs an API key and a cost decision, so it's a product call for the entrepreneur stage.
