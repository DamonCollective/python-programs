# Claire's Wigs — Etsy data analysis

## Context
Handmade theatrical/historical/costume wigs. Etsy shop, 5+ years, based in Athens, Greece.
Also sells via own Shopify site and alegro.gr (PrestaShop).

Working file: `Data-analysis.py` (this folder)
Data: Etsy CSV exports, `D:\Downloads\DATA-ETSY`
 - `EtsySoldOrderItems{2020..2026}.csv` — line-item level: Sale Date, Item Name, Price,
   Quantity, Item Total, Discount Amount, Ship Country, Order ID, Transaction ID
 - `EtsySoldOrders{2020..2026}.csv` — order level, buyer country, order totals
 - `EtsyListingsDownload.csv` — full catalog, PRICE + TITLE
 - Sale Date format is `%m/%d/%y`. Revenue = `Item Total`, fall back to `Price * Quantity`.
 - Exports cover sales only. No visits/views/conversion — those live in Etsy Stats.

## Diagnosis established (analysis run 21 Jul 2026)
Two changes made ~20 June 2026:
 1. Flat +$20 on US-market listings under $150 (~30 core items), to offset tariffs
 2. Global switch from "returns accepted" to "no returns" — ALL listings, all markets

Findings from full 2020–2026 order data:
 - ~48% per-day order drop at the 20 June changepoint. Unique to 2026 — 2023, 2024, 2025
   were flat-to-UP across the same calendar window. There is no seasonal summer lull.
 - US −49%/day, non-US −45%/day. Near-identical. Non-US buyers only experienced the
   returns change, not the price increase → returns policy is the primary cause.
 - The +$20 additionally killed the US sub-$100 tier: 25 → 7 orders.
   The $99.90–150 tier held and grew: 5 → 11.
 - Revenue looked flat YoY (~$4,800 for the window) only because AOV nearly doubled,
   $73 → $126. That masked order-count erosion and a shrinking customer base.
 - Coupons were NOT a factor (Germany acquisition campaign + a negotiated pro-buyer
   discount — both deliberate, not panic discounting).
 - True peak season is Sept–Oct Halloween: ~160 orders vs ~60 baseline (~4x).
   July 4th is minor by comparison.
 - Customers order ~45 days before an event: 1–3 weeks production + ~10 days
   Greece→US shipping. So the ordering window opens ~mid-August for Halloween.

## Fixes already applied
 - Returns restored globally, 30-day window, 296 listings (2 remaining no-returns
   listings are digital products — correct as-is)
 - Marquis Renaissance 1700 price typo fixed ($13,990 → $139.90 for US buyers)
 - Shipping profiles assigned to previously unassigned listings
   (Cavaliere Orsini had 21 favorites and zero sales because of this)

## Open work
 - Bootstrapped confidence intervals on total revenue loss from the June changes.
   Point estimate so far is napkin math only (~$3,500–4,500 for the window) — needs
   a real CI, not a guess. This is the next task.
 - Per-item seasonality curves across all years.
 - Price/typo consistency audit across the full catalog.
 - Decide whether to standardize the US surcharge — some mid-price items were never
   given it (e.g. Marie Antoinette at $129.90 everywhere).

## Working preferences
 - No fast-guessing. If the data can't support a statistical claim, say so and label
   estimates as estimates rather than dressing them up.
 - Work one thread at a time. State findings as hypotheses and confirm before building
   on them.
 - Push back when the analysis outruns the evidence.

## Security note
Older scripts in this workspace (alegro.gr PrestaShop batch, March 2026) have admin
URL, email and password hardcoded in plaintext. Move these to environment variables
or a local config that is never synced to cloud storage, and rotate the password.
