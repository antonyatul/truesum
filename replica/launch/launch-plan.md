# Launch plan — Truesum

Goal for this launch: a **working public demo and a strong GitHub page** that show data-analyst
skills (cleaning, data quality, analysis, communication, testing) to employers, and **10 real
people trying it** to learn whether the product route is worth building.

## Before launch (this week)

- [ ] **Deploy** to Streamlit Community Cloud (`/replica-deploy`). Live URL in the README hero.
- [ ] **Repo** public as `antonyatul/truesum`; description and topics from `listing.json`; pin it
      on the GitHub profile.
- [ ] **Run the name checks** marked "to run" in `brand.md` (UK IPO first) before buying a domain.
- [ ] **Feedback route:** a GitHub issue template "Something looked wrong in my numbers". No email
      list needed for a demo.
- [ ] **Errors:** Streamlit Cloud shows app logs; check them daily for the first week. No analytics
      script, consistent with the privacy page; Community Cloud's own viewer count is enough.

## Where to share (in this order)

| channel | why | what to post | lead with |
| --- | --- | --- | --- |
| **LinkedIn** | your job search (Data Analyst / BI Analyst, UK-wide, Glasgow, Edinburgh) | post below, with the sales-page screenshot | the profit-formula fix and the data checks |
| **Streamlit forum "Show the Community"** | friendly technical audience, often featured | `listing.json → streamlit_community` | what's under the hood |
| **UK Business Forums** | where 11 of the research comments came from; real UK small-business owners | a short "I built a free tool, would value feedback" post, following the forum's self-promotion rules | data checks and plain English, not the tech |
| **Show HN** | developers who care about data quality | `listing.json → show_hn` | the pre-binned charts and the tests |
| Product Hunt | later, once 10 people have used it and anything confusing is fixed | `listing.json → product_hunt` | — |

No paid ads, no review swaps, no invented numbers.

## LinkedIn post (draft for you to edit)

> I rebuilt two of my old data projects into one app, and found a bug that overstated profit by 73%.
>
> The first was a Streamlit dashboard; the second, a Python pipeline that rated sales as High, Medium
> or Low on profit. While combining them I tested the profit formula against the 100,000-row dataset
> it was built on. It subtracted the unit cost once per row instead of multiplying by quantity, so
> average profit came out at £489 instead of £283, and every tier was wrong.
>
> The result is Truesum: upload a sales spreadsheet and it
> • checks the maths (quantity × price, discounts, missing costs) and flags rows that don't add up
> • rates every sale on profit against your own data
> • says what stands out in plain sentences, worked out with fixed rules rather than AI
> • hands the answers back as an Excel workbook
>
> Behind it: pandas, Plotly, 100+ automated tests, an accessibility scan, and CI on every push.
>
> Free to try, nothing is stored: [live link]
> Code: [GitHub link]
>
> If you work with sales data in spreadsheets, I'd value 5 minutes of feedback on what it gets wrong.
>
> #DataAnalytics #Python #DataQuality #Streamlit

## The first 10 users (talk to them by hand)

Aim for a mix: 4 small-business owners or bookkeepers (shops, trades, online sellers), 3 people
who analyse data at work, 3 classmates or tutors. For each, watch them use it with their own file
if possible and note:

1. Did the column guess get it right? What did they change?
2. Which finding or check made them say "huh"?
3. What did they expect that wasn't there?
4. Would they open it again next month? What would make them?

Write each session into `replica/feedback-users.md`; it replaces internet reviews as the evidence
for the next round of `/replica-entrepreneur`.

## After launch

- Week 1: fix anything that confused two or more people.
- Week 2–3: decide product route or portfolio-only, based on question 4 above.
- If product: run the name checks, build v2 accounts from `schema.sql`, then pricing from `pricing.md`.
