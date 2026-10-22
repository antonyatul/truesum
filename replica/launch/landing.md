# Landing — Truesum

Built as: `README.md` (the GitHub page is the landing page for a portfolio demo) and the
app's own Upload page. Screenshots are of the real product (`docs/`). No testimonials, user
counts, ratings or logos: there are none yet, so the proof section is the product itself and
the test suite.

| section | copy | where it lives |
| --- | --- | --- |
| Hero | **Your sales spreadsheet, explained in plain English.** Truesum checks the maths, rates every sale on profit, and hands you back a workbook you can keep in Excel. Button: *Try it with sample data* (the live app) | README top; app hero |
| Problem | Two themes from the research, paraphrased: anything past basics needs an expert (22 comments, 4 sources); mistakes are hard to spot (13 comments, 3 sources). | README "The problem" |
| How it works | Add your sales file → clean it with one click → get answers | README; app's three-step order |
| Features (fixes first) | Checks the maths · Plain-English findings · Back to Excel · Honest about limits | README table; app pages |
| Pricing | Free. (Product pricing in `pricing.md` is a plan, not live.) | not shown on the demo |
| FAQ | below | README sections + Privacy & about page |
| Final CTA | *Run it yourself* (3 commands) and the live link | README |

## FAQ (the real objections)

- **Is my data safe?** It's read in memory for your visit only; Truesum writes nothing to disk
  and keeps nothing. The host keeps its own standard logs.
- **Is this AI?** No. The findings and checks are fixed rules you can read in the code. That's
  deliberate: the numbers should be explainable.
- **Can I use my own spreadsheet layout?** Yes, as long as there's a revenue column. Truesum
  guesses which column is which from the headers and lets you change it.
- **Does it replace Excel?** No. It hands the answers back as an Excel workbook.
- **How big a file?** Up to 50 MB and 250,000 rows. 200,000 rows take about 2 seconds.
- **Can I save my work?** Not in the free demo; refreshing starts over. Saved datasets are the
  planned paid version.

Contrast: the README is rendered by GitHub's own theme; the app's colours pass AA (24/24).
