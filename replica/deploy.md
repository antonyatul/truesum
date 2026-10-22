# Deploy — Truesum

Target: **Streamlit Community Cloud**, deploying from GitHub `antonyatul/truesum`, branch
`main`, entry file `app.py`, Python **3.12**. Free, HTTPS included, redeploys on every push.
No secrets, database, payments, OAuth or email in v1, so Step 2 of the deploy guide (production
services) doesn't apply yet.

## 1. Preflight (run 2026-10-22, all in a clean Python 3.12 environment)

| check | command | result |
| --- | --- | --- |
| clean install from `requirements.txt` only | `python3.12 -m venv … && pip install -r requirements.txt` | ✅ streamlit 1.66.1, pandas 3.0.6, plotly 7.1.0 |
| lint | `ruff check .` | ✅ all checks passed |
| colour contrast | `python replica/design/contrast.py replica/design/tokens.json` | ✅ 24/24 AA |
| unit + page tests | `pytest tests/unit tests/app` | ✅ 100 passed, 1 skipped (optional 100k regression file) |
| browser flow, 1440px + 390px | `python tests/e2e/flow.py` | ✅ OK, report 4.9 MB |
| real file uploads (xlsx, broken, unicode, empty) | `python tests/e2e/uploads.py` | ✅ OK |
| accessibility + keyboard-only core loop | `python tests/e2e/a11y.py` | ✅ 0 blocking in our markup; remaining nodes are Streamlit's own nav/toast markup (bugs.md) |
| server log during all browser runs | `grep error/traceback/warning` | ✅ 0 |
| feature parity | `python replica/tools/parity.py replica/features.csv` | ✅ 100%, must-haves 20/20 |
| old-identity sweep | `python replica/tools/sweep.py . --config replica/brand.json` | ✅ clean |
| launch listings | `python replica/tools/listing.py replica/launch/listing.json` | ✅ 0 errors |
| dependency audit | `pip-audit -r requirements.txt` | ✅ no known vulnerabilities |
| v2 row-level security | `tests/db/run.sh` | ✅ passed earlier today (not deployed in v1) |

By hand:

| item | status |
| --- | --- |
| open S1 / S2 bugs | ✅ none (bugs.md) |
| privacy page, naming every processor | ✅ in-app "Privacy & about" names Streamlit Community Cloud as host |
| terms page | not needed for a free, account-less demo; page carries a "not financial or accounting advice" line |
| cookie banner | ✅ not needed: the app sets no non-essential cookies (host's own cookies are covered on the privacy page) |
| account deletion | n/a in v1 (no accounts) |
| favicon, page title, logo | ✅ Truesum (`assets/favicon.png`, page title "Truesum") |
| OG image | made (`assets/og-image.png`); Streamlit Cloud controls the page's meta tags, so use it when posting links on LinkedIn and in the README |
| name screening | ⚠ web checks done; trademark and domain checks **to run** before buying a domain (brand.md). Not a blocker for a free demo on a streamlit.app address |

**Verdict: ready to deploy.**

## 2. Steps

| # | who | step |
| --- | --- | --- |
| 1 | Atul or Claude | Create the **public** repo `antonyatul/truesum` (empty, no README). Claude can do this through the connected GitHub account once you say go. |
| 2 | Claude | Push `main` with its full history. CI starts on the push. |
| 3 | Atul | Go to **share.streamlit.io** → *Create app* → *Deploy a public app from GitHub* → repo `antonyatul/truesum`, branch `main`, main file `app.py`. |
| 4 | Atul | *Advanced settings* → Python **3.12**. No secrets needed. Pick the subdomain, e.g. `truesum.streamlit.app`. Deploy. |
| 5 | Claude | Run the browser flow against the live URL, then put the URL into the README hero and push. |
| 6 | Atul | Open it on your phone and run the sample-data flow once. |

## 3. Domain (later, optional)

Streamlit Community Cloud serves apps on `*.streamlit.app` and doesn't support custom domains.
If a custom domain is wanted later (product route), move hosting to Render or Fly and add, at your
registrar:

| record | name | value |
| --- | --- | --- |
| CNAME | `app` (or `www`) | the host's target, shown in its domain settings |
| TXT | as the host asks | its verification value |

No email DNS needed until v2 sends email (then SPF, DKIM and DMARC `p=none` from the email
provider, tightened to `quarantine` once reports are clean).

## 4. Watch it (first week)

- **Logs:** Streamlit Cloud → app → *Manage app* → logs. Check daily; look for `Traceback` and
  `MemoryError`. Free apps have about 1 GB shared memory: if several 200k-row uploads run at once
  and it restarts, lower `MAX_ROWS` in `truesum/core/io.py`.
- **Sleep:** free apps sleep after a period without visitors and wake on the next visit (a short
  wait). Mention it if you share the link before an interview.
- **Uptime:** optional free check on the app URL (e.g. UptimeRobot) emailing you if it's down.
- **Feedback:** GitHub issues ("Something looked wrong in my numbers" template).
- **No analytics script**, by design (privacy page). Community Cloud's own viewer count is enough.

## Live URL

**https://truesum.streamlit.app/** (deployed 2026-10-22 from `antonyatul/truesum` `main`).

### Checked on the live site (2026-10-22, in the Claude desktop browser at ~800 px)

| check | result |
| --- | --- |
| app loads, Truesum branding and favicon | ✅ |
| sample data → recommended clean → sales analysis | ✅ same totals as local (revenue 1,838,524.11, profit 876,824.33, margin 48.5%) |
| findings and warnings | ✅ shown |
| browser console | only Streamlit Cloud's own calls: `api/v2/user/details` 404 (anonymous visitor) and `api/v1/app/event/open` 403 (its visitor counter). No app errors. |
| **found:** metric numbers broke mid-number at ~800 px | fixed (BUG-11), pushed, tablet width added to the browser test |
