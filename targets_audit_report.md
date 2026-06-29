# TARGETS Array Audit Report — June 29, 2026

## Executive Summary

Live-tested **every endpoint** in the `TARGETS` array against production APIs. Found **massive attrition** across all platforms, with many companies migrating off Greenhouse/Lever to Ashby, Workday, SmartRecruiters, or proprietary systems.

---

## Platform Breakdown

### ✅ Greenhouse — VERIFIED LIVE (35 boards)
| Company | Board ID | Jobs |
|---------|----------|------|
| Stripe | `stripe` | 490 |
| Groww | `groww` | 17 |
| PhonePe | `phonepe` | 64 |
| Razorpay | `razorpaysoftwareprivatelimited` | 25 |
| Slice | `slice` | 76 |
| Brex | `brex` | 249 |
| Airbnb | `airbnb` | 237 |
| Tower Research Capital | `towerresearchcapital` | 68 |
| AlphaGrep | `alphagrepsecurities` | 17 |
| Databricks | `databricks` | 774 |
| Rubrik | `rubrik` | 105 |
| Cloudflare | `cloudflare` | 215 |
| ClearTax | `clear` (ID CHANGED) | 40 |
| Agoda | `agoda` | 258 |
| DoorDash | `doordashusa` (ID CHANGED) | 446 |
| Twilio | `twilio` | 160 |
| Dropbox | `dropbox` | 51 |
| Anthropic | `anthropic` | 398 |
| Figma | `figma` | 172 |
| Coinbase | `coinbase` | 126 |
| Discord | `discord` | 65 |
| Reddit | `reddit` | 186 |
| Affirm | `affirm` | 163 |
| Robinhood | `robinhood` | 137 |
| Vercel | `vercel` | 75 |
| MongoDB | `mongodb` | 421 |
| Datadog | `datadog` | 416 |
| Elastic | `elastic` | 198 |
| Asana | `asana` | 140 |
| Coursera | `coursera` | 7 |
| Udemy | `udemy` | 7 |
| Netlify | `netlify` | 4 |
| Airtable | `airtable` | 36 |
| Scale AI | `scaleai` | 177 |
| Netskope | `netskope` | 100 |
| Samsara | `samsara` | 330 |
| Duolingo | `duolingo` | 64 |
| Pinterest | `pinterest` | 184 |
| Twitch | `twitch` | 64 |
| Optiver | `optiver` | 0 (valid board, currently empty) |
| Jump Trading | `jumptrading` | 59 |
| Postman | `postman` (MOVED from Lever) | 120 |
| Gong | `gongio` (ID CHANGED) | 98 |
| Apollo GraphQL | `apolloio` (ID CHANGED) | 44 |

### ✅ Ashby — NEWLY DISCOVERED (12 boards)
| Company | Board ID | Jobs | Previous ATS |
|---------|----------|------|-------------|
| OpenAI | `openai` | 721 | Greenhouse |
| Notion | `notion` | 149 | Greenhouse |
| Plaid | `plaid` | 106 | Greenhouse |
| Ramp | `ramp` | 118 | Greenhouse |
| Cohere | `cohere` | 130 | Greenhouse |
| Supabase | `supabase` | 52 | Greenhouse |
| PostHog | `posthog` | 21 | Greenhouse |
| Miro | `miro` | 38 | Greenhouse |
| Confluent | `confluent` | 49 | Greenhouse |
| Checkout.com | `checkout.com` | 207 | Greenhouse |
| Deliveroo | `deliveroo` | 208 | Greenhouse |
| MindTickle | `mindtickle` | 22 (on Lever) | Greenhouse |

### ✅ Lever — VERIFIED LIVE (7 boards)
| Company | Board ID | Jobs |
|---------|----------|------|
| Palantir | `palantir` | 244 |
| Paytm | `paytm` | 225 |
| Meesho | `meesho` | 44 |
| Dream11 | `dreamsports` | 22 |
| Fi Money | `fi` | 10 |
| Zeta | `zeta` | 19 |
| CRED | `cred` | 5 |
| MindTickle | `mindtickle` | 22 |

### ✅ Workday — VERIFIED LIVE (29 portals)
All verified except **Walmart** (HTTP 410 Gone — fully deprecated).

**New Addition:**
| Company | URL | Jobs |
|---------|-----|------|
| BrowserStack | `https://browserstack.wd3.myworkdayjobs.com/External` | 18 |

### ❌ Eightfold — ALL 404 (API deprecated)
Eightfold has locked down their `/api/apply/v2/jobs` endpoint behind OAuth2. **All 17 Eightfold targets** now fail silently. These must be moved to unsupported.

### ❌ Dead Lever Boards (44 boards returning 404)
Massive Indian startup migration off Lever: Revolut, Perfios, PolicyBazaar, BizNext, Jumbotail, Graviton, Swiggy, Zomato, Zepto, Blinkit, Lenskart, Delhivery, Tekion, Unacademy, BharatPe, Spinny, Acko, Navi, Udaan, Khatabook, UpGrad, Whatfix, Jupiter, Smallcase, KreditBee, Cashfree, Instamojo, Open, Signzy, InMobi, Glance, MoEngage, CleverTap, LeadSquared, Amagi, Shiprocket, Locus, GreyOrange, Urban Company, Practo, HealthifyMe, Licious, Vedantu, Apna, Postman (moved to GH), Atlassian (0 jobs).

### ❌ Dead Greenhouse Boards (29 boards returning 404)
Checkoutcom→Ashby, CRED→Lever, Rippling→custom, Upstox→custom, Grab→custom, GoTo→custom, MobiKwik→custom, PineLabs→custom, Wise→custom, Chargebee→custom, Yubi→custom, LendingKart→custom, Quadeye→custom, Cohesity→custom, GitHub→custom, Grammarly→custom, Hasura→custom, HashiCorp→IBM, DigitalOcean→Workable, Hugging Face→custom, Deel→custom, Polygon→custom, Innovaccer→custom, Yelp→custom, TwoSigma→custom, HRT→custom, PayU→custom, Freshworks→SmartRecruiters, BrowserStack→Workday.

---

## Key Issues Fixed
1. **Duplicate Zoom entry** removed (lines 315 & 323)
2. **Duplicate NVIDIA** — kept Workday (live), removed Eightfold (dead)
3. **Duplicate American Express** — kept Workday (live), removed Eightfold (dead)
4. **Postman** moved from dead Lever to live Greenhouse
5. **BrowserStack** moved from dead Greenhouse to live Workday
6. **12 companies** remapped from dead Greenhouse to live Ashby
7. **CRED** remapped from dead Greenhouse to live Lever
8. **MindTickle** remapped from dead Greenhouse to live Lever
9. **ClearTax** board ID fixed: `cleartax` → `clear`
10. **DoorDash** board ID fixed: `doordash` → `doordashusa`
11. **Gong** board ID fixed: `gong` → `gongio`
12. **Apollo GraphQL** board ID fixed: `apollographql` → `apolloio`
13. **Walmart** removed from Workday (API returned 410 Gone)
14. **All Eightfold targets** moved to unsupported (API locked behind OAuth2)
15. **New Ashby scraper** added to the engine
