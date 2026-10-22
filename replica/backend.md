# Backend — Smartlytics

## v1: public demo (built)

There is no server-side storage by design (architecture.md §1). The "backend" is the
`smartlytics/core` package running inside the Streamlit process; each visitor's data
lives in their own session and is gone when they close the tab.

| area | v1 status |
| --- | --- |
| auth | none needed: no accounts, nothing stored |
| database | none: session memory only |
| payments | none |
| email | none |
| jobs | none |
| integrations | none |

### Security checklist (v1)

- [x] **Secrets:** none exist. `.env*` and `.streamlit/secrets.toml` are git-ignored; `.env.example` lists v2 names with no values.
- [x] **Input validation:** every upload goes through `core.io.read_table`: 50 MB cap (also enforced by Streamlit's `maxUploadSize`), 250,000-row cap, CSV/XLSX only, encoding and delimiter detection, friendly errors.
- [x] **Malicious spreadsheets:** `defusedxml` is installed, so openpyxl parses .xlsx XML safely (no entity expansion or external entities). Verified `openpyxl.DEFUSEDXML is True`.
- [x] **HTML injection:** every user-supplied string rendered as HTML (dataset name, column names, values in the report) goes through `html.escape`; Streamlit markdown elsewhere doesn't render raw HTML.
- [x] **Authorisation:** n/a in v1 (no shared data). For v2 see below — tested.
- [x] **Rate limits:** n/a (no auth, no email). The host limits resources per app.
- [x] **Uploads:** size and type limits as above; files are never written to disk or served back.
- [x] **No user data in URLs or logs:** pages have fixed URLs; the app logs nothing about data. Streamlit usage stats are off (`gatherUsageStats = false`).
- [x] **XSRF / CORS:** left at Streamlit's secure defaults. (The old Hub's dev container turned both off; not carried over.)
- [x] **Dependencies audited:** `pip-audit -r requirements.txt` → no known vulnerabilities (2026-10-22).
- [ ] **Privacy notice:** short in-app line exists ("used in memory for this visit only. Nothing is saved."); a full page listing the host as processor is a launch task.
- [ ] **CSV formula injection:** exports contain the user's own data back to them; cells starting with `=` are not neutralised. Low risk in v1, revisit when files are shared between users in v2.

## v2: accounts and saved datasets (designed, not built)

Build only when the product route is chosen. You create the accounts and keys; Claude
never signs up for services or handles live keys.

| area | plan |
| --- | --- |
| auth | Supabase Auth: email + password with verification, password reset, magic link; Google sign-in with your own Google Cloud OAuth client (basic profile scopes only, so no lengthy Google verification) |
| sessions | Supabase http-only cookies; "sign out everywhere" via Supabase |
| database | `replica/schema.sql` — 8 tables, row level security on all of them |
| files | Supabase Storage bucket `datasets`, path `{user_id}/{dataset_id}/raw.ext`, bucket policy on the first path segment |
| payments | Stripe Checkout for the Pro plan, Customer Portal for changes and one-click cancel; webhook handler idempotent on event id; plan stored in `profiles.plan`, never trusted from the client |
| email | Resend from your own domain (verification, receipts) |
| jobs | nightly cleanup of orphaned storage files; account deletion cascades in the database (tested) |
| hosting change | Streamlit Community Cloud can hold secrets, but a paid product should move to Render or Fly for more memory and a custom domain |

### Tested now

`tests/db/rls_test.sql` applies the real `schema.sql` to Postgres 16 (with a stub of
Supabase's `auth.uid()`), then as a second user checks it **can't read, update,
delete or forge** the first user's rows, that check constraints fire, and that deleting
an account deletes everything it owns. Result: **passed**. The test was also run with
RLS switched off on one table and correctly failed ("B can read A's datasets"), so the
pass is meaningful.

Run it: `PGHOST=… PGUSER=postgres tests/db/run.sh`
