#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
organize_data.py  -  ClairesWigs / Etsy data organizer
=======================================================

Companion to Data-analysis.py. Where that script is the "laboratory" for
testing hypotheses, this one is the "organizer": it reads every file in the
export folder, tells you plainly what is and isn't usable, and produces two
on-demand full lists:

    1. customers  - every customer: name, address, order history, what they
                    bought, when, total spent. (No email/phone: Etsy's bulk
                    CSV exports do not include them - see LIMITATIONS below.)
    2. products   - every item ever sold, ranked by units/revenue, plus which
                    ones sold well and then stopped selling.
    3. halloween  - per-item Sep-Oct historical demand (mean, std dev, years
                    observed), to plan what to have pre-made before the
                    mid-August ordering window opens.

LIMITATIONS (read this before trusting the customer list)
-----------------------------------------------------------------------------
Etsy's "Sold Orders" / "Sold Order Items" CSV exports do NOT contain buyer
email or phone number, at any point in the 2020-2026 history checked. This is
an Etsy privacy restriction on bulk exports, not a bug in this script. The
customer list below has: name, full shipping address, order dates, items
bought, quantities, amounts. If you need email/phone for a specific buyer,
that only exists in that buyer's individual message thread / order page in
Etsy Shop Manager, one at a time.

Some buyers have no "Buyer User ID" (Etsy shows this for registered accounts
only, not guest checkouts). Those are grouped by name+zipcode instead, so a
guest who orders twice with the same name/zip is still counted as one
customer; a genuine one-off guest is not falsely merged with unrelated
buyers.

Usage
-----
    python organize_data.py catalog       # what's in the data folder, what's junk
    python organize_data.py customers     # full customer list -> CSV
    python organize_data.py products      # best sellers + stopped-selling items -> CSV
    python organize_data.py halloween     # Sep-Oct per-item demand stats -> CSV
    python organize_data.py all           # everything above

Add  --data-dir "PATH"  to point at a different export folder.
Output goes to <data-dir>/organized_output/
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import os
import sys
from datetime import timedelta

import pandas as pd

DEFAULT_DATA_DIR = r"D:\Downloads\DATA-ETSY"
OUTPUT_SUBDIR = "organized_output"
STOPPED_SELLING_DAYS = 180   # no sale in this many days -> "stopped selling"

pd.set_option("display.width", 160)
pd.set_option("display.max_columns", 40)


# --------------------------------------------------------------------------- #
# Low-level helpers (same conventions as Data-analysis.py)
# --------------------------------------------------------------------------- #

def _read_csv(path: str) -> pd.DataFrame:
    try:
        return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8")
    except UnicodeDecodeError:
        return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="latin-1")


def _to_num(series: pd.Series) -> pd.Series:
    cleaned = (
        series.astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("$", "", regex=False)
        .str.strip()
        .replace({"": None})
    )
    return pd.to_numeric(cleaned, errors="coerce")


def _to_date(series: pd.Series, fmt: str | None = None) -> pd.Series:
    if fmt:
        return pd.to_datetime(series, format=fmt, errors="coerce")
    return pd.to_datetime(series, errors="coerce")


def _md5(path: str) -> str:
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# --------------------------------------------------------------------------- #
# 1. File discovery / catalog
# --------------------------------------------------------------------------- #

# Known Etsy export patterns and what they're for. Anything in the folder
# that doesn't match one of these is flagged, not silently ignored.
KNOWN_PATTERNS = {
    "orders":          "EtsySoldOrders20*.csv",
    "order_items":     "EtsySoldOrderItems20*.csv",
    "deposits":        "EtsyDeposits20*.csv",
    "checkout_payments": "EtsyDirectCheckoutPayments20*.csv",
    "listings":        "EtsyListingsDownload.csv",
    "reviews":         "reviews.json",
    "shop_settings":   "shop_settings.json",
}


def discover(data_dir: str) -> dict:
    """Classify every file in data_dir. Returns a catalog dict for reporting."""
    all_files = sorted(
        f for f in glob.glob(os.path.join(data_dir, "*"))
        if os.path.isfile(f) and os.path.basename(f) != OUTPUT_SUBDIR
    )
    claimed = set()
    by_kind = {}
    for kind, pattern in KNOWN_PATTERNS.items():
        matches = sorted(glob.glob(os.path.join(data_dir, pattern)))
        by_kind[kind] = matches
        claimed.update(matches)

    # duplicate detection: same basename pattern with "(1)" etc., or identical
    # content under a different name (Etsy re-download artifacts)
    hashes: dict[str, list[str]] = {}
    for f in claimed:
        hashes.setdefault(_md5(f), []).append(f)
    duplicate_groups = [v for v in hashes.values() if len(v) > 1]

    unclaimed = [f for f in all_files if f not in claimed]
    return {
        "by_kind": by_kind,
        "duplicate_groups": duplicate_groups,
        "unclaimed": unclaimed,
    }


def print_catalog(data_dir: str, cat: dict) -> None:
    print("=" * 78)
    print(f"DATA CATALOG  -  {data_dir}")
    print("=" * 78)
    for kind, files in cat["by_kind"].items():
        print(f"\n[{kind}]  {len(files)} file(s)")
        for f in files:
            size = os.path.getsize(f)
            print(f"   {os.path.basename(f):40s} {size:>10,} bytes")

    if cat["duplicate_groups"]:
        print("\n[duplicates found - byte-identical content, safe to ignore the extra copy]")
        for g in cat["duplicate_groups"]:
            print("   " + "  ==  ".join(os.path.basename(f) for f in g))

    if cat["unclaimed"]:
        print("\n[NOT RECOGNIZED - not loaded, check manually]")
        for f in cat["unclaimed"]:
            size = os.path.getsize(f)
            note = ""
            head = ""
            try:
                with open(f, "rb") as fh:
                    head = fh.read(200).decode("utf-8", "replace")
            except Exception:
                pass
            if head.strip().startswith("<!DOCTYPE") or head.strip().startswith("<html"):
                note = "  (raw HTML page shell, not exported data - dynamic Etsy stats pages save like this)"
            elif size == 0:
                note = "  (empty file)"
            elif "PS C:\\" in head or "PowerShell" in head:
                note = "  (looks like a saved terminal/PowerShell transcript, not Etsy data - probably misfiled)"
            print(f"   {os.path.basename(f):40s} {size:>10,} bytes{note}")
    print()


# --------------------------------------------------------------------------- #
# 2. Clean loaders
# --------------------------------------------------------------------------- #

def load_orders(files: list[str]) -> pd.DataFrame:
    frames = [_read_csv(f) for f in files]
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True, sort=False)
    df = df.drop_duplicates(subset=["Order ID"], keep="first")
    df["date"] = _to_date(df.get("Sale Date"), "%m/%d/%y")
    df["order_value"] = _to_num(df.get("Order Value"))
    df["order_total"] = _to_num(df.get("Order Total"))
    df["shipping"] = _to_num(df.get("Shipping"))
    df["discount"] = _to_num(df.get("Discount Amount"))
    df["buyer_id"] = df.get("Buyer User ID", "").str.strip()
    df["full_name"] = df.get("Full Name", "").str.strip()
    df["street1"] = df.get("Street 1", "").str.strip()
    df["street2"] = df.get("Street 2", "").str.strip()
    df["city"] = df.get("Ship City", "").str.strip()
    df["state"] = df.get("Ship State", "").str.strip()
    df["zipcode"] = df.get("Ship Zipcode", "").str.strip()
    df["country"] = df.get("Ship Country", "").str.strip()
    # customer key: registered buyer id when we have it, else name+zip
    df["customer_key"] = df["buyer_id"].where(
        df["buyer_id"] != "",
        (df["full_name"].str.lower() + "::" + df["zipcode"].str.lower()),
    )
    return df[df["date"].notna()].sort_values("date").reset_index(drop=True)


def load_items(files: list[str]) -> pd.DataFrame:
    frames = [_read_csv(f) for f in files]
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True, sort=False)
    df = df.drop_duplicates(subset=["Transaction ID"], keep="first")
    df["date"] = _to_date(df.get("Sale Date"), "%m/%d/%y")
    df["qty"] = _to_num(df.get("Quantity"))
    df["price"] = _to_num(df.get("Price"))
    df["item_total"] = _to_num(df.get("Item Total"))
    df["listing_id"] = df.get("Listing ID", "").str.strip()
    df["item_name"] = df.get("Item Name", "").str.strip()
    df["order_id"] = df.get("Order ID", "").str.strip()
    return df[df["date"].notna()].sort_values("date").reset_index(drop=True)


def load_deposits(files: list[str]) -> pd.DataFrame:
    frames = [_read_csv(f) for f in files]
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True, sort=False)
    df["amount"] = _to_num(df.get("Amount"))
    df["date"] = _to_date(df.get("Date"))
    df = df.drop_duplicates(subset=["Date", "Amount", "Bank Account Ending Digits"])
    return df[df["date"].notna()].sort_values("date").reset_index(drop=True)


def load_checkout_payments(files: list[str]) -> pd.DataFrame:
    frames = [_read_csv(f) for f in files]
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True, sort=False)
    df = df.drop_duplicates(subset=["Payment ID"], keep="first")
    for col in ["Gross Amount", "Fees", "Net Amount", "VAT Amount", "Refund Amount"]:
        if col in df:
            df[col.lower().replace(" ", "_")] = _to_num(df[col])
    df["order_id"] = df.get("Order ID", "").str.strip()
    return df


def load_listings(path: str | None) -> pd.DataFrame:
    if not path or not os.path.isfile(path):
        return pd.DataFrame()
    df = _read_csv(path)
    df["price"] = _to_num(df.get("PRICE"))
    return df


# --------------------------------------------------------------------------- #
# 3. Customer list  (the "who bought what, when" full list)
# --------------------------------------------------------------------------- #

def build_customer_detail(orders: pd.DataFrame, items: pd.DataFrame) -> pd.DataFrame:
    """One row per item purchased, with full customer/address info attached."""
    if orders.empty or items.empty:
        return pd.DataFrame()
    cust_cols = ["Order ID", "customer_key", "buyer_id", "full_name",
                 "street1", "street2", "city", "state", "zipcode", "country"]
    o = orders[[c for c in cust_cols if c in orders.columns]].copy()
    o = o.rename(columns={"Order ID": "order_id"})
    it = items[["order_id", "date", "item_name", "qty", "price", "item_total",
                "listing_id"]].copy()
    it = it.rename(columns={"date": "purchase_date"})
    merged = it.merge(o, on="order_id", how="left")
    cols = ["customer_key", "full_name", "buyer_id", "street1", "street2",
            "city", "state", "zipcode", "country", "order_id", "purchase_date",
            "item_name", "qty", "price", "item_total", "listing_id"]
    merged = merged[cols].sort_values(["customer_key", "purchase_date"])
    return merged.reset_index(drop=True)


def build_customer_summary(detail: pd.DataFrame) -> pd.DataFrame:
    """One row per customer: address + order history rollup."""
    if detail.empty:
        return pd.DataFrame()
    g = detail.groupby("customer_key")
    summary = pd.DataFrame({
        "full_name": g["full_name"].first(),
        "street1": g["street1"].first(),
        "street2": g["street2"].first(),
        "city": g["city"].first(),
        "state": g["state"].first(),
        "zipcode": g["zipcode"].first(),
        "country": g["country"].first(),
        "first_order": g["purchase_date"].min(),
        "last_order": g["purchase_date"].max(),
        "n_orders": g["order_id"].nunique(),
        "n_items": g["qty"].sum(),
        "total_spent": g["item_total"].sum(),
        "items_bought": g["item_name"].apply(lambda s: "; ".join(sorted(set(s)))),
    })
    return summary.sort_values("total_spent", ascending=False).reset_index()


def run_customers(data_dir: str, orders: pd.DataFrame, items: pd.DataFrame, out_dir: str) -> None:
    detail = build_customer_detail(orders, items)
    summary = build_customer_summary(detail)
    if detail.empty:
        print("No order/item data loaded - nothing to build a customer list from.")
        return

    detail_path = os.path.join(out_dir, "customers_full_detail.csv")
    summary_path = os.path.join(out_dir, "customers_summary.csv")
    detail.to_csv(detail_path, index=False, encoding="utf-8-sig")
    summary.to_csv(summary_path, index=False, encoding="utf-8-sig")

    print("=" * 78)
    print("CUSTOMER LIST")
    print("=" * 78)
    print("NOTE: no email or phone number in this list - Etsy's bulk order CSV")
    print("exports never include buyer contact info, only name + shipping address.")
    print(f"\nUnique customers: {len(summary):,}")
    print(f"Total line-item purchases: {len(detail):,}")
    print(f"\nWrote full detail (1 row per item bought)  -> {detail_path}")
    print(f"Wrote per-customer summary (1 row per buyer) -> {summary_path}")
    print("\nTop 10 customers by total spent:")
    print(summary.head(10)[["full_name", "city", "country", "n_orders",
                             "n_items", "total_spent"]].to_string(index=False))


# --------------------------------------------------------------------------- #
# 4. Product performance  (best sellers + items that stopped selling)
# --------------------------------------------------------------------------- #

def build_product_table(items: pd.DataFrame) -> pd.DataFrame:
    if items.empty:
        return pd.DataFrame()
    ref = items["date"].max()
    cutoff = ref - timedelta(days=STOPPED_SELLING_DAYS)
    g = items.groupby("listing_id")
    prod = pd.DataFrame({
        "name": g["item_name"].last(),
        "first_sale": g["date"].min(),
        "last_sale": g["date"].max(),
        "units_sold": g["qty"].sum(),
        "revenue": g["item_total"].sum(),
        "orders": g["order_id"].nunique(),
    })
    prod["days_since_last_sale"] = (ref - prod["last_sale"]).dt.days
    prod["status"] = prod["last_sale"].apply(
        lambda d: "STOPPED SELLING" if d < cutoff else "ACTIVE")
    return prod.sort_values("revenue", ascending=False).reset_index()


def run_products(items: pd.DataFrame, out_dir: str) -> None:
    prod = build_product_table(items)
    if prod.empty:
        print("No item-level data loaded - nothing to rank.")
        return

    best_path = os.path.join(out_dir, "products_best_sellers.csv")
    stopped_path = os.path.join(out_dir, "products_stopped_selling.csv")
    prod.to_csv(best_path, index=False, encoding="utf-8-sig")
    stopped = prod[prod["status"] == "STOPPED SELLING"].sort_values(
        "revenue", ascending=False)
    stopped.to_csv(stopped_path, index=False, encoding="utf-8-sig")

    print("=" * 78)
    print("PRODUCT PERFORMANCE")
    print("=" * 78)
    print(f"(reference date = {items['date'].max():%Y-%m-%d}; "
          f"'stopped selling' = no sale in the last {STOPPED_SELLING_DAYS} days)\n")
    print(f"Total distinct items ever sold: {len(prod):,}")
    print(f"Wrote full ranked list -> {best_path}")
    print(f"Wrote stopped-selling list -> {stopped_path}")

    print("\n>> TOP 15 BEST SELLERS (all-time, by revenue)")
    print(prod.head(15)[["name", "units_sold", "revenue", "orders", "last_sale"]]
          .to_string(index=False, max_colwidth=45))

    print(f"\n>> STOPPED SELLING ({len(stopped)} items, ranked by what they used to earn)")
    if stopped.empty:
        print("  (none - everything has sold within the last "
              f"{STOPPED_SELLING_DAYS} days)")
    else:
        print(stopped.head(20)[["name", "units_sold", "revenue", "last_sale",
                                 "days_since_last_sale"]]
              .to_string(index=False, max_colwidth=45))


# --------------------------------------------------------------------------- #
# 5. Halloween prep  -  per-item seasonal demand, with variance
# --------------------------------------------------------------------------- #

# Customers order ~45 days before an event (1-3 weeks production + ~10 days
# Greece->US shipping) - see CLAUDE_data-analysis1.md. So the Halloween
# ordering window opens roughly mid-August. This report is meant to be run
# in the weeks before that, to decide what to have pre-made ready to go.
HALLOWEEN_MONTHS = (9, 10)   # Sep-Oct pooled, per the existing seasonality finding


def build_halloween_table(items: pd.DataFrame) -> pd.DataFrame:
    """
    Per listing: Sep-Oct units sold in each historical year, then mean/std/min/max
    across those years. Small n (few Halloweens observed) is reported explicitly,
    not hidden - a mean of 1 year is a data point, not a forecast.
    """
    if items.empty:
        return pd.DataFrame()
    it = items.copy()
    it["cal_month"] = it["date"].dt.month
    it["cal_year"] = it["date"].dt.year
    # only fully-elapsed Halloween seasons count as history; this year's
    # Sep/Oct (if we're already past it when this runs) would be included too
    hw = it[it["cal_month"].isin(HALLOWEEN_MONTHS)]
    if hw.empty:
        return pd.DataFrame()

    per_year = hw.groupby(["listing_id", "cal_year"])["qty"].sum().reset_index()
    stats = per_year.groupby("listing_id")["qty"].agg(
        years_observed="count", mean_units="mean", std_units="std",
        min_units="min", max_units="max", total_units="sum")
    stats["std_units"] = stats["std_units"].fillna(0.0)
    stats["cv"] = (stats["std_units"] / stats["mean_units"]).round(2)  # coefficient of variation

    names = hw.groupby("listing_id")["item_name"].last()
    revenue = hw.groupby("listing_id")["item_total"].sum()
    overall = build_product_table(items).set_index("listing_id")["status"] \
        if not items.empty else pd.Series(dtype=str)

    out = stats.join(names.rename("name")).join(revenue.rename("halloween_revenue_alltime"))
    out = out.join(overall.rename("current_status"))
    out["confidence"] = out["years_observed"].apply(
        lambda n: "low (1 season only)" if n <= 1 else
                   ("medium (2 seasons)" if n == 2 else "higher (3+ seasons)"))
    cols = ["name", "years_observed", "confidence", "mean_units", "std_units",
            "cv", "min_units", "max_units", "total_units",
            "halloween_revenue_alltime", "current_status"]
    return out.reset_index()[cols].sort_values("mean_units", ascending=False)


def run_halloween(items: pd.DataFrame, out_dir: str) -> None:
    table = build_halloween_table(items)
    if table.empty:
        print("No Sep/Oct sales history found - nothing to base a Halloween "
              "forecast on.")
        return

    path = os.path.join(out_dir, "halloween_prep.csv")
    table.to_csv(path, index=False, encoding="utf-8-sig")

    years_seen = sorted(int(y) for y in
        items.loc[items["date"].dt.month.isin(HALLOWEEN_MONTHS), "date"].dt.year.unique())

    print("=" * 78)
    print("HALLOWEEN PREP  -  per-item Sep-Oct demand, historical")
    print("=" * 78)
    print(f"Halloween seasons in the data: {years_seen}")
    print("Lead time reminder: production is 1-3 weeks + ~10 days Greece->US "
          "shipping, and buyers order ~45 days out - so the ordering window "
          "opens roughly mid-August. This is when 'ready-made' stock starts "
          "to matter, not October.")
    print(f"\nWrote full per-item table -> {path}")

    print("\n>> TOP 20 BY AVERAGE SEP-OCT UNITS (mean across observed years)")
    top = table.head(20)
    print(top[["name", "years_observed", "confidence", "mean_units",
               "std_units", "cv", "current_status"]]
          .to_string(index=False, max_colwidth=42))

    flagged = table[(table["current_status"] == "STOPPED SELLING") &
                     (table["mean_units"] >= 3)]
    print(f"\n>> WARNING: {len(flagged)} item(s) look SEASONAL, not abandoned")
    print("These are flagged 'STOPPED SELLING' by the 180-day rule, but have real "
          "Sep-Oct history - that flag is almost certainly just the off-season gap, "
          "not a dead product. Don't read the earlier stopped-selling list as-is for "
          "these without checking this table first.")
    if not flagged.empty:
        print(flagged[["name", "years_observed", "mean_units", "std_units",
                        "cv"]].to_string(index=False, max_colwidth=42))

    print("\nHow to read this table:")
    print("- mean_units: average units sold in Sep+Oct pooled, per historical year")
    print("- std_units / cv: how much that varies year to year. Low cv (<~0.4) on a "
          "few years = fairly consistent seasonal demand. High cv or years_observed<=1 "
          "= treat the mean as a rough guess, not a committed number - hedge production.")
    print("- This is descriptive history, not a statistical forecast model. With "
          "3-6 data points per item, don't dress up the mean as more precise than it is.")


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main(argv=None) -> None:
    p = argparse.ArgumentParser(description="ClairesWigs Etsy data organizer")
    p.add_argument("--data-dir", default=DEFAULT_DATA_DIR)
    p.add_argument("cmd", nargs="?", default="all",
                    choices=["catalog", "customers", "products", "halloween", "all"])
    args = p.parse_args(argv)

    data_dir = args.data_dir
    if not os.path.isdir(data_dir):
        sys.exit(f"ERROR: data folder not found: {data_dir}")
    out_dir = os.path.join(data_dir, OUTPUT_SUBDIR)
    os.makedirs(out_dir, exist_ok=True)

    cat = discover(data_dir)
    if args.cmd in ("catalog", "all"):
        print_catalog(data_dir, cat)

    if args.cmd in ("customers", "products", "halloween", "all"):
        orders = load_orders(cat["by_kind"]["orders"])
        items = load_items(cat["by_kind"]["order_items"])

    if args.cmd in ("customers", "all"):
        run_customers(data_dir, orders, items, out_dir)

    if args.cmd in ("halloween", "all"):
        run_halloween(items, out_dir)

    if args.cmd in ("products", "all"):
        run_products(items, out_dir)


if __name__ == "__main__":
    main()
