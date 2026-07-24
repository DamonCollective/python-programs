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
    4. financials - turnover in US$, EUR equivalent (Etsy's own per-transaction
                    FX rate), and what actually remains after ALL of Etsy's
                    costs (real bank deposits, not an estimate).

All of the above are also written into a persistent SQLite database
(etsy_data.db, in the data folder) so that new exports can be dropped into the
folder later and merged in without re-processing or duplicating history - see
the 'database' command and DB_NOTES below.

DB_NOTES (how "keep everything, add more later" actually works)
-----------------------------------------------------------------------------
Every run of 'database' (or 'all') re-reads whatever CSV/JSON files currently
sit in the data folder and merges them into etsy_data.db:
  - Transactional tables (orders, order_items, deposits, checkout_payments)
    are UPSERTED by their natural key (Order ID / Transaction ID / Payment ID
    / date+amount+bank-last-4). Rows already in the database are kept; only
    new or changed rows are added/updated. Nothing is deleted. So you can add
    a fresh "EtsySoldOrders2026.csv" with more rows in October, re-run, and
    the database grows - it does not need the old file kept around forever,
    though there's no harm in keeping it either.
  - Snapshot tables (listings, reviews, shop_settings) reflect whatever was
    most recently loaded, since those are "current state" exports, not an
    append-only log.
Once built, etsy_data.db can be queried directly with any SQL tool
(e.g. `sqlite3 etsy_data.db "select * from orders limit 5"`), which is the
"ask a question, get an accurate answer" part - the tables and column names
are stable and documented in the loader functions below, not a moving target.

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
    python organize_data.py financials    # turnover US$ / EUR / net-after-Etsy
    python organize_data.py database      # build/update etsy_data.db, no reports
    python organize_data.py all           # everything above

Add  --data-dir "PATH"  to point at a different export folder.
Output goes to <data-dir>/organized_output/
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import os
import sqlite3
import sys
from datetime import timedelta

import pandas as pd

DEFAULT_DATA_DIR = r"D:\Downloads\DATA-ETSY"
OUTPUT_SUBDIR = "organized_output"
DB_NAME = "etsy_data.db"
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
    df = df.drop(columns=["Shipping"])  # else clashes with "shipping" in SQLite (case-insensitive)
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
    df = df.drop(columns=["Price"])  # else clashes with "price" in SQLite (case-insensitive)
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
    df = df.drop(columns=["Date", "Amount"])  # else clash with "date"/"amount" in SQLite
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
    df = df.drop(columns=["Fees"])  # else clashes with "fees" in SQLite (case-insensitive)
    df["order_id"] = df.get("Order ID", "").str.strip()
    return df


def load_listings(path: str | None) -> pd.DataFrame:
    if not path or not os.path.isfile(path):
        return pd.DataFrame()
    df = _read_csv(path)
    df["price"] = _to_num(df.get("PRICE"))
    df = df.drop(columns=["PRICE"])  # else clashes with "price" in SQLite (case-insensitive)
    return df


# --------------------------------------------------------------------------- #
# 2b. Persistent database  -  "keep everything, add more later, ask questions"
# --------------------------------------------------------------------------- #

# table -> columns that uniquely identify a row, for upsert-by-key
TABLE_KEYS = {
    "orders": ["Order ID"],
    "order_items": ["Transaction ID"],
    # NOTE: use the derived lowercase "date"/"amount", not raw "Date"/"Amount" -
    # those raw columns get folded away by _dedupe_columns_for_sqlite (case-
    # insensitive clash with the derived columns), so keying on them would
    # silently break matching on every run after the first.
    "deposits": ["date", "amount", "Bank Account Ending Digits"],
    "checkout_payments": ["Payment ID"],
}


def _dedupe_columns_for_sqlite(df: pd.DataFrame) -> pd.DataFrame:
    """
    SQLite treats column names as case-insensitive, so a raw CSV column like
    "Shipping" and our own derived "shipping" collide at CREATE TABLE time even
    though pandas is fine holding both. Keep the LAST occurrence of any
    case-insensitive duplicate (our derived/cleaned columns are always added
    after the raw ones, so this keeps the cleaned version).
    """
    seen = {}
    for i, col in enumerate(df.columns):
        seen[col.lower()] = i          # later index overwrites earlier
    keep_idx = sorted(seen.values())
    return df.iloc[:, keep_idx]


def _upsert(conn: sqlite3.Connection, table: str, new_df: pd.DataFrame) -> tuple[int, int]:
    """
    Merge new_df into `table`, keyed by TABLE_KEYS[table]. Existing rows are
    kept; rows with the same key are refreshed with the newest load; brand
    new rows are added. Nothing already in the table is ever dropped.
    Returns (rows_before, rows_after).
    """
    keys = TABLE_KEYS[table]
    new_df = new_df.copy()
    # sqlite3's driver can't bind pandas Timestamp objects - store as ISO text,
    # same as what comes back out of a round-trip read, so types never clash
    for col in new_df.columns:
        if pd.api.types.is_datetime64_any_dtype(new_df[col]):
            new_df[col] = new_df[col].dt.strftime("%Y-%m-%d %H:%M:%S")

    existing = pd.DataFrame()
    try:
        existing = pd.read_sql(f"SELECT * FROM {table}", conn)
    except (sqlite3.OperationalError, pd.errors.DatabaseError):
        pass  # table doesn't exist yet - first run
    before = len(existing)

    # align dtypes as str for the key columns so joins/dedup are exact. Round
    # any float key first - money values drift by a bit (e.g. 71.96 ->
    # 71.959999999999999) after a couple of SQLite round-trips, which would
    # otherwise silently break key matching on the 2nd/3rd run, not the 1st.
    for df in (existing, new_df):
        for k in keys:
            if k in df.columns:
                if pd.api.types.is_float_dtype(df[k]):
                    df[k] = df[k].round(2)
                df[k] = df[k].astype(str)

    combined = pd.concat([existing, new_df], ignore_index=True, sort=False)
    combined = combined.drop_duplicates(subset=keys, keep="last")
    combined = _dedupe_columns_for_sqlite(combined)
    combined.to_sql(table, conn, if_exists="replace", index=False)
    return before, len(combined)


def _replace_snapshot(conn: sqlite3.Connection, table: str, df: pd.DataFrame) -> None:
    """Snapshot tables (current-state exports) just get overwritten wholesale."""
    if df.empty:
        return
    df = _dedupe_columns_for_sqlite(df)
    df.to_sql(table, conn, if_exists="replace", index=False)


def build_database(data_dir: str, cat: dict) -> sqlite3.Connection:
    """Load every recognized export and merge it into etsy_data.db."""
    db_path = os.path.join(data_dir, DB_NAME)
    conn = sqlite3.connect(db_path)

    orders = load_orders(cat["by_kind"]["orders"])
    items = load_items(cat["by_kind"]["order_items"])
    deposits = load_deposits(cat["by_kind"]["deposits"])
    ccp = load_checkout_payments(cat["by_kind"]["checkout_payments"])
    listings_files = cat["by_kind"]["listings"]
    listings = load_listings(listings_files[0] if listings_files else None)

    report = {}
    if not orders.empty:
        report["orders"] = _upsert(conn, "orders", orders)
    if not items.empty:
        report["order_items"] = _upsert(conn, "order_items", items)
    if not deposits.empty:
        report["deposits"] = _upsert(conn, "deposits", deposits)
    if not ccp.empty:
        report["checkout_payments"] = _upsert(conn, "checkout_payments", ccp)
    if not listings.empty:
        _replace_snapshot(conn, "listings", listings)
        report["listings"] = (None, len(listings))
    conn.commit()

    _hr = "-" * 78
    print(_hr)
    print(f"DATABASE  -  {db_path}")
    print(_hr)
    for table, (before, after) in report.items():
        if before is None:
            print(f"  {table:20s} snapshot replaced -> {after:,} rows")
        elif before == after and before > 0:
            print(f"  {table:20s} {after:,} rows (no change - nothing new to merge)")
        else:
            print(f"  {table:20s} {before:,} -> {after:,} rows "
                  f"(+{after - before:,} new/updated)")
    print()
    return conn


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
# 6. Financials  -  turnover US$, EUR equivalent, net after Etsy's expenses
# --------------------------------------------------------------------------- #

def build_financials_table(orders: pd.DataFrame, ccp: pd.DataFrame,
                            deposits: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Returns (by_year table, all_time dict). See the printed report for how to
    read each column - the short version:
      - turnover_usd_*      : what buyers paid, from Sold Orders (accrual, by order date)
      - eur_gross_etsy_fx   : the same sales converted to EUR at ETSY'S OWN per-
                              transaction rate (from Checkout Payments), for orders
                              that are actually in the Sold Orders export (excludes
                              fully-refunded/cancelled charges)
      - eur_net_after_etsy  : real EUR that hit the bank (Deposits export) - this
                              already has EVERY Etsy cost removed (processing fee,
                              transaction fee, listing fees, any ad spend), because
                              it's the literal payout amount, not a calculation.
    CAVEAT: turnover/eur_gross are dated by ORDER date (accrual); deposits are
    dated by PAYOUT date (cash). Etsy pays out ~1-3 weeks after a sale, so a
    few thousand EUR near each year boundary shifts into the following year's
    deposit total. Don't over-read small year-to-year swings at the edges;
    the all-time totals are unaffected by this timing shift.
    """
    matched = ccp[ccp["order_id"].isin(set(orders["Order ID"]))].copy()
    pay_by_order = matched.set_index("order_id")[["gross_amount", "fees"]]
    o = orders.set_index("Order ID").join(pay_by_order, how="left")
    o["year"] = pd.to_datetime(o["date"]).dt.year

    by_year = o.groupby("year").agg(
        orders=("order_value", "count"),
        turnover_usd_merch=("order_value", "sum"),
        turnover_usd_incl_ship=("order_total", "sum"),
        eur_gross_etsy_fx=("gross_amount", "sum"),
    )
    dep_by_year = deposits.groupby(deposits["date"].dt.year)["amount"].sum()
    by_year["eur_net_after_etsy"] = dep_by_year
    by_year["etsy_total_cut_%"] = (
        100 * (1 - by_year["eur_net_after_etsy"] / by_year["eur_gross_etsy_fx"])
    ).round(1)

    unmatched_orders = o["gross_amount"].isna().sum()

    all_time = {
        "orders": int(len(o)),
        "turnover_usd_merch": float(o["order_value"].sum()),
        "turnover_usd_incl_ship": float(o["order_total"].sum()),
        "eur_gross_etsy_fx": float(o["gross_amount"].sum()),
        "eur_net_after_etsy": float(deposits["amount"].sum()),
        "unmatched_orders_no_payment_row": int(unmatched_orders),
        "avg_implied_fx_usd_to_eur": float(
            (matched["gross_amount"] / _to_num(matched["Listing Amount"])).mean()),
    }
    all_time["etsy_total_cut_%"] = round(
        100 * (1 - all_time["eur_net_after_etsy"] / all_time["eur_gross_etsy_fx"]), 1)
    return by_year, all_time


def run_financials(orders: pd.DataFrame, ccp: pd.DataFrame,
                    deposits: pd.DataFrame, out_dir: str) -> None:
    if orders.empty or ccp.empty or deposits.empty:
        print("Missing orders, checkout-payments, or deposits data - "
              "can't compute financials."); return
    by_year, all_time = build_financials_table(orders, ccp, deposits)

    path = os.path.join(out_dir, "financials_by_year.csv")
    by_year.to_csv(path, encoding="utf-8-sig")

    _hr = "-" * 78
    print(_hr)
    print("FINANCIALS  -  turnover, EUR equivalent, net after Etsy's expenses")
    print(_hr)
    print("turnover_usd_merch    : what buyers paid for merchandise (USD), from Sold Orders")
    print("turnover_usd_incl_ship: same, plus shipping & tax charged to buyer (USD)")
    print("eur_gross_etsy_fx     : same sales in EUR, at Etsy's OWN per-transaction FX rate")
    print("eur_net_after_etsy    : actual EUR deposited to the bank - ALL Etsy costs already")
    print("                        removed (processing fee, transaction fee, listing fees,")
    print("                        any ad spend). Not an estimate - it's the real payout.")
    print("etsy_total_cut_%      : 1 - (net_after_etsy / eur_gross), i.e. Etsy's full bite\n")

    print(by_year.to_string(float_format=lambda v: f"{v:,.2f}"))
    print(f"\nWrote by-year table -> {path}")

    print("\n>> ALL-TIME (2020-10-10 through most recent data)")
    print(f"  Orders:                     {all_time['orders']:,}")
    print(f"  Turnover, merchandise:      US$ {all_time['turnover_usd_merch']:,.2f}")
    print(f"  Turnover, incl ship/tax:    US$ {all_time['turnover_usd_incl_ship']:,.2f}")
    print(f"  EUR equivalent (Etsy's FX): EUR {all_time['eur_gross_etsy_fx']:,.2f}"
          f"   (avg implied rate ~{all_time['avg_implied_fx_usd_to_eur']:.3f} USD->EUR)")
    print(f"  Net after ALL Etsy costs:   EUR {all_time['eur_net_after_etsy']:,.2f}")
    print(f"  Etsy's total cut:           {all_time['etsy_total_cut_%']:.1f}%  "
          f"of the EUR gross amount")
    if all_time["unmatched_orders_no_payment_row"]:
        print(f"\n  NOTE: {all_time['unmatched_orders_no_payment_row']} order(s) had no "
              f"matching Checkout Payments row (excluded from the EUR gross figure "
              f"above, included in the USD turnover figure) - check these manually.")

    print("\nWhy 'net after Etsy costs' uses Deposits and not a fee calculation:")
    print("Checkout Payments only shows the payment-PROCESSING fee. Etsy also bills")
    print("transaction fees, listing fees, and any ad spend separately ('Etsy Bill'),")
    print("which is not in any file in this folder. The bank deposit is the one number")
    print("that already has literally everything removed - no assumptions required.")


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main(argv=None) -> None:
    p = argparse.ArgumentParser(description="ClairesWigs Etsy data organizer")
    p.add_argument("--data-dir", default=DEFAULT_DATA_DIR)
    p.add_argument("cmd", nargs="?", default="all",
                    choices=["catalog", "customers", "products", "halloween",
                             "financials", "database", "all"])
    args = p.parse_args(argv)

    data_dir = args.data_dir
    if not os.path.isdir(data_dir):
        sys.exit(f"ERROR: data folder not found: {data_dir}")
    out_dir = os.path.join(data_dir, OUTPUT_SUBDIR)
    os.makedirs(out_dir, exist_ok=True)

    cat = discover(data_dir)
    if args.cmd in ("catalog", "all"):
        print_catalog(data_dir, cat)

    if args.cmd in ("database", "all"):
        build_database(data_dir, cat)

    if args.cmd in ("customers", "products", "halloween", "financials", "all"):
        orders = load_orders(cat["by_kind"]["orders"])
        items = load_items(cat["by_kind"]["order_items"])

    if args.cmd in ("customers", "all"):
        run_customers(data_dir, orders, items, out_dir)

    if args.cmd in ("halloween", "all"):
        run_halloween(items, out_dir)

    if args.cmd in ("products", "all"):
        run_products(items, out_dir)

    if args.cmd in ("financials", "all"):
        deposits = load_deposits(cat["by_kind"]["deposits"])
        ccp = load_checkout_payments(cat["by_kind"]["checkout_payments"])
        run_financials(orders, ccp, deposits, out_dir)


if __name__ == "__main__":
    main()
