# Pricing — Truesum

**Now:** free public demo, no accounts, no billing.
**Later (product route):** the plan below is a hypothesis to test with real users, not a
decision. Don't create Stripe products until 10 people have used the free version.

## What the alternatives cost (read 2026-10-22)

| product | plan | price | source |
| --- | --- | --- | --- |
| Microsoft 365 (Excel) | Business Basic / Standard | £5.40 / £10.50 per user per month from 1 July 2026 (were £4.60 / £9.40); article doesn't say if VAT is included | [Cloud Switched, 13 Apr 2026](https://cloudswitched.com/news/microsoft-365-price-increase-july-2026-copilot-uk-guide) |
| Power BI | Pro / Premium Per User | $14 / $24 per user per month (2026 list) | [CloudNuro, Aug 2026](https://www.cloudnuro.ai/blog/power-bi-license-cost-2026-pro-ppu-premium-fabric) |
| Julius AI | Free / Plus / Pro | $0 (daily credits) / $20 / $45 per month; 20% off annually | [eesel, edited 5 Oct 2026](https://www.eesel.ai/blog/julius-ai-pricing) |

These are third-party summaries; check each vendor's own pricing page before quoting them
publicly.

## What reviewers said about price

From `feedback.md`: **7 comments across 3 sources** mention cost, mostly disliking
subscriptions (moving Excel to subscription, paid features behind Microsoft 365, an
expensive premium licence). A small theme, but it argues for a free tier that's genuinely
useful on its own and a low, flat price.

## Proposed model

| tier | for | price | what's included |
| --- | --- | --- | --- |
| **Free** | trying it, one-off checks | £0 | everything in today's demo; nothing saved |
| **Owner** | a sole trader or shop owner | £6/month or £60/year (2 months free) | saved datasets, month-on-month comparison, scheduled email of "what stands out" |
| **Team** | a small business, up to 5 people | £18/month flat or £180/year | Owner + shared workspace; flat price, no per-seat jumps |

Billing rules (fixing the complaints up front): one-click cancel in the Stripe Customer Portal;
a reminder email 7 days before an annual renewal; no per-seat charges inside Team; prices shown
with VAT for UK customers.

## Stripe objects to create (you create them, test mode first)

| product | price ID name | amount | interval |
| --- | --- | --- | --- |
| Truesum Owner | `owner_monthly` / `owner_annual` | £6.00 / £60.00 | month / year |
| Truesum Team | `team_monthly` / `team_annual` | £18.00 / £180.00 | month / year |

Env vars are already named in `.env.example` (`STRIPE_PRICE_PRO_MONTHLY` should be renamed to
these when billing is built).
