"""
ELTA_Damon2.9 — Don't JS-click react-select combobox triggers
(forked from Elta_Damon2.8)

2.9 (2026-08-20): 2.8's JS-click fallback broke the one click it was
already documented not to work for — the Made-in/ship-from/ship-to
react-select trigger already had a comment saying "a real click opens it,
a synthetic JS click does not". When the native click on Made-in got
intercepted, the JS fallback fired, reported success (no exception), but
never actually opened the dropdown — so the following code, believing it
was open, typed "Greece" into whatever was still focused instead (the
HS-code field), corrupting it to "6704.11.0000Gr" (confirmed live, Brett
Johnson order — 2 characters landed before something interrupted it).
click_with_retry gained a use_js_fallback=True/False parameter; the three
combobox-trigger call sites (_zonos_select_combo's button click, Made-in
field click) now pass False, so a failed native click there goes straight
to retry/pause instead of a JS click that only fakes success.

ELTA_Damon2.8 — JS-click fallback for intercepted clicks
(forked from Elta_Damon2.7)

2.8 (2026-08-20): recurring pattern across this whole live-testing session
— "Save item", the Made-in option, and "Continue to payment" all failed
with the identical ElementClickInterceptedException ("is not clickable at
point (x,y) because another element ... obscures it"), each needing a
manual-fix pause even though the button was visibly fine on screen. Cause:
Selenium's native .click() does a hit-test at the element's center point,
and some other element (a text label, a sticky footer wrapper) sits at
that exact pixel per Zonos's layout — so the "real" clickable area isn't
where Selenium tries to click. click_with_retry now tries a JS-dispatched
click (driver.execute_script("arguments[0].click();", el)) as an automatic
fallback the moment a native click fails, before ever sleeping/retrying or
pausing — a JS click fires directly on the element with no hit-test, so it
goes through regardless of what's visually on top of it. Should eliminate
most of today's manual-fix pauses outright.

ELTA_Damon2.7 — Fixes a react-select crash after a manual combobox fix
(forked from Elta_Damon2.6)

2.7 (2026-08-20): live-confirmed first real 3-item Zonos order to fully
succeed (Toni Willis) — but crashed with "'NoneType' object has no
attribute 'group'" adding item 3. Cause: when a click_with_retry pause on
the Made-in / ship-from / ship-to combobox gets resolved by the user
picking the option themselves (not just opening the dropdown), the
dropdown is already closed and focus has moved on by the time the script's
own code resumes — so the react-select id it expects to find on the
focused element (to build the "...-option" selector) isn't there, and
`m.group(1)` crashed on `m = None`. Both call sites (_zonos_select_combo
and zonos_add_item's Made-in field) now trust that a non-matching id means
the user already finished the selection by hand, and just move on instead
of crashing. (This particular crash was already caught by 2.5's per-item
try/except rather than losing the whole order — item 3 was fine on screen
— but it shouldn't need a manual-fix dialog for something already fixed.)

ELTA_Damon2.6 — Fixes the truncated customs tariff code (Donald MacDonald)
(forked from Elta_Damon2.5)

2.6 (2026-08-20): CUSTOMS_TARIFF_CODE was "67041100" (8 digits) even though
its own comment said it should match Zonos' "6704.11.0000" — 2 zeros short
of the real 10-digit HTS heading. ZONOS_HS_CODE's dotted-form derivation
then produced "6704.11.00" instead of "6704.11.0000", which Zonos
errored/rejected on live (Donald MacDonald order), and the same truncated
code was going into ELTA's own bulk-upload CSV "HS tariff number" columns.
Fixed at the single source (CUSTOMS_TARIFF_CODE = "6704110000"), which
corrects both systems at once, matching the comment's own stated intent
that ELTA and Zonos always declare the identical code.

ELTA_Damon2.5 — Per-item resilience in Zonos + digits-only phone for ELTA CSV
(forked from Elta_Damon2.4)

2.5 (2026-08-20), two independent fixes from the same live testing session:

1) zonos_add_item()'s description/value/HS-code/qty-container lookups were
   raw driver.find_element() calls with no wait at all — the one remaining
   place in the whole Zonos flow that could still throw instantly (e.g.
   right after a manual-fix pause, before the item form finishes
   re-rendering). New find_with_wait() helper gives them the same
   retry-then-pause treatment click_with_retry gives clicks. On top of
   that, the per-item loop in process_zonos_batch() now wraps EACH
   zonos_add_item() call in its own try/except: a failure on one item
   pauses for the user to add/fix just that item, then the loop continues
   with the next item — instead of escaping to the outer per-ORDER handler
   and abandoning every remaining item (confirmed live: a 3-item order,
   Sean Maley, only got item 1 added before the automation moved straight
   to the finish/compliance step).

2) ELTA's business-account CSV bulk-upload rejected a real order (Donald
   MacDonald) with "Μη έγκυρη τιμή (Παραλήπτης - Τηλέφωνο)" because the
   customer's phone was entered as "(616)302-2487" and build_csv_row() only
   stripped whitespace before writing it — the parentheses and dash stayed.
   Now strips everything but digits.

ELTA_Damon2.4 — Closes the last gap in per-step retry/pause coverage
(forked from Elta_Damon2.3)

2.4 (2026-08-20): 2.3 fixed click_with_retry's own re-click bug, but two
clicks inside zonos_add_item() / _zonos_select_combo() never went through
click_with_retry at all — the auto-classify-toggle checkbox and the
react-select dropdown "option" clicks used raw .click() with zero retry or
pause. When one of those hit the same "could not be scrolled into view"
issue (Sean Maley order, 2026-08-20), the exception skipped every per-step
safety net and landed in the outer per-order try/except, which shows a
dialog but then — since it's the only order in a single-order run — falls
through to `finally: driver.quit()` and kills the whole Zonos session,
forcing a full restart. Fixed by routing all three remaining raw clicks
through click_with_retry, so a failure there now pauses in place and lets
the automation continue the SAME order afterward, instead of losing it.

ELTA_Damon2.3 — Fixes click_with_retry to stop re-clicking after a manual
pause (forked from Elta_Damon2.2)

2.3 (2026-08-20): click_with_retry's manual-pause fallback used to click the
element again right after the user was told "fix manually, then click Done"
— for a toggle element like Zonos's attestation checkbox, that re-click
undid the user's own manual fix (ticked it, then the script immediately
unticked it again), which is the likely cause of the Zonos flow breaking/
closing right after a manual-fix pause. Fixed to match elta6.01's actual
pattern: try automatically (with retries) -> on failure, ask the user to
complete that one step by hand in the browser -> once they click Done, trust
it's done and move on to the next step, never clicking again itself.

ELTA_Damon2.2 — Adds CP/LL/per-order service choice + click-retry resilience
(forked from Elta_Damon2.1)

2.00's bottleneck turned out to be Zonos Prepay itself — done live, by hand,
one field at a time. 2.1 adds Selenium automation for that step (function
prefix zonos_*, see the "ZONOS PREPAY AUTOMATION" section below), built from
the real DOM selectors (data-testid attributes) confirmed live against
dashboard.zonosprepay.com on 2026-08-18, plus a deterministic net-weight
formula (compute_item_weights_g) so the script never has to ask the user to
type a per-item weight by hand again. It still pauses once per order — right
before the Pay button — for the user to complete card/CVC, then finishes the
order itself: ticks the attestation checkbox, waits for the confirmation
page, and saves both the confirmation and invoice documents as real headless
PDFs via Selenium's driver.print_page() (no native print dialog — that was
the wall 2.0-via-Claude-in-Chrome hit every time). ELTA's own CSV
export/upload/label-printing (everything from Elta_Damon2.00) is completely
unchanged — this only touches the Zonos side, and the two stay decoupled:
Zonos produces its saved PDFs exactly as before, and the existing
parse_zonos_pdf()/CSV-export path still reads them back the same way.

2.2 (2026-08-19), built after a live batch where the run-wide "Parcel"
choice silently produced an LL (854) row for a US order (Stephen Duff) —
root cause not confirmed (mis-click vs. a real bug), but the fix either way
is to make the choice explicit and give a per-order escape hatch:
ask_service_preference() is now a 3-way choice — "CP" (renamed from
"Parcel" for clarity; same 800 US/802 UK codes), "LL" (854), or "Let me
choose per order", which pauses once per record via
ask_service_preference_for_record() so the user picks CP/LL by hand for
that specific order instead of trusting one run-wide default. Also carries
forward the click_with_retry() resilience pattern added to 2.1's Zonos flow
on 2026-08-19 — see feedback_automation_retry_pattern in project memory.

ELTA_Damon2.00 — Business-Account CSV Bulk-Upload Variant (forked from Elta_Damon1.3)

This is a scope change, not just a version bump: 2.00 no longer drives ELTA's
weblabeling site with Selenium at all. Instead it produces a semicolon-delimited
CSV file matching ELTA's own "ΕΡΜΗΣ-ΣΥΣΤΗΜΑ ΠΕΛΑΤΗΣ" business-account bulk-import
format (see D:\\Downloads\\Instructions.xls / Sample_File.xlsx — the 72-column
spec ELTA gives business customers for "Εισαγωγή Στοιχείων Αντικειμένων Από
Αρχείο"). You upload that file yourself on weblabeling.elta.gr after logging in
with the business account (customer code + username + password) — this script's
job ends at producing a correct, ready-to-upload file.

Everything upstream of that (Etsy order parsing, product catalog, customer DB,
returning-customer handling, MyData receipt + Zonos PDF parsing, thank-you
letters) is unchanged from Elta_Damon1.3 — only the final "submit to ELTA" step
changed from browser automation to a file.

Differences from Elta_Damon1.3:
  - Selenium/Firefox removed entirely — no browser, no CAPTCHA, no per-field
    fill functions, no "Next" pauses. fill_by_id / fill_visible_field /
    click_checkbox_by_label / find_and_click_next_button / select_country_and_service /
    fill_receiver_form / fill_content_description / fill_customs_declaration_lines /
    print_shipping_label / process_elta_labels are all gone.
  - New build_csv_row()/write_shipment_csv()/process_csv_export() write one row
    per shipment to ELTA_BULK_<timestamp>.csv in OUTPUT_DIR, using the exact
    72-column header from Sample_File.xlsx. Recipient address is always written
    inline (column C "ID"/recipient-code left blank) — no dependency on ELTA's
    separate saved-recipient address book.
  - Country + numeric Service code (columns A/B) are resolved from SERVICE_CODES,
    captured live from the business account's own country/service dropdowns
    (weblabeling.elta.gr, 2026-08-18) since the code numbering is per-country and
    isn't documented anywhere ELTA hands out on paper.
  - Service preference is asked once per run (ask_service_preference): "CP"
    (default — service 800 for US / 802 for UK, ELTA's promo pricing through
    2026-12-31, ~18€/kg vs the older 21€/kg flat LL rate), "LL" (854, the
    dimension-agnostic registered-letter rate used until now), or "Let me
    choose per order" (2.2, 2026-08-19) which pauses once per record via
    ask_service_preference_for_record() instead of trusting one run-wide
    default. Revisit CP/LL in November per user's own note — the promo's
    future beyond Dec 2026 is unknown.
  - Zonos Prepay PDF lookup only runs for USA shipments — the UK has no Zonos
    step (confirmed by user 2026-08-18); get_and_parse_receipt() no longer asks
    for a Zonos confirmation file for non-US orders.
  - Customs declaration line weight/description/value still come from the same
    MyData-receipt + Zonos merge as 1.3 (get_and_parse_receipt, unchanged logic
    including the 70%-of-gross-weight fallback for items with no Zonos weight).

Differences from elta6.01 (carried over from Elta_Damon1.2/1.3):
  - Package weight/dimensions are entered once, in the Review & Edit screen —
    same fields, now read directly into the CSV row instead of auto-filled onto
    a browser form.
  - Customs declaration lines are parsed automatically from a per-customer MyData
    receipt PDF in D:\\Downloads (matched by surname; filenames containing "zonos"
    are never treated as the receipt — those are Zonos prep docs, not the MyData
    receipt): English-only description, quantity, value (Aξία), tariff 67041100,
    origin GR, invoice number from the receipt.
  - "Sale Of Goods" customs category ticked (column AH = 1) automatically and
    unconditionally on every order, same as before.

Base features (from elta6.01, unchanged):
  - Product catalog with unique SKUs (WIG-001, WIG-002 …)
  - Auto-SKU resolution: fuzzy title match + confirm dialog (same item / new item)
  - Auto-save dims/weight/customs value to catalog per SKU
  - Catalog values always override hardcoded defaults on load (weight/dims/price persist)
  - Customer CRM: returning customer dialog with stored vs new address comparison
  - Keep / Update (session only) / Update + Save to DB options
  - Historical import mode (data only, no CSV export)
  - From Database mode: multi-select customers → CSV rows/letters without Etsy file
  - Standalone DB manager — add, edit, delete customers and products
  - Edit Product button in order form — edit weight/price/dims for current SKU inline
  - Order deduplication — same order_id is never recorded twice
  - Customer address pre-saved at review stage (survives a mid-run crash)
  - Multi-item orders: assign more than one product per order, each as an
    existing catalog SKU, a brand-new catalog SKU, or a one-off description
    that is never saved to the catalog — fills one ELTA customs line per item
  - Assign Products popup auto-sizes to its content (no clipped columns)
"""

import sys, json, os, re, datetime, csv, unicodedata, time, base64
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from difflib import SequenceMatcher
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
from odf.opendocument import OpenDocumentText
from odf.style import Style, TextProperties, ParagraphProperties
from odf.text import P, Span

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS & PATHS
# ═══════════════════════════════════════════════════════════════════════════════

OUTPUT_DIR       = os.path.expanduser("~/Documents/ELTA_NEW_PROGRAM")
CUSTOMER_DB_PATH = os.path.join(OUTPUT_DIR, "customer_db.json")
CATALOG_PATH     = os.path.join(OUTPUT_DIR, "product_catalog.json")

# ── GitHub DB sync ──────────────────────────────────────────────────────────
_tok = os.path.join(os.path.dirname(os.path.abspath(__file__)), "github_token.txt")
GITHUB_TOKEN = open(_tok).read().strip() if os.path.exists(_tok) else ""
GITHUB_REPO  = "DamonCollective/alegro-scripts"
GH_DB_PATH   = "elta_db/customer_db.json"
GH_CAT_PATH  = "elta_db/product_catalog.json"
GH_API       = "https://api.github.com"

def _gh_headers():
    return {"Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"}

def _gh_get_file(gh_path):
    import base64, urllib3
    urllib3.disable_warnings()
    try:
        r = requests.get(f"{GH_API}/repos/{GITHUB_REPO}/contents/{gh_path}",
                         headers=_gh_headers(), timeout=10, verify=False)
        if r.status_code == 200:
            d = r.json()
            return base64.b64decode(d["content"]).decode("utf-8"), d["sha"]
    except Exception:
        pass
    return None, None

def _gh_put_file(gh_path, content_str, message="update"):
    import base64, urllib3
    urllib3.disable_warnings()
    try:
        _, sha = _gh_get_file(gh_path)
        payload = {"message": message,
                   "content": base64.b64encode(content_str.encode("utf-8")).decode("ascii")}
        if sha:
            payload["sha"] = sha
        r = requests.put(f"{GH_API}/repos/{GITHUB_REPO}/contents/{gh_path}",
                         headers=_gh_headers(), json=payload, timeout=15, verify=False)
        return r.status_code in (200, 201)
    except Exception:
        return False

def _db_size(data_str):
    """Return a comparable size metric for a JSON DB string."""
    try:
        d = json.loads(data_str)
        if isinstance(d, dict):
            return d.get("_next_id", len(d))  # catalog uses _next_id, customer db uses key count
        return 0
    except Exception:
        return 0

def sync_dbs_from_github():
    """Smart sync: always keeps the richer copy. Pushes local to GitHub if local has more data."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for gh_path, local_path, label in [
        (GH_DB_PATH,  CUSTOMER_DB_PATH, "customer_db"),
        (GH_CAT_PATH, CATALOG_PATH,     "product_catalog"),
    ]:
        gh_content, sha = _gh_get_file(gh_path)
        local_content = None
        if os.path.exists(local_path):
            with open(local_path, 'r', encoding='utf-8') as f:
                local_content = f.read()

        gh_size    = _db_size(gh_content)    if gh_content    else 0
        local_size = _db_size(local_content) if local_content else 0

        if gh_size > local_size:
            # GitHub is richer — pull it down
            with open(local_path, 'w', encoding='utf-8') as f:
                f.write(gh_content)
            print(f"✓ {label}: pulled from GitHub ({gh_size} entries)")
        elif local_size > gh_size and local_content:
            # Local is richer — push it up
            _gh_put_file(gh_path, local_content, message=f"sync {label} from local (richer copy)")
            print(f"✓ {label}: pushed local to GitHub ({local_size} entries)")
        elif gh_content and not local_content:
            with open(local_path, 'w', encoding='utf-8') as f:
                f.write(gh_content)
            print(f"✓ {label}: pulled from GitHub (no local copy)")
        elif local_content and gh_content and local_content.strip() != gh_content.strip():
            # Same number of entries but content differs (e.g. dims updated locally but push failed)
            # Local wins — push to GitHub so the other machine gets the latest data
            _gh_put_file(gh_path, local_content, message=f"sync {label} from local (content refresh)")
            print(f"✓ {label}: pushed local to GitHub (content updated)")
        else:
            print(f"✓ {label}: already in sync")

EU_COUNTRIES = {
    "Austria","Belgium","Bulgaria","Croatia","Cyprus","Czech Republic",
    "Denmark","Estonia","Finland","France","Germany","Greece","Hungary",
    "Ireland","Italy","Latvia","Lithuania","Luxembourg","Malta","Netherlands",
    "Poland","Portugal","Romania","Slovakia","Slovenia","Spain","Sweden",
}

COUNTRY_NAME_MAP = {
    "United Kingdom": "Great Britain",
    "Spain": "ES SPAIN",
    "Netherlands": "NL NETHERLANDS",
}

# Canary Islands postal code prefixes (outside EU customs territory)
_CANARY_ZIPS = {'35', '38'}
_CANARY_STATES = {
    'las palmas', 'santa cruz de tenerife', 'tenerife',
    'canarias', 'canary islands', 'islas canarias', 'gran canaria',
    'lanzarote', 'fuerteventura', 'la palma', 'la gomera', 'el hierro',
}
def _is_canary_islands(record):
    z = str(record.get('ship_zipcode', '')).strip()
    if z[:2] in _CANARY_ZIPS:
        return True
    state = str(record.get('ship_state', '')).strip().lower()
    city  = str(record.get('ship_city', '')).strip().lower()
    return state in _CANARY_STATES or city in _CANARY_STATES


def elta_country(record):
    """Return the exact option text from the ELTA weblabeling country dropdown."""
    country = record.get('ship_country', '')
    if country == 'Spain':
        if _is_canary_islands(record):
            return 'IC CANARY ISLANDS / SPAIN'
        z = str(record.get('ship_zipcode', '')).strip()
        if z[:2] == '51':
            return 'XC CEUTA / SPAIN'
        if z[:2] == '52':
            return 'XL MELILLA / SPAIN'
    return COUNTRY_NAME_MAP.get(country, country)


def needs_customs(record):
    """Return True if this shipment requires a customs declaration."""
    country = record.get('ship_country', '')
    if country not in EU_COUNTRIES:
        return True
    # Canary Islands, Ceuta, Melilla are in Spain but outside EU customs territory
    if country == 'Spain':
        z = str(record.get('ship_zipcode', '')).strip()
        if _is_canary_islands(record) or z[:2] in ('51', '52'):
            return True
    return False

COUNTRY_TO_ISO2 = {
    "United States":"US","United States of America":"US","USA":"US",
    "United Kingdom":"GB","Great Britain":"GB","UK":"GB","Germany":"DE","France":"FR",
    "Italy":"IT","Spain":"ES","Netherlands":"NL","Belgium":"BE","Austria":"AT",
    "Switzerland":"CH","Sweden":"SE","Norway":"NO","Denmark":"DK","Finland":"FI",
    "Poland":"PL","Portugal":"PT","Greece":"GR","Australia":"AU","Canada":"CA",
    "Japan":"JP","South Korea":"KR","Brazil":"BR","Mexico":"MX","Argentina":"AR",
    "Chile":"CL","Colombia":"CO","Israel":"IL","Turkey":"TR","Russia":"RU",
    "China":"CN","India":"IN","Singapore":"SG","New Zealand":"NZ","Ireland":"IE",
    "Czech Republic":"CZ","Hungary":"HU","Romania":"RO","Bulgaria":"BG",
    "Croatia":"HR","Slovakia":"SK","Slovenia":"SI","Estonia":"EE","Latvia":"LV",
    "Lithuania":"LT","Luxembourg":"LU","Malta":"MT","Cyprus":"CY","Iceland":"IS",
    "UAE":"AE","Saudi Arabia":"SA","South Africa":"ZA","Ukraine":"UA","Serbia":"RS",
}

USA_COUNTRY_VALUES = {"United States","United States of America","USA","US"}

# ═══════════════════════════════════════════════════════════════════════════════
# ELTA BUSINESS-ACCOUNT SERVICE CODES  (columns A/B of the bulk-upload CSV)
# ═══════════════════════════════════════════════════════════════════════════════
# Captured live from weblabeling.elta.gr's own country/service dropdowns while
# logged into the business account, 2026-08-18 — ELTA doesn't document these
# codes anywhere on paper, and the numbering is per-country, not universal.
#
# Full US dropdown: 800 Parcel A and/or insured, 801 Parcel B and/or insured,
#   851 Letter A, 852 Letter B, 853 Letter RE, 854 Letter LL, 871-873 M-Bags.
# Full GB dropdown: 802 Parcel Interconnect Premium, 801 Parcel B and/or
#   insured, 851-854 Letters (same as US), 871-873 M-Bags. Note GB has NO
#   "800" option — Interconnect Premium (802) is GB's top parcel tier instead
#   (bundled tracking, signature, ~500€ insurance; UK is one of ELTA's 30
#   "Interconnect" countries).
#
# 'parcel' = the promo/priority parcel tier (18€/kg-ish, promo runs through
#   2026-12-31 per D:\Downloads\Screenshot 2026-08-18 ... ELTA PORTAL.png —
#   revisit this table in November per user's own note).
# 'll'     = 854 Letter LL, the flat 21€/kg-regardless-of-dimensions rate used
#   until now — always available as a fallback since it's identical for both
#   countries.
SERVICE_CODES = {
    "US": {"parcel": "800", "ll": "854"},
    "GB": {"parcel": "802", "ll": "854"},
}

def resolve_service_code(country_iso2, preference):
    """Return the numeric ELTA service code for (country, preference), falling
    back to LL (854) — and printing why — if the preferred tier doesn't exist
    for that country or the country isn't in SERVICE_CODES at all."""
    codes = SERVICE_CODES.get(country_iso2)
    if not codes:
        print(f"⚠ No known ELTA service codes for country '{country_iso2}' — "
              f"defaulting to LL (854). Add it to SERVICE_CODES once confirmed live.")
        return "854"
    code = codes.get(preference)
    if not code:
        print(f"⚠ '{preference}' service not available for {country_iso2} — "
              f"falling back to LL (854).")
        return codes.get("ll", "854")
    return code

def ask_service_preference():
    """Ask once per run which service tier to use. Returns 'parcel', 'll', or
    'ask' (meaning: pause and ask again for every individual order via
    ask_service_preference_for_record()). Enter / default button = 'parcel'.

    Added 2026-08-19 (2.2): was a 2-button Parcel/LL choice; renamed "Parcel"
    to "CP" for clarity (that's what it's always meant — 800 US / 802 UK,
    the promo top-tier code, same "CP" as elta6.02's weblabeling picker) and
    added the third "let me choose per order" option after a live run where
    the run-wide choice produced an unexpected LL row for a US order."""
    result = ["parcel"]
    root = tk.Tk(); root.title("ELTA_Damon2.9 — Service Preference")
    root.attributes('-topmost', True); root.resizable(False, False)
    tk.Label(root, text="Preferred ELTA service for this run:",
             font=('Arial', 12, 'bold'), pady=14, padx=20).pack()
    tk.Label(root,
             text="800 US / 802 UK CP (Parcel) — promo pricing through 31/12/2026\n"
                  "854 LL (Letter) — flat 21€/kg, used until now, always available",
             font=('Arial', 9), fg='#555', justify='left', padx=20).pack()
    bf = tk.Frame(root); bf.pack(pady=(10, 18), padx=20)
    def pick(v): result[0] = v; root.destroy()
    default_btn = tk.Button(bf, text="CP  (800 / 802 — default)",
              command=lambda: pick('parcel'),
              bg='#27ae60', fg='white', font=('Arial', 11, 'bold'),
              relief='flat', padx=20, pady=10, cursor='hand2', width=32)
    default_btn.pack(pady=6)
    tk.Button(bf, text="LL  (854 — registered letter)",
              command=lambda: pick('ll'),
              bg='#7f8c8d', fg='white', font=('Arial', 11, 'bold'),
              relief='flat', padx=20, pady=10, cursor='hand2', width=32).pack(pady=6)
    tk.Button(bf, text="Let me choose per order  (pauses each time)",
              command=lambda: pick('ask'),
              bg='#2980b9', fg='white', font=('Arial', 11, 'bold'),
              relief='flat', padx=20, pady=10, cursor='hand2', width=32).pack(pady=6)
    root.bind('<Return>', lambda e: pick('parcel'))
    root.update_idletasks()
    w, h = root.winfo_reqwidth(), root.winfo_reqheight()
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")
    default_btn.focus_set()
    root.grab_set(); root.mainloop()
    return result[0]

def ask_service_preference_for_record(record):
    """Per-order version of ask_service_preference(), used when the run-wide
    choice was 'ask'. Blocks until the user picks CP or LL for this specific
    order — same pattern as every other pause in this project (wait_for_user,
    zonos_pause_for_payment). Returns 'parcel' or 'll'; no default binding on
    Enter, so a mis-key can't silently pick the wrong one for a real order."""
    name = record.get('full_name', '') or f"{record.get('first_name','')} {record.get('last_name','')}".strip()
    country = record.get('ship_country', '?')
    result = [None]
    root = tk.Tk(); root.title("ELTA_Damon2.9 — Choose Service")
    root.attributes('-topmost', True); root.lift(); root.focus_force()
    root.resizable(False, False)
    tk.Label(root, text=f"Choose ELTA service for:\n{name}  ({country})",
             font=('Arial', 12, 'bold'), pady=14, padx=20, justify='center').pack()
    bf = tk.Frame(root); bf.pack(pady=(6, 18), padx=20)
    def pick(v): result[0] = v; root.destroy()
    cp_btn = tk.Button(bf, text="CP  (800 / 802)", command=lambda: pick('parcel'),
              bg='#27ae60', fg='white', font=('Arial', 11, 'bold'),
              relief='flat', padx=20, pady=10, cursor='hand2', width=24)
    cp_btn.pack(pady=6)
    tk.Button(bf, text="LL  (854)", command=lambda: pick('ll'),
              bg='#7f8c8d', fg='white', font=('Arial', 11, 'bold'),
              relief='flat', padx=20, pady=10, cursor='hand2', width=24).pack(pady=6)
    root.update_idletasks()
    w, h = root.winfo_reqwidth(), root.winfo_reqheight()
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")
    cp_btn.focus_set()
    root.grab_set(); root.mainloop()
    return result[0]

SPANISH_COUNTRIES = {
    "Spain","Mexico","Argentina","Colombia","Chile","Peru","Venezuela",
    "Ecuador","Bolivia","Paraguay","Uruguay","Costa Rica","Guatemala",
    "Honduras","El Salvador","Nicaragua","Panama","Cuba","Dominican Republic",
}

COUNTRY_ISO = {
    "France":"FR","Germany":"DE","Spain":"ES","Italy":"IT",
    "United Kingdom":"GB","Great Britain":"GB","Netherlands":"NL",
    "Belgium":"BE","Switzerland":"CH","Austria":"AT","Sweden":"SE",
    "Norway":"NO","Denmark":"DK","Finland":"FI","Poland":"PL",
    "Portugal":"PT","Greece":"GR","Australia":"AU","Canada":"CA",
    "United States":"US","Mexico":"MX","Brazil":"BR","Argentina":"AR",
}

GENDER_CONFIDENCE_THRESHOLD = 0.85


# ═══════════════════════════════════════════════════════════════════════════════
# PRODUCT CATALOG
# ═══════════════════════════════════════════════════════════════════════════════

def load_catalog():
    if os.path.exists(CATALOG_PATH):
        with open(CATALOG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"_next_id": 1, "skus": {}, "title_map": {}}

def save_catalog(catalog):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    content_str = json.dumps(catalog, ensure_ascii=False, indent=2)
    with open(CATALOG_PATH, 'w', encoding='utf-8') as f:
        f.write(content_str)
    _gh_put_file(GH_CAT_PATH, content_str, message="update product catalog")

def _next_sku(catalog):
    n = catalog["_next_id"]
    catalog["_next_id"] = n + 1
    return f"WIG-{n:03d}"

def find_sku_for_title(catalog, etsy_title):
    """Return (sku, entry) if Etsy title is mapped, else (None, None)."""
    key = (etsy_title or "").strip().lower()
    sku = catalog["title_map"].get(key)
    if sku and sku in catalog["skus"]:
        return sku, catalog["skus"][sku]
    return None, None

def find_similar_skus(catalog, etsy_title, threshold=0.55):
    """Return list of (score, sku, entry) for titles similar to etsy_title, sorted best first."""
    query = etsy_title.strip().lower()
    seen  = set()
    results = []
    for sku, entry in catalog["skus"].items():
        best = 0.0
        for title in entry.get("etsy_titles", []):
            s = SequenceMatcher(None, query, title.strip().lower()).ratio()
            best = max(best, s)
        s = SequenceMatcher(None, query, entry.get("name", "").lower()).ratio()
        best = max(best, s)
        if best >= threshold and sku not in seen:
            results.append((best, sku, entry))
            seen.add(sku)
    results.sort(reverse=True)
    return results

def ask_similar_or_new(catalog, etsy_title, similar_skus, parent=None):
    """
    Dialog: is the new Etsy title the same product as an existing SKU, or a new product?
    Returns (sku, entry).
    """
    result = [None, None]
    if parent and parent.winfo_exists():
        root = tk.Toplevel(parent)
    else:
        root = tk.Tk()
    root.title("New Product — Match?")
    root.attributes('-topmost', True); root.geometry("680x380"); root.resizable(True, True)

    tk.Label(root, text="New Etsy title:", font=('Arial', 10, 'bold'),
             pady=6, padx=12, anchor='w').pack(fill='x')
    tk.Label(root, text=etsy_title[:120], font=('Arial', 10), fg='#2980b9',
             padx=16, wraplength=640, anchor='w').pack(fill='x')
    tk.Label(root, text="Similar products in catalog — is it the same?",
             font=('Arial', 10, 'bold'), pady=8, padx=12, anchor='w').pack(fill='x')

    lf = tk.Frame(root); lf.pack(fill=tk.BOTH, expand=True, padx=12)
    cols = ('SKU', 'Name', 'Match %', 'Weight', 'Dims (LxWxH)')
    tree = ttk.Treeview(lf, columns=cols, show='headings', height=6)
    tree.column('SKU',          width=70,  anchor='w',      stretch=False)
    tree.column('Name',         width=280, anchor='w')
    tree.column('Match %',      width=70,  anchor='center', stretch=False)
    tree.column('Weight',       width=65,  anchor='center', stretch=False)
    tree.column('Dims (LxWxH)', width=110, anchor='center', stretch=False)
    for c in cols: tree.heading(c, text=c)
    sb = ttk.Scrollbar(lf, orient='vertical', command=tree.yview)
    tree.configure(yscrollcommand=sb.set); sb.pack(side=tk.RIGHT, fill=tk.Y)
    tree.pack(fill=tk.BOTH, expand=True)

    for score, sku, entry in similar_skus:
        dims = f"{entry.get('length_cm','')}×{entry.get('width_cm','')}×{entry.get('height_cm','')}"
        tree.insert('', 'end', iid=sku, values=(
            sku, entry.get('name', '')[:50], f"{score:.0%}",
            entry.get('weight_kg', ''), dims,
        ))
    if similar_skus:
        tree.selection_set(similar_skus[0][1])

    bf = tk.Frame(root); bf.pack(fill='x', padx=12, pady=8)

    def use_selected():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("No selection",
                                   "Select a product from the list or click 'New Product'.")
            return
        sku   = sel[0]
        entry = catalog["skus"][sku]
        link_title_to_sku(catalog, sku, etsy_title)
        result[0] = sku; result[1] = entry; root.destroy()

    def new_product():
        sku, entry = register_new_sku(catalog, name=etsy_title[:60],
                                      etsy_title=etsy_title,
                                      weight='', length='', width='', height='', value='')
        print(f"✓ New SKU auto-created: {sku}")
        result[0] = sku; result[1] = entry; root.destroy()

    tk.Button(bf, text="✓ Same product (use selected)", command=use_selected,
              bg='#27ae60', fg='white', font=('Arial', 10, 'bold'),
              relief='flat', padx=12, pady=5).pack(side=tk.LEFT, padx=4)
    tk.Button(bf, text="+ Different product (new SKU)", command=new_product,
              bg='#2980b9', fg='white', font=('Arial', 10, 'bold'),
              relief='flat', padx=12, pady=5).pack(side=tk.LEFT, padx=4)

    root.update_idletasks()
    w, h = root.winfo_reqwidth(), root.winfo_reqheight()
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")
    root.grab_set()
    if isinstance(root, tk.Toplevel):
        root.wait_window()
    else:
        root.mainloop()
    return result[0], result[1]

def auto_resolve_sku(catalog, etsy_title, parent=None):
    """
    Resolve or create a SKU for an Etsy title:
      - Exact match → return existing SKU silently
      - Fuzzy match → ask user (same product or different?)
      - No match    → auto-create new SKU silently
    Returns (sku, entry).
    """
    if not etsy_title:
        return None, None
    sku, entry = find_sku_for_title(catalog, etsy_title)
    if sku:
        return sku, entry
    similar = find_similar_skus(catalog, etsy_title, threshold=0.55)
    if similar:
        return ask_similar_or_new(catalog, etsy_title, similar, parent=parent)
    sku, entry = register_new_sku(catalog, name=etsy_title[:60],
                                  etsy_title=etsy_title,
                                  weight='', length='', width='', height='', value='')
    print(f"✓ New SKU auto-created: {sku} — {etsy_title[:50]}")
    return sku, entry

def register_new_sku(catalog, name, etsy_title, weight, length, width, height, value):
    """Create a new SKU entry. Returns (sku, entry)."""
    sku = _next_sku(catalog)
    entry = {
        "name": name,
        "etsy_titles": [etsy_title] if etsy_title else [],
        "weight_kg": weight,
        "length_cm": length,
        "width_cm":  width,
        "height_cm": height,
        "value_eur": value,
        "times_shipped": 0,
        "last_shipped":  None,
    }
    catalog["skus"][sku] = entry
    if etsy_title:
        catalog["title_map"][etsy_title.strip().lower()] = sku
    save_catalog(catalog)
    return sku, entry

def link_title_to_sku(catalog, sku, etsy_title):
    """Associate an additional Etsy title with an existing SKU."""
    key = etsy_title.strip().lower()
    catalog["title_map"][key] = sku
    titles = catalog["skus"][sku].setdefault("etsy_titles", [])
    if etsy_title not in titles:
        titles.append(etsy_title)
    save_catalog(catalog)

def bump_sku_shipment(catalog, sku):
    entry = catalog["skus"].get(sku)
    if entry:
        entry["times_shipped"] = entry.get("times_shipped", 0) + 1
        entry["last_shipped"]  = datetime.date.today().isoformat()
        save_catalog(catalog)

def bump_items_shipped(catalog, record):
    """Bump times_shipped for every catalog SKU in record['items'] (multi-item
    orders); falls back to record['sku'] for legacy single-item records."""
    skus = {it.get('sku') for it in record.get('items', []) if it.get('sku')}
    if not skus and record.get('sku'):
        skus = {record['sku']}
    for sku in skus:
        bump_sku_shipment(catalog, sku)

def _parse_num(value, default=0.0):
    """Parse a possibly Greek-comma-decimal numeric string; returns default on failure."""
    try:
        return float(str(value).strip().replace(',', '.'))
    except (ValueError, TypeError):
        return default


# ═══════════════════════════════════════════════════════════════════════════════
# CUSTOMER DB  (extended — backwards compatible)
# ═══════════════════════════════════════════════════════════════════════════════

def load_customer_db():
    if os.path.exists(CUSTOMER_DB_PATH):
        with open(CUSTOMER_DB_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_customer_db(db):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    content_str = json.dumps(db, ensure_ascii=False, indent=2)
    with open(CUSTOMER_DB_PATH, 'w', encoding='utf-8') as f:
        f.write(content_str)
    _gh_put_file(GH_DB_PATH, content_str, message="update customer db")

def customer_db_key(record):
    email = record.get('email', '').strip()
    return email.lower() if email else record.get('full_name', '').strip().lower()

def upsert_customer(record, sku=None, carrier="ELTA", tracking=None,
                    order_date=None, historical=False):
    """Save / update a customer record and append to order history."""
    db  = load_customer_db()
    key = customer_db_key(record)
    if not key:
        return

    today = order_date or datetime.date.today().isoformat()

    if key not in db:
        db[key] = {
            "full_name":   record.get("full_name", ""),
            "first_name":  record.get("first_name", ""),
            "last_name":   record.get("last_name", ""),
            "email":       record.get("email", ""),
            "phone":       record.get("phone", ""),
            "street_1":    record.get("street_1", ""),
            "street_number": record.get("street_number", ""),
            "street_2":    record.get("street_2", ""),
            "ship_city":   record.get("ship_city", ""),
            "ship_state":  record.get("ship_state", ""),
            "ship_zipcode":record.get("ship_zipcode", ""),
            "ship_country":record.get("ship_country", ""),
            "orders":      [],
            "total_orders":0,
            "total_spent": 0.0,
        }

    order_entry = {
        "date":         today,
        "order_id":     record.get("order_id", ""),
        "sku":          sku or "",
        "product_name": record.get("product_name", ""),
        "value_eur":    record.get("value_eur", ""),
        "carrier":      carrier,
        "tracking":     tracking or "",
        "historical":   historical,
    }
    # Deduplication: skip append if this order_id was already recorded
    existing_ids = {o.get("order_id", "") for o in db[key].get("orders", [])}
    if order_entry["order_id"] and order_entry["order_id"] in existing_ids:
        # Same order seen again — only refresh address fields
        for field in ("street_1","street_number","street_2","ship_city",
                      "ship_state","ship_zipcode","ship_country","phone"):
            if record.get(field):
                db[key][field] = record[field]
        save_customer_db(db)
        return

    db[key]["orders"].append(order_entry)
    db[key]["total_orders"] = len(db[key]["orders"])
    try:
        db[key]["total_spent"] = round(sum(
            float(str(o.get("value_eur") or 0).replace(",", "."))
            for o in db[key]["orders"]
        ), 2)
    except Exception:
        pass

    # Refresh address fields from the latest record
    for field in ("street_1","street_number","street_2","ship_city",
                  "ship_state","ship_zipcode","ship_country","phone"):
        if record.get(field):
            db[key][field] = record[field]

    save_customer_db(db)


def save_customer_address(record):
    """Pre-save customer address to DB during review, before label printing.
    Creates the DB entry (or refreshes address fields) without adding an order entry.
    If label printing later fails, the address is still available for the next session."""
    db  = load_customer_db()
    key = customer_db_key(record)
    if not key:
        return
    if key not in db:
        db[key] = {
            "full_name":     record.get("full_name", ""),
            "first_name":    record.get("first_name", ""),
            "last_name":     record.get("last_name", ""),
            "email":         record.get("email", ""),
            "phone":         record.get("phone", ""),
            "street_1":      record.get("street_1", ""),
            "street_number": record.get("street_number", ""),
            "street_2":      record.get("street_2", ""),
            "ship_city":     record.get("ship_city", ""),
            "ship_state":    record.get("ship_state", ""),
            "ship_zipcode":  record.get("ship_zipcode", ""),
            "ship_country":  record.get("ship_country", ""),
            "orders":        [],
            "total_orders":  0,
            "total_spent":   0.0,
        }
    else:
        for field in ("full_name", "first_name", "last_name", "email", "phone",
                      "street_1", "street_number", "street_2",
                      "ship_city", "ship_state", "ship_zipcode", "ship_country"):
            if record.get(field):
                db[key][field] = record[field]
    save_customer_db(db)


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def strip_accents(text):
    text = str(text).replace('ß', 'ss').replace('SS', 'SS').replace('\u2018', ' ').replace('\u2019', ' ')
    text = text.replace('Ł', 'L').replace('ł', 'l')
    nfkd = unicodedata.normalize('NFKD', text)
    return ''.join(c for c in nfkd if not unicodedata.combining(c))


# ═══════════════════════════════════════════════════════════════════════════════
# ETSY ORDER PARSER
# ═══════════════════════════════════════════════════════════════════════════════

def load_orders_from_html(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()

    if not html.strip():
        raise ValueError("EMPTY_FILE")

    start = html.find('Etsy.Context=')
    if start == -1:
        raise ValueError("WRONG_FORMAT")
    start = html.find('{', start)
    depth = 0; end = start
    for i, c in enumerate(html[start:], start):
        if c == '{': depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0: end = i + 1; break

    data   = json.loads(html[start:end])
    search = data['data']['initial_data']['orders']['orders_search']
    orders = search['orders']
    buyers = {b['buyer_id']: b for b in search['buyers']}

    records = []
    for order in orders:
        if order.get('is_canceled'):
            continue

        addr  = order['fulfillment']['to_address']
        buyer = buyers.get(order['buyer_id'], {})

        full_name = addr.get('name', '').strip()
        parts     = full_name.rsplit(' ', 1)
        first_name = parts[0] if len(parts) == 2 else full_name
        last_name  = parts[1] if len(parts) == 2 else ''

        street = addr.get('first_line', '').strip()
        lead   = re.match(r'^(\d+)([^\s\d][^\s]*)?\s+(.*)', street)
        trail  = re.match(r'^(.*\S)\s+(\d+)([^\s\d][^\s]*)?$', street)
        trail2 = re.match(r'^(.*\S)\s+(\d+)\s+([A-Za-z]{1,4})$', street)

        if lead:
            street_number = lead.group(1)
            suffix        = lead.group(2) or ''
            rest          = lead.group(3).strip()
            street_name   = (suffix + ' ' + rest).strip() if suffix else rest
        elif trail:
            rest          = trail.group(1).strip()
            street_number = trail.group(2)
            suffix        = trail.group(3) or ''
            street_name   = (suffix + ' ' + rest).strip() if suffix else rest
        elif trail2:
            rest          = trail2.group(1).strip()
            street_number = trail2.group(2)
            suffix        = trail2.group(3)
            street_name   = (suffix + ' ' + rest).strip()
        else:
            street_number = '0'
            street_name   = street

        # Extract item titles from the order (for SKU matching)
        etsy_items = []
        for src in ('listings', 'transactions', 'items'):
            items = order.get(src, [])
            if items:
                for item in items:
                    title = item.get('title') or item.get('listing_title') or ''
                    if title:
                        etsy_items.append(title.strip())
                break
        etsy_title = " AND ".join(etsy_items) if etsy_items else ""

        # Order total value
        try:
            total_val = str(order.get('total', {}).get('amount', '') or '')
            if not total_val:
                total_val = str(order.get('grandtotal', {}).get('amount', '') or '')
        except Exception:
            total_val = ""

        records.append({
            'order_id':      str(order['order_id']),
            'full_name':     full_name,
            'first_name':    first_name,
            'last_name':     last_name,
            'street_1':      street_name,
            'street_number': street_number,
            'street_2':      addr.get('second_line', ''),
            'ship_city':     addr.get('city', ''),
            'ship_state':    addr.get('state') or addr.get('region') or addr.get('province', ''),
            'ship_zipcode':  addr.get('zip', ''),
            'ship_country':  addr.get('country', ''),
            'email':         buyer.get('email', ''),
            'phone':         addr.get('phone', ''),
            'buyer':         buyer.get('username', ''),
            'etsy_title':    etsy_title,
            'etsy_items':    etsy_items,
            'value_eur':     total_val,
            'print_label':   True,
            'carrier':       'ELTA',
            'sku':           '',
            'product_name':  '',
            'weight_kg':     '0,49',
            'length_cm':     '21',
            'width_cm':      '28',
            'height_cm':     '12',
            'customs_qty':   '2',
        })

    print(f"✓ Loaded {len(records)} orders from {os.path.basename(filepath)}")
    return records


# ═══════════════════════════════════════════════════════════════════════════════
# UI DIALOGS
# ═══════════════════════════════════════════════════════════════════════════════

def ask_for_orders_file():
    root = tk.Tk(); root.withdraw(); root.attributes('-topmost', True)
    path = filedialog.askopenfilename(
        title='Select Etsy orders file',
        initialdir=OUTPUT_DIR,
        filetypes=[('HTML/Text files', '*.txt *.html *.htm'), ('All files', '*.*')]
    )
    root.destroy()
    if not path:
        default = os.path.join(OUTPUT_DIR, 'orders.txt')
        if os.path.exists(default):
            return default
        raise SystemExit("No orders file selected.")
    return path

def wait_for_user(message):
    root = tk.Tk(); root.title("⚠ Action Required")
    root.attributes('-topmost', True); root.lift(); root.focus_force()
    root.resizable(False, False)
    tk.Label(root, text=message, wraplength=440, justify='left',
             pady=12, padx=16, font=('Arial', 11)).pack()
    tk.Button(root, text="✓ Done — Continue", command=root.destroy,
              bg='#27ae60', fg='white', font=('Arial', 11, 'bold'),
              relief='flat', padx=12, pady=6, cursor='hand2').pack(pady=(4, 14))
    root.update_idletasks()
    w, h = root.winfo_reqwidth(), root.winfo_reqheight()
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")
    root.grab_set(); root.mainloop()

def click_with_retry(driver, by, selector, description, retries=2, delay=1.0, timeout=10,
                      use_js_fallback=True):
    """Standard resilience pattern (added 2026-08-19, fixed 2026-08-20, see
    feedback_automation_retry_pattern in project memory): never let a
    single click crash the run. Retry a couple of times first (covers
    transient overlays/toasts like the one that blocked Zonos's
    'Add another item' button on the Stephen Duff order) — if it still
    won't go through, pause and let the user complete that step by hand in
    the browser, then trust it's done and move on to the next step, same as
    elta6.01's pause/Next pattern. Does NOT click again after the pause —
    for toggle-type elements (e.g. a checkbox) re-clicking after the user
    already fixed it would just undo their fix.

    Added 2026-08-20: on any failed native click, tries a JS-dispatched
    click before sleeping/retrying. Recurring live pattern this session —
    Save item, the Made-in option, and Continue-to-payment all failed with
    "is not clickable at point (x,y) because another element ... obscures
    it" (ElementClickInterceptedException) even though the button was
    visibly fine — a sticky footer/wrapper div sits at the same on-screen
    point. Selenium's native .click() refuses to click through that; a JS
    click (element.click() dispatched directly, no visibility/topmost-
    element check) goes through anyway.

    use_js_fallback=False for react-select combobox triggers (Made-in,
    ship-from, ship-to): a JS click doesn't fire React's open-dropdown
    handler at all (already known — see the comment at the Made-in call
    site), so it reports "success" (no exception) while nothing actually
    opened. The caller then types into whatever field was last focused
    instead, corrupting it (live 2026-08-20, Brett Johnson order: "Greece"
    landed in the HS-code field as a stray "Gr", since the Made-in click's
    JS fallback silently did nothing and left focus on the HS-code input).
    For these, a failed native click should go straight to retry/pause
    instead of a JS click that only fakes success."""
    last_err = None
    for _ in range(retries):
        try:
            el = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((by, selector)))
            el.click()
            return el
        except Exception as e:
            last_err = e
            if use_js_fallback:
                try:
                    js_el = driver.find_element(by, selector)
                    driver.execute_script("arguments[0].click();", js_el)
                    return js_el
                except Exception:
                    pass
            time.sleep(delay)
    wait_for_user(f"Problem: {description}\n{last_err}\n\n"
                  f"Please complete this step manually in the browser, "
                  f"then click Done to continue.")
    return None

def find_with_wait(driver, by, selector, description, retries=2, delay=1.0, timeout=10):
    """Same resilience pattern as click_with_retry (see feedback_automation_
    retry_pattern in project memory), but for locating a field to type into
    rather than clicking. Added 2026-08-20: zonos_add_item's description/
    value/HS-code fields were being grabbed with a raw driver.find_element()
    and no wait at all — the one call in this whole flow that could still
    throw instantly (e.g. right after a manual-fix pause, before the item
    form has finished re-rendering) and escape past every other per-step
    safety net into the outer per-order handler, abandoning the rest of
    that order's items. Retries with a wait first; if the field still isn't
    there, pauses for the user to sort it out by hand, then looks one more
    time (raises if it's genuinely still missing, since there's no click to
    skip past — the caller can't type into nothing)."""
    last_err = None
    for _ in range(retries):
        try:
            return WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((by, selector)))
        except Exception as e:
            last_err = e
            time.sleep(delay)
    wait_for_user(f"Problem: {description}\n{last_err}\n\n"
                  f"Please complete this step manually in the browser, "
                  f"then click Done to continue.")
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, selector)))

def ask_yes_no(question):
    result = [False]
    root = tk.Tk(); root.title("Question")
    root.attributes('-topmost', True); root.lift(); root.resizable(False, False)
    tk.Label(root, text=question, wraplength=420, justify='left',
             pady=14, padx=16, font=('Arial', 11)).pack()
    bf = tk.Frame(root); bf.pack(pady=(4, 14))
    tk.Button(bf, text="Yes", command=lambda:(result.__setitem__(0,True),root.destroy()),
              bg='#27ae60', fg='white', font=('Arial',11,'bold'), relief='flat',
              padx=20, pady=6, cursor='hand2').pack(side=tk.LEFT, padx=8)
    tk.Button(bf, text="No",  command=root.destroy,
              bg='#e74c3c', fg='white', font=('Arial',11,'bold'), relief='flat',
              padx=20, pady=6, cursor='hand2').pack(side=tk.LEFT, padx=8)
    root.update_idletasks()
    w, h = root.winfo_reqwidth(), root.winfo_reqheight()
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")
    root.grab_set(); root.mainloop()
    return result[0]

def show_customer_update_dialog(record, stored, parent=None):
    """
    Show stored vs incoming address. Returns (action, save_to_db):
      action = 'keep'  → use stored address
      action = 'new'   → use incoming address
      save_to_db = True → persist the new address to the customer DB
    """
    FIELDS = [
        ('street_1',      'Street'),
        ('street_number', 'Number'),
        ('street_2',      'Street 2'),
        ('ship_city',     'City'),
        ('ship_state',    'State'),
        ('ship_zipcode',  'ZIP'),
        ('ship_country',  'Country'),
        ('phone',         'Phone'),
    ]
    has_diff = any(
        str(stored.get(f, '') or '') != str(record.get(f, '') or '')
        for f, _ in FIELDS
    )
    result = ['keep', False]

    if parent:
        root = tk.Toplevel(parent)
        root.transient(parent)
    else:
        root = tk.Tk()
    root.title("Returning Customer")
    root.attributes('-topmost', True); root.resizable(True, True)

    name   = record.get('full_name', '')
    orders = stored.get('total_orders', 0)
    spent  = stored.get('total_spent', 0.0)

    tk.Label(root, text=f"Returning customer: {name}",
             font=('Arial', 12, 'bold'), pady=10, padx=16).pack(anchor='w')
    tk.Label(root, text=f"Past orders: {orders}   Total spent: €{spent:.2f}",
             font=('Arial', 10), fg='#555', padx=16).pack(anchor='w')

    if has_diff:
        tk.Label(root, text="Address differences (highlighted):",
                 font=('Arial', 10, 'bold'), pady=6, padx=16).pack(anchor='w')
        gf = tk.Frame(root, padx=16); gf.pack(fill='x', pady=4)
        for col, text in enumerate(("Field", "Stored", "New (from Etsy)")):
            tk.Label(gf, text=text, width=14 if col==0 else 30,
                     font=('Arial', 9, 'bold'), anchor='w').grid(
                         row=0, column=col, padx=4, sticky='w')
        for i, (field, label) in enumerate(FIELDS, start=1):
            sv  = str(stored.get(field, '') or '')
            nv  = str(record.get(field, '') or '')
            chg = sv != nv
            bg  = '#fff3cd' if chg else '#f8f9fa'
            tk.Label(gf, text=label, width=14, anchor='w', bg=bg,
                     font=('Arial', 9)).grid(row=i, column=0, padx=4, pady=1, sticky='ew')
            tk.Label(gf, text=sv[:38], width=30, anchor='w', bg=bg,
                     font=('Arial', 9)).grid(row=i, column=1, padx=4, pady=1, sticky='ew')
            tk.Label(gf, text=nv[:38], width=30, anchor='w', bg=bg,
                     font=('Arial', 9, 'bold') if chg else ('Arial', 9)).grid(
                         row=i, column=2, padx=4, pady=1, sticky='ew')
    else:
        tk.Label(root, text="Address matches stored data — no differences.",
                 font=('Arial', 10), fg='#27ae60', padx=16, pady=8).pack(anchor='w')

    bf = tk.Frame(root); bf.pack(fill='x', padx=16, pady=12)

    def keep_stored():   result[0]='keep'; result[1]=False; root.destroy()
    def new_session():   result[0]='new';  result[1]=False; root.destroy()
    def new_and_save():  result[0]='new';  result[1]=True;  root.destroy()

    tk.Button(bf, text="Keep stored address", command=keep_stored,
              bg='#27ae60', fg='white', font=('Arial', 10, 'bold'),
              relief='flat', padx=10, pady=5).pack(side=tk.LEFT, padx=4)
    if has_diff:
        tk.Button(bf, text="Use new (this shipment only)", command=new_session,
                  bg='#e67e22', fg='white', font=('Arial', 10, 'bold'),
                  relief='flat', padx=10, pady=5).pack(side=tk.LEFT, padx=4)
        tk.Button(bf, text="Use new + Save to DB", command=new_and_save,
                  bg='#c0392b', fg='white', font=('Arial', 10, 'bold'),
                  relief='flat', padx=10, pady=5).pack(side=tk.LEFT, padx=4)

    root.update_idletasks()
    w, h = root.winfo_reqwidth(), root.winfo_reqheight()
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")
    root.grab_set()
    if parent:
        parent.wait_window(root)
    else:
        root.mainloop()
    return result[0], result[1]


# ═══════════════════════════════════════════════════════════════════════════════
# FROM-DB MODE  &  STANDALONE DB MANAGER
# ═══════════════════════════════════════════════════════════════════════════════

def pick_customers_from_db():
    """Show customer list and return a list of selected customer dicts (multi-select)."""
    result = [[]]
    db_cache = [{}]

    root = tk.Tk(); root.title("Select Customers — From Database")
    root.geometry("1000x620"); root.attributes('-topmost', True)

    tk.Label(root,
             text="Select one or more customers (Ctrl+Click / Shift+Click for multiple):",
             font=('Arial', 11, 'bold'), pady=8, padx=10).pack(anchor='w')

    top = tk.Frame(root); top.pack(fill=tk.X, padx=10, pady=2)
    tk.Label(top, text="Search:", font=('Arial', 10)).pack(side=tk.LEFT)
    search_var = tk.StringVar()
    tk.Entry(top, textvariable=search_var, width=36,
             font=('Arial', 10)).pack(side=tk.LEFT, padx=6)

    tf = tk.Frame(root); tf.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)
    cols = ('Name', 'Email', 'Country', 'State', 'City', 'Orders', 'Spent')
    tree = ttk.Treeview(tf, columns=cols, show='headings', selectmode='extended')
    tree.column('Name',    width=190, anchor='w')
    tree.column('Email',   width=190, anchor='w')
    tree.column('Country', width=100, anchor='w',      stretch=False)
    tree.column('State',   width=70,  anchor='w',      stretch=False)
    tree.column('City',    width=120, anchor='w',      stretch=False)
    tree.column('Orders',  width=55,  anchor='center', stretch=False)
    tree.column('Spent',   width=80,  anchor='center', stretch=False)
    for c in cols: tree.heading(c, text=c)
    sb = ttk.Scrollbar(tf, orient='vertical', command=tree.yview)
    tree.configure(yscrollcommand=sb.set); sb.pack(side=tk.RIGHT, fill=tk.Y)
    tree.pack(fill=tk.BOTH, expand=True)

    count_lbl = tk.Label(root, text="", font=('Arial', 9), fg='#555')
    count_lbl.pack(anchor='w', padx=12)

    def load(ft=''):
        tree.delete(*tree.get_children())
        db = load_customer_db()
        db_cache[0] = db
        ft = ft.strip().lower()
        rows = []
        for key, c in db.items():
            name    = c.get('full_name') or key
            email   = c.get('email', '')
            country = c.get('ship_country', '')
            state   = c.get('ship_state', '')
            city    = c.get('ship_city', '')
            orders  = c.get('total_orders', 0)
            spent   = c.get('total_spent', 0.0)
            if ft and ft not in name.lower() and ft not in email.lower() \
                   and ft not in country.lower() and ft not in city.lower() \
                   and ft not in state.lower():
                continue
            rows.append((key, name, email, country, state, city, orders, spent))
        rows.sort(key=lambda r: r[1].lower())
        for key, name, email, country, state, city, orders, spent in rows:
            tree.insert('', 'end', iid=key, values=(
                name, email, country, state, city, orders, f"€{spent:.2f}"))
        count_lbl.config(text=f"{len(rows)} customer(s)")

    search_var.trace_add('write', lambda *_: load(search_var.get()))
    load()

    def select():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Select at least one customer.", parent=root)
            return
        result[0] = [db_cache[0][k] for k in sel if k in db_cache[0]]
        root.destroy()

    tree.bind('<Double-1>', lambda e: select())

    bf = tk.Frame(root); bf.pack(fill=tk.X, padx=10, pady=8)
    tk.Button(bf, text="Cancel", command=root.destroy,
              bg='#95a5a6', fg='white', font=('Arial', 10, 'bold'),
              relief='flat', padx=12, pady=6).pack(side=tk.LEFT, padx=4)
    sel_lbl = tk.Label(bf, text="0 selected", font=('Arial', 10), fg='#555')
    sel_lbl.pack(side=tk.LEFT, padx=16)
    tree.bind('<<TreeviewSelect>>',
              lambda e: sel_lbl.config(text=f"{len(tree.selection())} selected"))
    tk.Button(bf, text="✓  Use Selected Customer(s)", command=select,
              bg='#27ae60', fg='white', font=('Arial', 11, 'bold'),
              relief='flat', padx=18, pady=6, cursor='hand2').pack(side=tk.RIGHT, padx=4)

    root.grab_set(); root.mainloop()
    return result[0]


def open_db_manager():
    """Standalone DB manager — customers and products."""
    root = tk.Tk(); root.title("ELTA — Database Manager")
    root.resizable(False, False); root.attributes('-topmost', True)

    tk.Label(root, text="Database Manager",
             font=('Arial', 14, 'bold'), pady=18, padx=30).pack()

    bf = tk.Frame(root); bf.pack(padx=30, pady=4)
    tk.Button(bf, text="👥   Customer Database",
              command=lambda: CustomerListWindow(root),
              bg='#2980b9', fg='white', font=('Arial', 12, 'bold'),
              relief='flat', padx=24, pady=12, cursor='hand2', width=26).pack(pady=6)
    tk.Button(bf, text="📦   Product Catalog",
              command=lambda: ProductCatalogWindow(root),
              bg='#16a085', fg='white', font=('Arial', 12, 'bold'),
              relief='flat', padx=24, pady=12, cursor='hand2', width=26).pack(pady=6)
    tk.Button(bf, text="Close", command=root.destroy,
              bg='#95a5a6', fg='white', font=('Arial', 10, 'bold'),
              relief='flat', padx=16, pady=6).pack(pady=(16, 20))

    root.grab_set(); root.mainloop()


def ask_run_mode():
    """Returns 'live', 'historical', 'from_db', or 'db_manager'."""
    result = ['live']
    root = tk.Tk(); root.title("ELTA_Damon2.9 — Mode")
    root.attributes('-topmost', True); root.resizable(False, False)
    tk.Label(root, text="Choose processing mode:",
             font=('Arial', 13, 'bold'), pady=16, padx=20).pack()
    bf = tk.Frame(root); bf.pack(pady=(0, 18), padx=20)
    def pick(v): result[0]=v; root.destroy()
    tk.Button(bf, text="▶  Live Processing\n(shipment CSV, letters)",
              command=lambda: pick('live'),
              bg='#2980b9', fg='white', font=('Arial',11,'bold'),
              relief='flat', padx=20, pady=10, cursor='hand2', width=28).pack(pady=6)
    tk.Button(bf, text="📂  Historical Import\n(data only — no CSV)",
              command=lambda: pick('historical'),
              bg='#7f8c8d', fg='white', font=('Arial',11,'bold'),
              relief='flat', padx=20, pady=10, cursor='hand2', width=28).pack(pady=6)
    tk.Button(bf, text="👤  From Database\n(label / letter for stored customer)",
              command=lambda: pick('from_db'),
              bg='#8e44ad', fg='white', font=('Arial',11,'bold'),
              relief='flat', padx=20, pady=10, cursor='hand2', width=28).pack(pady=6)
    tk.Button(bf, text="🗄  Manage Database\n(view, add, edit, delete)",
              command=lambda: pick('db_manager'),
              bg='#16a085', fg='white', font=('Arial',11,'bold'),
              relief='flat', padx=20, pady=10, cursor='hand2', width=28).pack(pady=6)
    root.update_idletasks()
    w, h = root.winfo_reqwidth(), root.winfo_reqheight()
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")
    root.grab_set(); root.mainloop()
    return result[0]

def ask_what_to_run():
    """Checklist: Zonos Prep / Shipment CSV / Thank-you Notes.
    Returns {'mode': 'both'|'labels'|'letters', 'zonos': bool}."""
    result = {}
    root = tk.Tk(); root.title("ELTA_Damon2.9 — What do you need?")
    root.attributes('-topmost', True); root.resizable(False, False)
    tk.Label(root, text="What do you need for this run?", font=('Arial',12,'bold'),
             pady=14, padx=20).pack()
    zonos_var   = tk.BooleanVar(value=False)
    labels_var  = tk.BooleanVar(value=True)
    letters_var = tk.BooleanVar(value=True)
    cf = tk.Frame(root); cf.pack(padx=20, pady=(0,4), anchor='w')
    tk.Checkbutton(cf, text="Zonos Prep (automated, US orders only)", variable=zonos_var,
                   font=('Arial',11)).pack(anchor='w', pady=2)
    tk.Checkbutton(cf, text="Shipment CSV (ELTA bulk-upload row)", variable=labels_var,
                   font=('Arial',11)).pack(anchor='w', pady=2)
    tk.Checkbutton(cf, text="Thank-you Notes", variable=letters_var,
                   font=('Arial',11)).pack(anchor='w', pady=2)
    def go():
        if not labels_var.get() and not letters_var.get() and not zonos_var.get():
            messagebox.showwarning("Pick something",
                "Select at least Zonos Prep, Shipment CSV, or Thank-you Notes.")
            return
        if labels_var.get() and letters_var.get(): m = 'both'
        elif labels_var.get(): m = 'labels'
        elif letters_var.get(): m = 'letters'
        else: m = 'none'
        result['mode']  = m
        result['zonos'] = zonos_var.get()
        root.destroy()
    tk.Button(root, text="Continue", command=go, bg='#2980b9', fg='white',
              font=('Arial',11,'bold'), relief='flat', padx=16, pady=8,
              cursor='hand2').pack(pady=(8,18))
    root.update_idletasks()
    w, h = root.winfo_reqwidth(), root.winfo_reqheight()
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")
    root.grab_set(); root.mainloop()
    if not result:
        raise SystemExit("Aborted.")
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# ORDER SELECTION TABLE
# ═══════════════════════════════════════════════════════════════════════════════

def show_order_selection(records):
    selected = []
    root = tk.Tk(); root.title("ELTA_Damon2.9 — Order Selection")
    root.attributes('-topmost', True); root.geometry("1150x580"); root.resizable(True, True)

    tk.Label(root, text="Select orders to process (all ship ELTA):",
             font=('Arial', 11, 'bold'), pady=8).pack()

    tf = tk.Frame(root); tf.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)
    cols = ('#', 'Name', 'Country', 'City', 'Street', 'ZIP')
    tree = ttk.Treeview(tf, columns=cols, show='headings', selectmode='none')

    tree.column('#',       width=30,  anchor='center', stretch=False)
    tree.column('Name',    width=200, anchor='w')
    tree.column('Country', width=120, anchor='w')
    tree.column('City',    width=120, anchor='w')
    tree.column('Street',  width=220, anchor='w')
    tree.column('ZIP',     width=70,  anchor='w')
    for c in cols: tree.heading(c, text=c)

    sb = ttk.Scrollbar(tf, orient='vertical', command=tree.yview)
    tree.configure(yscrollcommand=sb.set); sb.pack(side=tk.RIGHT, fill=tk.Y)
    tree.pack(fill=tk.BOTH, expand=True)

    tree.tag_configure('checked',   background='#d4edda')
    tree.tag_configure('unchecked', background='#f8f9fa')

    checked = {}

    def row_tag(iid):
        return 'checked' if checked.get(iid) else 'unchecked'

    def refresh(iid):
        tree.item(iid, tags=(row_tag(iid),))
        vals = list(tree.item(iid,'values'))
        vals[0] = '✓' if checked[iid] else '☐'
        tree.item(iid, values=vals)

    def on_click(event):
        iid = tree.identify_row(event.y)
        if not iid: return
        checked[iid] = not checked[iid]
        refresh(iid); update_count()

    tree.bind('<Button-1>', on_click)
    count_var = tk.StringVar()

    def update_count():
        n = sum(1 for v in checked.values() if v)
        count_var.set(f"{n} selected")

    for i, r in enumerate(records):
        name    = f"{r.get('first_name','')} {r.get('last_name','')}".strip()
        country = r.get('ship_country', '')
        street  = f"{r.get('street_1','')} {r.get('street_number','')}".strip()
        iid     = str(i)
        checked[iid] = True
        tree.insert('', 'end', iid=iid, values=(
            '✓' if checked[iid] else '☐',
            name, country, r.get('ship_city',''), street,
            r.get('ship_zipcode',''),
        ))
        tree.item(iid, tags=(row_tag(iid),))
    update_count()

    bf = tk.Frame(root); bf.pack(fill=tk.X, padx=10, pady=6)

    def select_all():
        for iid in checked: checked[iid]=True; refresh(iid)
        update_count()
    def deselect_all():
        for iid in checked: checked[iid]=False; refresh(iid)
        update_count()
    def toggle_usa():
        usa = [str(i) for i,r in enumerate(records)
               if r.get('ship_country','') in USA_COUNTRY_VALUES]
        any_on = any(checked[iid] for iid in usa)
        for iid in usa: checked[iid]=not any_on; refresh(iid)
        update_count()
    def proceed():
        for i, r in enumerate(records):
            iid = str(i)
            if checked.get(iid):
                r['carrier'] = 'ELTA'
                selected.append(r)
        root.destroy()

    tk.Button(bf, text="Select All",    command=select_all,
              bg='#27ae60',fg='white',font=('Arial',10,'bold'),relief='flat',padx=10,pady=5).pack(side=tk.LEFT,padx=4)
    tk.Button(bf, text="Deselect All",  command=deselect_all,
              bg='#c0392b',fg='white',font=('Arial',10,'bold'),relief='flat',padx=10,pady=5).pack(side=tk.LEFT,padx=4)
    tk.Button(bf, text="Toggle USA",    command=toggle_usa,
              bg='#e67e22',fg='white',font=('Arial',10,'bold'),relief='flat',padx=10,pady=5).pack(side=tk.LEFT,padx=4)
    tk.Button(bf, text="Customers", command=lambda: CustomerListWindow(root),
              bg='#8e44ad', fg='white', font=('Arial',10,'bold'),
              relief='flat', padx=10, pady=5).pack(side=tk.LEFT, padx=4)
    tk.Button(bf, text="Products",  command=lambda: ProductCatalogWindow(root),
              bg='#16a085', fg='white', font=('Arial',10,'bold'),
              relief='flat', padx=10, pady=5).pack(side=tk.LEFT, padx=4)
    tk.Label(bf, textvariable=count_var, font=('Arial',10),fg='#333').pack(side=tk.LEFT,padx=16)
    tk.Button(bf, text="▶  Continue",  command=proceed,
              bg='#2980b9',fg='white',font=('Arial',11,'bold'),relief='flat',padx=18,pady=6).pack(side=tk.RIGHT,padx=6)

    root.grab_set(); root.mainloop()
    return selected


# ═══════════════════════════════════════════════════════════════════════════════
# SKU ASSIGNMENT DIALOG
# ═══════════════════════════════════════════════════════════════════════════════

def ask_items(catalog, etsy_title="", current_items=None, parent=None):
    """
    Show a dialog to assign one or more product items to an order.
    Each item is either an existing catalog SKU, a brand-new catalog SKU
    (saved permanently), or a one-off description (this order only — never
    written to product_catalog.json).
    Returns a list of item dicts, or None if the user cancelled/skipped.
    Item dict: {'sku','name','qty','weight_kg','value_eur','is_custom'}
    """
    result = [None]
    items = list(current_items) if current_items else []

    if parent and parent.winfo_exists():
        root = tk.Toplevel(parent)
    else:
        root = tk.Tk()
    root.title("Assign Products to This Order")
    root.attributes('-topmost', True); root.resizable(True, True)

    tk.Label(root, text="Assign product(s) to this order",
             font=('Arial',12,'bold'), pady=10).pack()
    if etsy_title:
        tk.Label(root, text=f"Etsy title: {etsy_title[:80]}",
                 font=('Arial',9), fg='#555', wraplength=560).pack()

    # Search bar
    sf = tk.Frame(root); sf.pack(fill=tk.X, padx=10, pady=6)
    tk.Label(sf, text="Search:", font=('Arial',10)).pack(side=tk.LEFT)
    search_var = tk.StringVar()
    se = tk.Entry(sf, textvariable=search_var, width=40, font=('Arial',10))
    se.pack(side=tk.LEFT, padx=6)

    # SKU list
    lf = tk.Frame(root); lf.pack(fill=tk.BOTH, expand=True, padx=10)
    cols = ('SKU', 'Name', 'Dims (LxWxH)', 'Weight', 'Value', 'Shipped')
    tree = ttk.Treeview(lf, columns=cols, show='headings', height=8)
    tree.column('SKU',         width=70,  anchor='w', stretch=False)
    tree.column('Name',        width=200, anchor='w')
    tree.column('Dims (LxWxH)',width=100, anchor='center', stretch=False)
    tree.column('Weight',      width=65,  anchor='center', stretch=False)
    tree.column('Value',       width=65,  anchor='center', stretch=False)
    tree.column('Shipped',     width=60,  anchor='center', stretch=False)
    for c in cols: tree.heading(c, text=c)
    sb = ttk.Scrollbar(lf, orient='vertical', command=tree.yview)
    tree.configure(yscrollcommand=sb.set); sb.pack(side=tk.RIGHT, fill=tk.Y)
    tree.pack(fill=tk.BOTH, expand=True)

    def populate(filter_text=""):
        tree.delete(*tree.get_children())
        ft = filter_text.lower()
        for sku, e in catalog["skus"].items():
            name = e.get("name","")
            if ft and ft not in sku.lower() and ft not in name.lower():
                continue
            dims = f"{e.get('length_cm','')}×{e.get('width_cm','')}×{e.get('height_cm','')}"
            tree.insert('', 'end', iid=sku, values=(
                sku, name, dims,
                e.get('weight_kg',''), e.get('value_eur',''),
                e.get('times_shipped',0),
            ))

    populate()
    search_var.trace_add('write', lambda *_: populate(search_var.get()))

    # Quantity used by whichever "Add" button is pressed
    qf = tk.Frame(root); qf.pack(fill=tk.X, padx=10, pady=(4,0))
    tk.Label(qf, text="Qty for next Add:", font=('Arial',9,'bold')).pack(side=tk.LEFT)
    qty_var = tk.StringVar(value="1")
    tk.Entry(qf, textvariable=qty_var, width=5, font=('Arial',9)).pack(side=tk.LEFT, padx=6)

    # Optional comment appended to the SELECTED catalog item's description
    # for this order only — the catalog entry's own name is never changed.
    tk.Label(qf, text="Comment for next Add Selected (optional):", font=('Arial',9,'bold')).pack(side=tk.LEFT, padx=(16,0))
    comment_var = tk.StringVar()
    tk.Entry(qf, textvariable=comment_var, width=35, font=('Arial',9)).pack(side=tk.LEFT, padx=6)

    # New product form (saved permanently to the catalog)
    nf = ttk.LabelFrame(root, text="  Create new product (saved to catalog)  ", padding=8)
    nf.pack(fill=tk.X, padx=10, pady=4)

    fields_new = {}
    new_rows = [
        ("Name",    "name",   30),
        ("Weight",  "weight", 8),
        ("Length",  "length", 8),
        ("Width",   "width",  8),
        ("Height",  "height", 8),
        ("Value €", "value",  8),
    ]
    for col, (lbl, key, w) in enumerate(new_rows):
        tk.Label(nf, text=lbl, font=('Arial',9)).grid(row=0,column=col*2,padx=(8,2))
        e = tk.Entry(nf, width=w, font=('Arial',9))
        e.grid(row=0, column=col*2+1, padx=(0,6))
        fields_new[key] = e
    fields_new["name"].config(width=22)
    if etsy_title: fields_new["name"].insert(0, etsy_title[:50])

    # One-off form (this order only — never written to the catalog)
    of = ttk.LabelFrame(root, text="  One-off item (this order only — not saved to catalog)  ", padding=8)
    of.pack(fill=tk.X, padx=10, pady=4)

    fields_oneoff = {}
    oneoff_rows = [
        ("Description", "name",   30),
        ("Weight",      "weight", 8),
        ("Value €",     "value",  8),
    ]
    for col, (lbl, key, w) in enumerate(oneoff_rows):
        tk.Label(of, text=lbl, font=('Arial',9)).grid(row=0,column=col*2,padx=(8,2))
        e = tk.Entry(of, width=w, font=('Arial',9))
        e.grid(row=0, column=col*2+1, padx=(0,6))
        fields_oneoff[key] = e
    fields_oneoff["name"].config(width=22)

    def copy_selected_to_oneoff():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("No selection","Select a product first."); return
        entry = catalog["skus"][sel[0]]
        fields_oneoff["name"].delete(0, tk.END);   fields_oneoff["name"].insert(0, entry.get('name',''))
        fields_oneoff["weight"].delete(0, tk.END); fields_oneoff["weight"].insert(0, str(entry.get('weight_kg','')))
        fields_oneoff["value"].delete(0, tk.END);  fields_oneoff["value"].insert(0, str(entry.get('value_eur','')))

    tk.Button(of, text="✎ Copy selected here to edit", command=copy_selected_to_oneoff,
              bg='#95a5a6',fg='white',font=('Arial',9),relief='flat',padx=8,pady=2)\
        .grid(row=1, column=0, columnspan=6, sticky='w', padx=8, pady=(4,0))

    # Items already added to this order
    itf = ttk.LabelFrame(root, text="  Items in this order  ", padding=8)
    itf.pack(fill=tk.BOTH, padx=10, pady=4)
    items_count_var = tk.StringVar()
    icols = ('SKU', 'Name', 'Qty', 'Weight', 'Value')
    items_tree = ttk.Treeview(itf, columns=icols, show='headings', height=4)
    items_tree.column('SKU',    width=70,  anchor='w', stretch=False)
    items_tree.column('Name',   width=220, anchor='w')
    items_tree.column('Qty',    width=45,  anchor='center', stretch=False)
    items_tree.column('Weight', width=65,  anchor='center', stretch=False)
    items_tree.column('Value',  width=65,  anchor='center', stretch=False)
    for c in icols: items_tree.heading(c, text=c)
    items_tree.pack(fill=tk.X)
    tk.Label(itf, textvariable=items_count_var, font=('Arial',9), fg='#555').pack(anchor='w', pady=(4,0))

    def refresh_items():
        items_tree.delete(*items_tree.get_children())
        for i, it in enumerate(items):
            items_tree.insert('', 'end', iid=str(i), values=(
                it.get('sku') or 'ONE-OFF', it.get('name','')[:40],
                it.get('qty','1'), it.get('weight_kg',''), it.get('value_eur',''),
            ))
        items_count_var.set(f"{len(items)} item(s) in this order")

    refresh_items()

    # Buttons
    bf = tk.Frame(root); bf.pack(fill=tk.X, padx=10, pady=4)

    def add_selected():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("No selection","Please select a product from the list.")
            return
        sku = sel[0]
        entry = catalog["skus"][sku]
        if etsy_title:
            link_title_to_sku(catalog, sku, etsy_title)
        comment = comment_var.get().strip()
        name = f"{entry.get('name','')} {comment}".strip() if comment else entry.get('name','')
        items.append({
            'sku': sku, 'name': name, 'qty': qty_var.get().strip() or '1',
            'weight_kg': entry.get('weight_kg',''), 'value_eur': entry.get('value_eur',''),
            'is_custom': False,
        })
        comment_var.set('')
        refresh_items()

    def create_new():
        name   = fields_new["name"].get().strip()
        weight = fields_new["weight"].get().strip()
        length = fields_new["length"].get().strip()
        width  = fields_new["width"].get().strip()
        height = fields_new["height"].get().strip()
        value  = fields_new["value"].get().strip()
        if not name:
            messagebox.showwarning("Missing","Please enter a product name."); return
        sku, entry = register_new_sku(catalog, name, etsy_title,
                                      weight, length, width, height, value)
        items.append({
            'sku': sku, 'name': name, 'qty': qty_var.get().strip() or '1',
            'weight_kg': weight, 'value_eur': value, 'is_custom': False,
        })
        refresh_items()
        for e in fields_new.values(): e.delete(0, tk.END)
        if etsy_title: fields_new["name"].insert(0, etsy_title[:50])

    def add_oneoff():
        name   = fields_oneoff["name"].get().strip()
        weight = fields_oneoff["weight"].get().strip()
        value  = fields_oneoff["value"].get().strip()
        if not name:
            messagebox.showwarning("Missing","Please enter a description."); return
        items.append({
            'sku': '', 'name': name, 'qty': qty_var.get().strip() or '1',
            'weight_kg': weight, 'value_eur': value, 'is_custom': True,
        })
        refresh_items()
        for e in fields_oneoff.values(): e.delete(0, tk.END)

    def remove_item():
        sel = items_tree.selection()
        if not sel:
            messagebox.showwarning("No selection","Select an item in the order list first.")
            return
        idx = int(sel[0])
        if 0 <= idx < len(items):
            items.pop(idx)
        refresh_items()

    def done():
        result[0] = list(items); root.destroy()

    def cancel():
        result[0] = None; root.destroy()

    tk.Button(bf, text="+ Add Selected",  command=add_selected,
              bg='#27ae60',fg='white',font=('Arial',9,'bold'),relief='flat',padx=8,pady=4).pack(side=tk.LEFT,padx=2)
    tk.Button(bf, text="+ Add New Product", command=create_new,
              bg='#2980b9',fg='white',font=('Arial',9,'bold'),relief='flat',padx=8,pady=4).pack(side=tk.LEFT,padx=2)
    tk.Button(bf, text="+ Add One-off",   command=add_oneoff,
              bg='#8e44ad',fg='white',font=('Arial',9,'bold'),relief='flat',padx=8,pady=4).pack(side=tk.LEFT,padx=2)
    tk.Button(bf, text="− Remove Item",   command=remove_item,
              bg='#c0392b',fg='white',font=('Arial',9,'bold'),relief='flat',padx=8,pady=4).pack(side=tk.LEFT,padx=2)

    bf2 = tk.Frame(root); bf2.pack(fill=tk.X, padx=10, pady=(0,8))
    tk.Button(bf2, text="✓ Done",  command=done,
              bg='#27ae60',fg='white',font=('Arial',10,'bold'),relief='flat',padx=12,pady=5).pack(side=tk.RIGHT,padx=4)
    tk.Button(bf2, text="Cancel",  command=cancel,
              bg='#95a5a6',fg='white',font=('Arial',10,'bold'),relief='flat',padx=12,pady=5).pack(side=tk.RIGHT,padx=4)

    # Auto-size the window to exactly fit its content — no clipped columns,
    # no leftover blank space — instead of a guessed fixed geometry.
    root.update_idletasks()
    w = root.winfo_reqwidth()
    h = root.winfo_reqheight()
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"{w}x{h}+{max(0,(sw-w)//2)}+{max(0,(sh-h)//2)}")

    root.grab_set()
    if isinstance(root, tk.Toplevel):
        root.wait_window()
    else:
        root.mainloop()
    return result[0]


# ═══════════════════════════════════════════════════════════════════════════════
# CUSTOMER LIST & PRODUCT CATALOG WINDOWS
# ═══════════════════════════════════════════════════════════════════════════════

class CustomerListWindow:
    def __init__(self, parent):
        self.win = tk.Toplevel(parent)
        self.win.title("Customers")
        self.win.geometry("940x600")
        self.win.attributes('-topmost', True)
        self._build()
        self._load()

    def _build(self):
        top = tk.Frame(self.win); top.pack(fill=tk.X, padx=10, pady=6)
        tk.Label(top, text="Search:", font=('Arial', 10)).pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        tk.Entry(top, textvariable=self.search_var, width=32,
                 font=('Arial', 10)).pack(side=tk.LEFT, padx=6)
        self.search_var.trace_add('write', lambda *_: self._load())
        tk.Button(top, text="Add", command=self._add,
                  bg='#27ae60', fg='white', font=('Arial', 10, 'bold'),
                  relief='flat', padx=12, pady=4, cursor='hand2').pack(side=tk.RIGHT, padx=4)
        tk.Button(top, text="Delete", command=self._delete,
                  bg='#c0392b', fg='white', font=('Arial', 10, 'bold'),
                  relief='flat', padx=12, pady=4, cursor='hand2').pack(side=tk.RIGHT, padx=4)
        tk.Button(top, text="Edit", command=self._edit,
                  bg='#2980b9', fg='white', font=('Arial', 10, 'bold'),
                  relief='flat', padx=12, pady=4, cursor='hand2').pack(side=tk.RIGHT, padx=4)

        tf = tk.Frame(self.win); tf.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)
        cols = ('Name', 'Email', 'Country', 'City', 'Orders', 'Spent')
        self.tree = ttk.Treeview(tf, columns=cols, show='headings')
        self.tree.column('Name',    width=200, anchor='w')
        self.tree.column('Email',   width=195, anchor='w')
        self.tree.column('Country', width=110, anchor='w',      stretch=False)
        self.tree.column('City',    width=130, anchor='w',      stretch=False)
        self.tree.column('Orders',  width=60,  anchor='center', stretch=False)
        self.tree.column('Spent',   width=82,  anchor='center', stretch=False)
        for c in cols: self.tree.heading(c, text=c)
        sb = ttk.Scrollbar(tf, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind('<Double-1>', lambda e: self._edit())

        self.count_lbl = tk.Label(self.win, text="", font=('Arial', 9), fg='#555')
        self.count_lbl.pack(anchor='w', padx=12, pady=(2, 6))

    def _load(self):
        self.tree.delete(*self.tree.get_children())
        db = load_customer_db()
        ft = self.search_var.get().strip().lower()
        rows = []
        for key, c in db.items():
            name    = c.get('full_name') or key
            email   = c.get('email', '')
            country = c.get('ship_country', '')
            city    = c.get('ship_city', '')
            orders  = c.get('total_orders', 0)
            spent   = c.get('total_spent', 0.0)
            if ft and ft not in name.lower() and ft not in email.lower() \
                   and ft not in country.lower() and ft not in city.lower():
                continue
            rows.append((key, name, email, country, city, orders, spent))
        rows.sort(key=lambda r: r[1].lower())
        for key, name, email, country, city, orders, spent in rows:
            self.tree.insert('', 'end', iid=key, values=(
                name, email, country, city, orders, f"€{spent:.2f}"))
        self.count_lbl.config(text=f"{len(rows)} customer(s)")

    def _edit(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Select a customer first.",
                                   parent=self.win); return
        key = sel[0]
        db  = load_customer_db()
        if key in db:
            CustomerEditDialog(self.win, key, db[key], on_save=self._load)

    def _add(self):
        blank = {f: '' for f, _ in CustomerEditDialog._FIELDS}
        CustomerEditDialog(self.win, None, blank, on_save=self._load)

    def _delete(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Select a customer first.",
                                   parent=self.win); return
        key = sel[0]
        db  = load_customer_db()
        if key not in db: return
        name = db[key].get('full_name', key)
        if messagebox.askyesno("Delete customer?",
                               f"Delete '{name}'?\nThis cannot be undone.",
                               parent=self.win):
            del db[key]
            save_customer_db(db)
            self._load()


class CustomerEditDialog:
    _FIELDS = [
        ('full_name',     'Full Name'),
        ('first_name',    'First Name'),
        ('last_name',     'Last Name'),
        ('email',         'Email'),
        ('phone',         'Phone'),
        ('street_1',      'Street'),
        ('street_number', 'Number'),
        ('street_2',      'Street 2'),
        ('ship_city',     'City'),
        ('ship_state',    'State'),
        ('ship_zipcode',  'ZIP'),
        ('ship_country',  'Country'),
    ]

    def __init__(self, parent, key, data, on_save=None):
        self.win     = tk.Toplevel(parent)
        self.key     = key        # None means new customer
        self.data    = dict(data)
        self.on_save = on_save
        title = "New Customer" if key is None else f"Edit — {data.get('full_name', key)}"
        self.win.title(title)
        self.win.geometry("680x660")
        self.win.attributes('-topmost', True)
        self._build()
        self.win.grab_set()

    def _build(self):
        af = ttk.LabelFrame(self.win, text="  Address & Contact  ", padding="8")
        af.pack(fill=tk.X, padx=12, pady=(10, 4))
        self.entries = {}
        for i, (field, label) in enumerate(self._FIELDS):
            r, col = divmod(i, 2)
            tk.Label(af, text=label + ':', width=14, anchor='w',
                     font=('Arial', 9)).grid(row=r, column=col*2,
                                             padx=(8, 2), pady=2, sticky='w')
            e = tk.Entry(af, width=28, font=('Arial', 9))
            e.insert(0, self.data.get(field, '') or '')
            e.grid(row=r, column=col*2+1, padx=(0, 12), pady=2, sticky='w')
            self.entries[field] = e

        orders = self.data.get('orders', [])
        total_spent = self.data.get('total_spent', 0.0)
        hf = ttk.LabelFrame(
            self.win,
            text=(f"  Order History  —  {len(orders)} order(s)"
                  f"  •  €{total_spent:.2f} total  "),
            padding="4")
        hf.pack(fill=tk.BOTH, expand=True, padx=12, pady=4)
        hi = tk.Frame(hf); hi.pack(fill=tk.BOTH, expand=True)
        cols = ('Date', 'Product', 'Price', 'Carrier', 'Tracking')
        ht = ttk.Treeview(hi, columns=cols, show='headings', height=4)
        ht.column('Date',     width=88,  anchor='w',      stretch=False)
        ht.column('Product',  width=240, anchor='w')
        ht.column('Price',    width=70,  anchor='center', stretch=False)
        ht.column('Carrier',  width=70,  anchor='center', stretch=False)
        ht.column('Tracking', width=120, anchor='w',      stretch=False)
        for c in cols: ht.heading(c, text=c)
        hsb = ttk.Scrollbar(hi, orient='vertical', command=ht.yview)
        ht.configure(yscrollcommand=hsb.set)
        hsb.pack(side=tk.RIGHT, fill=tk.Y)
        ht.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        for o in reversed(orders):
            prod  = (o.get('product_name') or o.get('sku') or '—')[:45]
            price = f"€{o.get('value_eur')}" if o.get('value_eur') else '—'
            ht.insert('', 'end', values=(
                o.get('date', ''), prod, price,
                o.get('carrier', 'ELTA'), o.get('tracking', '')))

        bf = tk.Frame(self.win); bf.pack(fill=tk.X, padx=12, pady=8)
        tk.Button(bf, text="Save", command=self._save,
                  bg='#27ae60', fg='white', font=('Arial', 10, 'bold'),
                  relief='flat', padx=14, pady=5).pack(side=tk.LEFT, padx=4)
        tk.Button(bf, text="Cancel", command=self.win.destroy,
                  bg='#95a5a6', fg='white', font=('Arial', 10, 'bold'),
                  relief='flat', padx=14, pady=5).pack(side=tk.LEFT, padx=4)

    def _save(self):
        db = load_customer_db()
        if self.key is None:
            # New customer — derive key from email or full name
            email = self.entries.get('email', tk.Entry()).get().strip().lower()
            name  = self.entries.get('full_name', tk.Entry()).get().strip().lower()
            new_key = email if email else name
            if not new_key:
                messagebox.showwarning("Missing data",
                    "Enter at least an Email or Full Name.", parent=self.win)
                return
            if new_key in db:
                messagebox.showwarning("Already exists",
                    f"A customer with key '{new_key}' already exists.", parent=self.win)
                return
            db[new_key] = {'orders': [], 'total_orders': 0, 'total_spent': 0.0}
            for field, _ in self._FIELDS:
                db[new_key][field] = self.entries[field].get().strip()
        else:
            if self.key not in db:
                self.win.destroy(); return
            for field, _ in self._FIELDS:
                db[self.key][field] = self.entries[field].get().strip()
        save_customer_db(db)
        if self.on_save: self.on_save()
        self.win.destroy()


class ProductCatalogWindow:
    def __init__(self, parent):
        self.win = tk.Toplevel(parent)
        self.win.title("Product Catalog")
        self.win.geometry("860x500")
        self.win.attributes('-topmost', True)
        self._build()
        self._load()

    def _build(self):
        top = tk.Frame(self.win); top.pack(fill=tk.X, padx=10, pady=6)
        tk.Label(top, text="Search:", font=('Arial', 10)).pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        tk.Entry(top, textvariable=self.search_var, width=28,
                 font=('Arial', 10)).pack(side=tk.LEFT, padx=6)
        self.search_var.trace_add('write', lambda *_: self._load())
        tk.Button(top, text="Add", command=self._add,
                  bg='#27ae60', fg='white', font=('Arial', 10, 'bold'),
                  relief='flat', padx=12, pady=4, cursor='hand2').pack(side=tk.RIGHT, padx=4)
        tk.Button(top, text="Delete", command=self._delete,
                  bg='#c0392b', fg='white', font=('Arial', 10, 'bold'),
                  relief='flat', padx=12, pady=4, cursor='hand2').pack(side=tk.RIGHT, padx=4)
        tk.Button(top, text="Edit", command=self._edit,
                  bg='#2980b9', fg='white', font=('Arial', 10, 'bold'),
                  relief='flat', padx=12, pady=4, cursor='hand2').pack(side=tk.RIGHT, padx=4)

        tf = tk.Frame(self.win); tf.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)
        cols = ('SKU', 'Name', 'Weight', 'Dims (LxWxH)', 'Value', 'Shipped', 'Last Shipped')
        self.tree = ttk.Treeview(tf, columns=cols, show='headings')
        self.tree.column('SKU',          width=70,  anchor='w',      stretch=False)
        self.tree.column('Name',         width=255, anchor='w')
        self.tree.column('Weight',       width=65,  anchor='center', stretch=False)
        self.tree.column('Dims (LxWxH)', width=110, anchor='center', stretch=False)
        self.tree.column('Value',        width=65,  anchor='center', stretch=False)
        self.tree.column('Shipped',      width=65,  anchor='center', stretch=False)
        self.tree.column('Last Shipped', width=95,  anchor='center', stretch=False)
        for c in cols: self.tree.heading(c, text=c)
        sb = ttk.Scrollbar(tf, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind('<Double-1>', lambda e: self._edit())

        self.count_lbl = tk.Label(self.win, text="", font=('Arial', 9), fg='#555')
        self.count_lbl.pack(anchor='w', padx=12, pady=(2, 6))

    def _load(self):
        self.tree.delete(*self.tree.get_children())
        catalog = load_catalog()
        ft    = self.search_var.get().strip().lower()
        count = 0
        for sku, e in sorted(catalog["skus"].items()):
            name = e.get('name', '')
            if ft and ft not in sku.lower() and ft not in name.lower():
                continue
            dims = f"{e.get('length_cm','')}×{e.get('width_cm','')}×{e.get('height_cm','')}"
            val  = f"€{e.get('value_eur')}" if e.get('value_eur') else '—'
            self.tree.insert('', 'end', iid=sku, values=(
                sku, name, e.get('weight_kg', ''), dims, val,
                e.get('times_shipped', 0),
                e.get('last_shipped', '—') or '—',
            ))
            count += 1
        self.count_lbl.config(text=f"{count} product(s)")

    def _edit(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Select a product first.",
                                   parent=self.win); return
        sku     = sel[0]
        catalog = load_catalog()
        if sku in catalog["skus"]:
            ProductEditDialog(self.win, sku, catalog["skus"][sku], on_save=self._load)

    def _add(self):
        blank = {field: '' for field, _, _ in ProductEditDialog._FIELDS}
        ProductEditDialog(self.win, None, blank, on_save=self._load)

    def _delete(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Select a product first.",
                                   parent=self.win); return
        sku     = sel[0]
        catalog = load_catalog()
        if sku not in catalog["skus"]: return
        name = catalog["skus"][sku].get('name', sku)
        if messagebox.askyesno("Delete product?",
                               f"Delete '{sku} — {name}'?\nThis cannot be undone.",
                               parent=self.win):
            for title in catalog["skus"][sku].get('etsy_titles', []):
                catalog["title_map"].pop(title.strip().lower(), None)
            del catalog["skus"][sku]
            save_catalog(catalog)
            self._load()


class ProductEditDialog:
    _FIELDS = [
        ('name',      'Name',        46),
        ('weight_kg', 'Weight (kg)', 12),
        ('length_cm', 'Length (cm)', 12),
        ('width_cm',  'Width (cm)',  12),
        ('height_cm', 'Height (cm)', 12),
        ('value_eur', 'Value (€)',   12),
    ]

    def __init__(self, parent, sku, data, on_save=None):
        self.win     = tk.Toplevel(parent)
        self.sku     = sku        # None means new product
        self.data    = dict(data)
        self.on_save = on_save
        title = "New Product" if sku is None else f"Edit Product — {sku}"
        self.win.title(title)
        self.win.geometry("500x430")
        self.win.attributes('-topmost', True)
        self._build()
        self.win.grab_set()

    def _build(self):
        ff = ttk.LabelFrame(self.win,
                            text=f"  New Product  " if self.sku is None else f"  {self.sku}  ",
                            padding="10")
        ff.pack(fill=tk.X, padx=14, pady=(12, 4))
        self.entries = {}
        for i, (field, label, width) in enumerate(self._FIELDS):
            tk.Label(ff, text=label + ':', width=14, anchor='w',
                     font=('Arial', 10)).grid(row=i, column=0, padx=6, pady=3, sticky='w')
            e = tk.Entry(ff, width=width, font=('Arial', 10))
            e.insert(0, self.data.get(field, '') or '')
            e.grid(row=i, column=1, padx=6, pady=3, sticky='w')
            self.entries[field] = e

        titles = self.data.get('etsy_titles', [])
        if titles:
            tf = ttk.LabelFrame(self.win, text="  Etsy Titles (linked)  ", padding="6")
            tf.pack(fill=tk.X, padx=14, pady=4)
            for t in titles[:6]:
                tk.Label(tf, text=f"• {t[:80]}", font=('Arial', 9), fg='#555',
                         anchor='w').pack(fill='x', padx=4)

        tk.Label(self.win,
                 text=(f"Shipped {self.data.get('times_shipped', 0)} time(s)  •  "
                       f"Last: {self.data.get('last_shipped', '—') or '—'}"),
                 font=('Arial', 9), fg='#888').pack(anchor='w', padx=14, pady=(4, 0))

        bf = tk.Frame(self.win); bf.pack(fill=tk.X, padx=14, pady=10)
        tk.Button(bf, text="Save", command=self._save,
                  bg='#27ae60', fg='white', font=('Arial', 10, 'bold'),
                  relief='flat', padx=14, pady=5).pack(side=tk.LEFT, padx=4)
        tk.Button(bf, text="Cancel", command=self.win.destroy,
                  bg='#95a5a6', fg='white', font=('Arial', 10, 'bold'),
                  relief='flat', padx=14, pady=5).pack(side=tk.LEFT, padx=4)

    def _save(self):
        catalog = load_catalog()
        if self.sku is None:
            # New product — auto-generate SKU
            sku = _next_sku(catalog)
            catalog["skus"][sku] = {
                "name": "", "etsy_titles": [], "weight_kg": "",
                "length_cm": "", "width_cm": "", "height_cm": "",
                "value_eur": "", "times_shipped": 0, "last_shipped": None,
            }
            for field, _, _ in self._FIELDS:
                catalog["skus"][sku][field] = self.entries[field].get().strip()
        else:
            if self.sku not in catalog["skus"]:
                self.win.destroy(); return
            entry = catalog["skus"][self.sku]
            for field, _, _ in self._FIELDS:
                entry[field] = self.entries[field].get().strip()
        save_catalog(catalog)
        if self.on_save: self.on_save()
        self.win.destroy()


# ═══════════════════════════════════════════════════════════════════════════════
# REVIEW & EDIT SCREEN  (EltaShippingApp — with SKU + carrier awareness)
# ═══════════════════════════════════════════════════════════════════════════════

class EltaShippingApp:
    def __init__(self, root, filepath, include_usa=True, mode='both',
                 records=None, historical=False, from_db=False, service_pref='parcel',
                 zonos=False):
        self.root            = root
        self.filepath        = filepath
        self.include_usa     = include_usa
        self.mode            = mode
        self.pre_loaded      = records
        self.historical      = historical
        self.from_db         = from_db   # skip returning-customer dialog when data came from DB
        self.service_pref    = service_pref
        self.zonos           = zonos
        self.catalog         = load_catalog()
        self.shipping_data   = []
        self.current_index   = 0

        self.root.title("ELTA_Damon2.9 — Review & Edit")
        self.root.geometry("1020x800")
        try:
            self.root.state('zoomed')   # maximize on Windows
        except Exception:
            pass

        # Menu bar
        menubar   = tk.Menu(self.root)
        self.root.config(menu=menubar)
        data_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Data", menu=data_menu)
        data_menu.add_command(label="Customer List",
                              command=lambda: CustomerListWindow(self.root))
        data_menu.add_command(label="Product List",
                              command=lambda: ProductCatalogWindow(self.root))

        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.data_frame = ttk.LabelFrame(main_frame, text="Order Data", padding="10")
        self.data_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.entries = {}

        self.address_fields = [
            "full_name","first_name","last_name",
            "street_1","street_number","street_2",
            "ship_city","ship_state","ship_zipcode","ship_country",
            "email","phone","buyer",
        ]
        self.shipping_fields = {
            "weight_kg":"0,49","length_cm":"21",
            "width_cm":"28","height_cm":"12","customs_qty":"2",
        }
        self.extra_fields = {
            "value_eur": "",
            "order_date": datetime.date.today().isoformat(),
        }

        row = 0
        for field in self.address_fields:
            ttk.Label(self.data_frame,
                      text=field.replace('_',' ').title()+":").grid(
                          row=row, column=0, sticky=tk.W, padx=5, pady=2)
            e = ttk.Entry(self.data_frame, width=50)
            e.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
            self.entries[field] = e; row += 1

        ttk.Separator(self.data_frame, orient='horizontal').grid(
            row=row, column=0, columnspan=3, sticky='ew', pady=6); row += 1

        # SKU row
        ttk.Label(self.data_frame, text="SKU / Product:",
                  font=('Arial',10,'bold')).grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        sku_frame = tk.Frame(self.data_frame); sku_frame.grid(row=row, column=1, sticky=tk.W); row+=1
        self.sku_label = tk.Label(sku_frame, text="— not assigned —",
                                  font=('Arial',10), fg='#c0392b', width=28, anchor='w')
        self.sku_label.pack(side=tk.LEFT, padx=(0,8))
        tk.Button(sku_frame, text="Assign / Change", command=self._assign_sku,
                  bg='#2980b9', fg='white', font=('Arial',9,'bold'),
                  relief='flat', padx=8, pady=2, cursor='hand2').pack(side=tk.LEFT)
        tk.Button(sku_frame, text="Edit Product", command=self._edit_product,
                  bg='#7f8c8d', fg='white', font=('Arial',9,'bold'),
                  relief='flat', padx=8, pady=2, cursor='hand2').pack(side=tk.LEFT, padx=(6,0))
        self._current_sku   = ""
        self._current_entry = None

        ttk.Separator(self.data_frame, orient='horizontal').grid(
            row=row, column=0, columnspan=3, sticky='ew', pady=6); row += 1

        for field, default in {**self.shipping_fields, **self.extra_fields}.items():
            ttk.Label(self.data_frame,
                      text=field.replace('_',' ').title()+":").grid(
                          row=row, column=0, sticky=tk.W, padx=5, pady=2)
            e = ttk.Entry(self.data_frame, width=20)
            e.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
            e.insert(0, default)
            self.entries[field] = e; row += 1

        # ELTA effective-country label (shows when country differs from ship_country)
        ttk.Label(self.data_frame, text="ELTA country:").grid(
            row=row, column=0, sticky=tk.W, padx=5, pady=2)
        self.elta_country_var = tk.StringVar(value="")
        self.elta_country_lbl = tk.Label(self.data_frame, textvariable=self.elta_country_var,
                                         font=('Arial', 10, 'bold'), fg='#e67e22', anchor='w')
        self.elta_country_lbl.grid(row=row, column=1, sticky=tk.W, padx=5); row += 1

        self.print_label_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.data_frame, text="Include in CSV export?",
                        variable=self.print_label_var).grid(
                            row=row, column=0, columnspan=2, sticky=tk.W, padx=5, pady=8)

        # ── Order History panel ──
        self.history_frame = ttk.LabelFrame(main_frame, text="  Order History  ", padding="4")
        self.history_frame.pack(fill=tk.X, padx=10, pady=(0, 4))
        _hist_inner = tk.Frame(self.history_frame)
        _hist_inner.pack(fill=tk.X)
        hist_cols = ('Date', 'Product', 'Price', 'Carrier', 'Tracking')
        self.hist_tree = ttk.Treeview(_hist_inner, columns=hist_cols,
                                       show='headings', height=3)
        self.hist_tree.column('Date',     width=88,  anchor='w',      stretch=False)
        self.hist_tree.column('Product',  width=280, anchor='w')
        self.hist_tree.column('Price',    width=72,  anchor='center', stretch=False)
        self.hist_tree.column('Carrier',  width=72,  anchor='center', stretch=False)
        self.hist_tree.column('Tracking', width=120, anchor='w',      stretch=False)
        for _c in hist_cols: self.hist_tree.heading(_c, text=_c)
        _hist_sb = ttk.Scrollbar(_hist_inner, orient='vertical',
                                 command=self.hist_tree.yview)
        self.hist_tree.configure(yscrollcommand=_hist_sb.set)
        _hist_sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.hist_tree.pack(side=tk.LEFT, fill=tk.X, expand=True)

        nav_frame = ttk.Frame(main_frame); nav_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(nav_frame, text="◀ Previous", command=self.prev_record).pack(side=tk.LEFT,padx=5)
        ttk.Button(nav_frame, text="Next ▶",     command=self.next_record).pack(side=tk.LEFT,padx=5)
        self.status_var = tk.StringVar()
        ttk.Label(nav_frame, textvariable=self.status_var).pack(side=tk.LEFT, padx=20)

        action_frame = ttk.Frame(main_frame); action_frame.pack(fill=tk.X, padx=10, pady=10)
        btn_lbl = "Save to DB (no labels)" if historical else "▶ Start Processing"
        btn_bg  = '#7f8c8d' if historical else '#27ae60'
        tk.Button(action_frame, text=btn_lbl, command=self.start_processing,
                  bg=btn_bg, fg='white', font=('Arial',11,'bold'),
                  relief='flat', padx=14, pady=7, cursor='hand2').pack(side=tk.RIGHT, padx=5)
        ttk.Button(action_frame, text="Save Changes",
                   command=self.save_changes).pack(side=tk.RIGHT, padx=5)

        # load_orders called via root.after(50)

    def _assign_sku(self):
        try:
            if not self.root.winfo_exists():
                return
        except Exception:
            return
        self.save_changes()
        rec        = self.shipping_data[self.current_index] if self.shipping_data else {}
        etsy_title = rec.get('etsy_title', '')
        # Backward compat: build a one-item starting list from legacy sku/product_name
        # fields if this record predates the multi-item 'items' list.
        current_items = rec.get('items')
        if current_items is None and rec.get('product_name'):
            current_items = [{
                'sku': rec.get('sku',''), 'name': rec.get('product_name',''),
                'qty': rec.get('customs_qty','1'),
                'weight_kg': rec.get('weight_kg',''), 'value_eur': rec.get('value_eur',''),
                'is_custom': not rec.get('sku',''),
            }]
        items = ask_items(self.catalog, etsy_title, current_items, parent=self.root)
        if items is None:
            return  # cancelled — leave record unchanged

        if not self.shipping_data:
            return
        rec['items'] = items
        if items:
            rec['product_name'] = " + ".join(it.get('name','') for it in items)
            rec['sku']          = items[0].get('sku','')           # primary, for legacy lookups/history
            rec['customs_qty']  = str(sum(int(_parse_num(it.get('qty','1'), 1)) for it in items))
            self._current_sku   = rec['sku']
            self._current_entry = self.catalog["skus"].get(rec['sku']) if rec['sku'] else None
            label = ", ".join(f"{(it.get('sku') or 'one-off')}: {it.get('name','')}" for it in items)
            try:
                self.sku_label.config(text=label[:70], fg='#27ae60')
                # Auto-fill package weight/value as the sum across items (dims left as-is —
                # box dimensions aren't a per-item property)
                total_weight = sum(_parse_num(it.get('weight_kg','')) for it in items)
                total_value  = sum(_parse_num(it.get('value_eur',''))  for it in items)
                if total_weight and 'weight_kg' in self.entries:
                    self.entries['weight_kg'].delete(0, tk.END)
                    self.entries['weight_kg'].insert(0, str(round(total_weight, 2)))
                if total_value and 'value_eur' in self.entries:
                    self.entries['value_eur'].delete(0, tk.END)
                    self.entries['value_eur'].insert(0, str(round(total_value, 2)))
            except Exception:
                pass
        else:
            rec['product_name'] = ''
            rec['sku']          = ''
            self._current_sku   = ''
            self._current_entry = None
            try:
                self.sku_label.config(text="— not assigned —", fg='#c0392b')
            except Exception:
                pass

    def _edit_product(self):
        if not self._current_sku:
            messagebox.showwarning("No Product", "Assign a product first, then edit it.")
            return
        entry = self.catalog["skus"].get(self._current_sku, {})
        def on_saved():
            self.catalog = load_catalog()
            updated = self.catalog["skus"].get(self._current_sku, {})
            self._current_entry = updated
            self.sku_label.config(
                text=f"{self._current_sku}  —  {updated.get('name','')}", fg='#27ae60')
            for k in ('weight_kg', 'length_cm', 'width_cm', 'height_cm', 'value_eur'):
                v = updated.get(k, '')
                if v and k in self.entries:
                    self.entries[k].delete(0, tk.END)
                    self.entries[k].insert(0, str(v))
        ProductEditDialog(self.root, self._current_sku, entry, on_save=on_saved)

    def _update_history_panel(self, record):
        self.hist_tree.delete(*self.hist_tree.get_children())
        db  = load_customer_db()
        key = customer_db_key(record)
        if not key or key not in db or not db[key].get('orders'):
            self.hist_tree.insert('', 'end', values=('—', 'No previous orders', '—', '—', ''))
            return
        orders = db[key].get('orders', [])
        total  = db[key].get('total_orders', len(orders))
        spent  = db[key].get('total_spent', 0.0)
        self.history_frame.config(
            text=f"  Order History  —  {total} order(s)  •  €{spent:.2f} total  ")
        for o in reversed(orders):
            prod  = (o.get('product_name') or o.get('sku') or '—')[:50]
            price = f"€{o.get('value_eur')}" if o.get('value_eur') else '—'
            self.hist_tree.insert('', 'end', values=(
                o.get('date', ''), prod, price,
                o.get('carrier', 'ELTA'), o.get('tracking', ''),
            ))

    def load_orders(self):
        try:
            if self.pre_loaded is not None:
                self.shipping_data = self.pre_loaded
            else:
                self.shipping_data = load_orders_from_html(self.filepath)
                if not self.include_usa:
                    self.shipping_data = [r for r in self.shipping_data
                                          if r.get('ship_country','') not in USA_COUNTRY_VALUES]

            for r in self.shipping_data:
                for k, v in self.shipping_fields.items():
                    r.setdefault(k, v)
                r.setdefault('value_eur', '')
                r.setdefault('order_date', datetime.date.today().isoformat())

            # Auto-resolve SKUs for all records (exact → fuzzy dialog → auto-create)
            for r in self.shipping_data:
                if not r.get('sku') and r.get('etsy_title'):
                    sku, entry = auto_resolve_sku(self.catalog, r['etsy_title'], parent=self.root)
                    if sku and entry:
                        r['sku']          = sku
                        r['product_name'] = entry.get('name', '')
                        for k in ('weight_kg','length_cm','width_cm','height_cm','value_eur'):
                            if entry.get(k):
                                r[k] = entry[k]

            # Returning customer check with full address comparison dialog
            # Skip when data came from DB (from_db mode) — we already have the stored data
            if not self.from_db:
                db = load_customer_db()
                for record in self.shipping_data:
                    key = customer_db_key(record)
                    if key and key in db:
                        stored = db[key]
                        action, save_to_db = show_customer_update_dialog(record, stored, parent=self.root)
                        if action == 'keep':
                            for field in ('street_1','street_number','street_2',
                                          'ship_city','ship_state','ship_zipcode','ship_country',
                                          'phone'):
                                if stored.get(field):
                                    record[field] = stored[field]
                        elif save_to_db:
                            for field in ('street_1','street_number','street_2','ship_city',
                                          'ship_state','ship_zipcode','ship_country','phone'):
                                if record.get(field):
                                    db[key][field] = record[field]
                            save_customer_db(db)

            if self.shipping_data:
                self.display_record(0)
                self.status_var.set(f"Record 1 of {len(self.shipping_data)}")
            else:
                messagebox.showwarning("No Orders", "No orders found.")

        except Exception as e:
            messagebox.showerror("Error Loading Orders", str(e))

    def display_record(self, index):
        if not (0 <= index < len(self.shipping_data)):
            return
        rec = self.shipping_data[index]
        for field in self.entries:
            self.entries[field].delete(0, tk.END)
            v = rec.get(field, '')
            if v: self.entries[field].insert(0, str(v))
        self.print_label_var.set(rec.get("print_label", True))
        self._update_history_panel(rec)
        sku   = rec.get('sku', '')
        pname = rec.get('product_name', '')
        items = rec.get('items') or []
        self._current_sku   = sku
        self._current_entry = self.catalog["skus"].get(sku) if sku else None
        if len(items) > 1:
            label = ", ".join(f"{(it.get('sku') or 'one-off')}: {it.get('name','')}" for it in items)
            self.sku_label.config(text=label[:70], fg='#27ae60')
        elif sku or pname:
            self.sku_label.config(text=f"{sku or 'one-off'}  —  {pname}", fg='#27ae60')
        else:
            self.sku_label.config(text="— not assigned —", fg='#c0392b')
        # ELTA effective country — show in orange when it differs from ship_country
        ec = elta_country(rec)
        ship = rec.get('ship_country', '')
        if ec and ec != ship:
            self.elta_country_var.set(f"⚠  {ec}  (customs required)")
            self.elta_country_lbl.config(fg='#e67e22')
        else:
            self.elta_country_var.set(ec or "")
            self.elta_country_lbl.config(fg='#555')
        self.current_index = index

    def save_changes(self):
        if not (0 <= self.current_index < len(self.shipping_data)):
            return
        rec = self.shipping_data[self.current_index]
        for field in self.entries:
            rec[field] = self.entries[field].get()
        rec["print_label"]   = self.print_label_var.get()
        rec["sku"]           = self._current_sku
        is_multi = len(rec.get('items') or []) > 1
        if not is_multi:
            rec["product_name"] = (self._current_entry or {}).get('name', '')
        # else: product_name was already set to the combined description in
        # _assign_sku — the per-order package weight/value entries below are a
        # SUM across items, so they must never be written back to a single
        # SKU's shared catalog entry (would corrupt it for future orders).
        if self._current_sku and not is_multi:
            entry = self.catalog["skus"].get(self._current_sku)
            if entry:
                changed = False
                for field, cat_key in [('weight_kg','weight_kg'),('length_cm','length_cm'),
                                        ('width_cm','width_cm'),('height_cm','height_cm'),
                                        ('value_eur','value_eur')]:
                    val = (rec.get(field) or '').strip()
                    if val and val != str(entry.get(cat_key, '')):
                        entry[cat_key] = val
                        changed = True
                if changed:
                    save_catalog(self.catalog)
                    print(f"✓ Catalog updated for {self._current_sku}")
        # Pre-save customer address so it survives a Firefox crash
        save_customer_address(rec)

    def next_record(self):
        if self.current_index < len(self.shipping_data) - 1:
            self.save_changes()
            next_idx = self.current_index + 1
            self.display_record(next_idx)
            self.status_var.set(f"Record {self.current_index+1} of {len(self.shipping_data)}")

    def prev_record(self):
        if self.current_index > 0:
            self.save_changes()
            prev_idx = self.current_index - 1
            self.display_record(prev_idx)
            self.status_var.set(f"Record {self.current_index+1} of {len(self.shipping_data)}")

    def start_processing(self):
        self.save_changes()
        to_process = [r for r in self.shipping_data if r.get("print_label", True)]
        if not to_process:
            messagebox.showwarning("Nothing to do", "No records selected.")
            return

        if self.historical:
            # Historical mode: save to DB only
            for r in to_process:
                upsert_customer(r, sku=r.get('sku',''),
                                carrier='ELTA',
                                order_date=r.get('order_date',''),
                                historical=True)
                bump_items_shipped(self.catalog, r)
            messagebox.showinfo("Done",
                f"✓ {len(to_process)} records saved to customer DB.\nNo labels generated.")
            self.root.destroy()
            return

        self.root.destroy()
        process_live(to_process, self.mode, self.catalog, self.service_pref, self.zonos)


# ═══════════════════════════════════════════════════════════════════════════════
# LIVE PROCESSING DISPATCHER
# ═══════════════════════════════════════════════════════════════════════════════

def process_live(elta_records, mode, catalog, service_pref='parcel', zonos=False):
    if zonos and elta_records:
        process_zonos_batch(elta_records, catalog)

    if mode == 'letters':
        for r in (elta_records or []):
            try:
                _db_pre = load_customer_db()
                _key    = customer_db_key(r)
                is_ret  = (_key and _key in _db_pre and
                           _db_pre[_key].get("total_orders", 0) > 0)
                generate_thank_you(r)
                if is_ret:
                    generate_thank_you_return(r)
                upsert_customer(r, sku=r.get('sku',''), carrier='ELTA')
                if catalog:
                    bump_items_shipped(catalog, r)
            except Exception as e:
                print(f"⚠ Letter error: {e}")
        return

    if mode == 'none':
        return  # Zonos-only run — no CSV/labels, no letters

    if elta_records:
        process_csv_export(elta_records, mode, catalog, service_pref)


# ═══════════════════════════════════════════════════════════════════════════════
# THANK-YOU LETTERS
# ═══════════════════════════════════════════════════════════════════════════════

def guess_gender(first_name, country=None):
    try:
        params = {"name": first_name.split()[0]}
        iso = COUNTRY_ISO.get(country,'')
        if iso: params["country_id"] = iso
        resp = requests.get("https://api.genderize.io", params=params, timeout=5, verify=False)
        data = resp.json()
        gender = data.get("gender"); prob = data.get("probability",0)
        if gender and prob >= GENDER_CONFIDENCE_THRESHOLD:
            return 'M' if gender=='male' else 'F'
    except Exception as e:
        print(f"⚠ genderize.io: {e}")
    return None

def ask_gender(full_name):
    result=['M']
    root=tk.Tk(); root.title("Gender?"); root.attributes('-topmost',True)
    root.resizable(False,False)
    tk.Label(root,text=f"Cannot determine gender for:\n{full_name}\n\nSelect salutation:",
             wraplength=320,justify='center',pady=12,padx=16,font=('Arial',11)).pack()
    bf=tk.Frame(root); bf.pack(pady=(4,14))
    tk.Button(bf,text="Mr.",command=lambda:(result.__setitem__(0,'M'),root.destroy()),
              bg='#2980b9',fg='white',font=('Arial',11,'bold'),relief='flat',
              padx=20,pady=6,cursor='hand2').pack(side=tk.LEFT,padx=8)
    tk.Button(bf,text="Ms.",command=lambda:(result.__setitem__(0,'F'),root.destroy()),
              bg='#8e44ad',fg='white',font=('Arial',11,'bold'),relief='flat',
              padx=20,pady=6,cursor='hand2').pack(side=tk.LEFT,padx=8)
    root.update_idletasks()
    sw,sh=root.winfo_screenwidth(),root.winfo_screenheight()
    w,h=root.winfo_reqwidth(),root.winfo_reqheight()
    root.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")
    root.grab_set(); root.mainloop()
    return result[0]

FRENCH_COUNTRIES = {
    "France", "Belgium", "Switzerland", "Luxembourg", "Monaco",
}

def generate_thank_you(record):
    first_name = record.get('first_name', '')
    last_name  = record.get('last_name', '')
    country    = record.get('ship_country', '')
    gender = guess_gender(first_name, country)
    if gender is None:
        gender = ask_gender(f"{first_name} {last_name}")

    if country in FRENCH_COUNTRIES:
        if gender == 'M':
            salutation = f"Cher M. {last_name},"
        else:
            salutation = f"Chère Mme {last_name},"
        body_paras = [
            "Bienvenue dans notre atelier ! Nous sommes sincèrement ravis que vous nous ayez choisis pour votre achat, et c'est un véritable honneur de contribuer à donner vie à votre vision créative.",
            "Chaque perruque qui quitte notre atelier est le fruit d'années de savoir-faire, de soin et de dévouement. Nous espérons que votre nouvelle pièce apportera exactement la touche qu'il faut à votre représentation, production ou événement — et que la porter sera aussi spécial que l'occasion pour laquelle elle a été créée.",
            "Si vous avez des questions, souhaitez partager votre expérience ou avez besoin d'ajustements, n'hésitez pas à nous contacter. Vos retours ne sont pas seulement les bienvenus — ils sont véritablement précieux et nous aident à continuer à progresser.",
            "Merci encore de nous avoir fait confiance. Ce sont des clients comme vous qui donnent tout son sens à notre travail, et nous espérons sincèrement avoir l'occasion de créer quelque chose ensemble à nouveau dans le futur.",
        ]
        closing  = "Avec nos chaleureuses salutations,"
        gap_lines = 2

    elif country in SPANISH_COUNTRIES:
        if gender == 'M':
            salutation  = f"Estimado señor {last_name},"
            bienvenidox = "¡Bienvenido a nuestro atelier! Estamos verdaderamente encantados de que nos haya elegido para su compra, y es un auténtico honor contribuir a dar vida a su visión creativa."
        else:
            salutation  = f"Estimada señora {last_name},"
            bienvenidox = "¡Bienvenida a nuestro atelier! Estamos verdaderamente encantados de que nos haya elegido para su compra, y es un auténtico honor contribuir a dar vida a su visión creativa."
        body_paras = [
            bienvenidox,
            "Cada peluca que sale de nuestro taller es el resultado de años de oficio, cuidado y dedicación. Esperamos que su nueva pieza aporte exactamente el toque adecuado a su actuación, producción o evento — y que llevarla sea tan especial como la ocasión para la que fue creada.",
            "Si tiene alguna pregunta, desea compartir su experiencia o necesita algún ajuste, no dude en ponerse en contacto con nosotros. Sus comentarios no solo son bienvenidos — son genuinamente valiosos y nos ayudan a seguir creciendo y mejorando.",
            "Gracias de nuevo por confiar en nosotros. Son clientes como usted quienes dan sentido a este trabajo, y esperamos con ilusión la posibilidad de crear algo juntos de nuevo en el futuro.",
        ]
        closing   = "Con un cordial saludo,"
        gap_lines = 1

    else:
        if gender == 'M':
            salutation = f"Dear Mr. {last_name},"
        else:
            salutation = f"Dear Ms. {last_name},"
        body_paras = [
            "Welcome to our atelier! We are truly delighted that you have chosen us for your purchase, and it is a genuine honor to play a part in bringing your creative vision to life.",
            "Every wig that leaves our workshop is the result of years of craft, care, and dedication. We hope your new piece adds exactly the right touch to your performance, production, or event — and that wearing it feels as special as the occasion it was made for.",
            "Should you have any questions, wish to share your experience, or need any adjustments, please do not hesitate to reach out. Your feedback is not just welcome — it is genuinely valued and helps us continue to grow and improve.",
            "Thank you once again for trusting us with your needs. It is customers like you who make this work meaningful, and we very much look forward to the possibility of creating something together again in the future.",
        ]
        closing   = "With warm regards,"
        gap_lines = 2

    # Build ODT
    doc = OpenDocumentText()

    style_body = Style(name="LBody", family="paragraph")
    style_body.addElement(ParagraphProperties(textalign="justify"))
    style_body.addElement(TextProperties(
        fontname="Linux Libertine Display G",
        fontsize="14pt",
        fontsizeasian="14pt",
        fontsizecomplex="14pt",
    ))
    doc.styles.addElement(style_body)

    style_blank = Style(name="LBlank", family="paragraph")
    style_blank.addElement(ParagraphProperties(textalign="justify"))
    style_blank.addElement(TextProperties(
        fontname="Linux Libertine Display G",
        fontsize="14pt",
        fontsizeasian="14pt",
        fontsizecomplex="14pt",
    ))
    doc.styles.addElement(style_blank)

    def add_para(text, style="LBody"):
        p = P(stylename=style)
        p.addText(text)
        doc.text.addElement(p)

    def add_blank():
        add_para("", "LBlank")

    add_para(salutation)
    add_blank()
    for i, para in enumerate(body_paras):
        add_para(para)
        if i < len(body_paras) - 1:
            add_blank()
    for _ in range(gap_lines):
        add_blank()
    add_para(closing)
    add_blank()
    add_para("Constantine")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    date_str = datetime.date.today().strftime("%d_%m_%y")
    filename = f"{last_name.upper()}_{first_name.upper()}_{date_str}_thankyou.odt"
    doc.save(os.path.join(OUTPUT_DIR, filename))
    print(f"✓ Thank-you letter: {filename}")


def generate_thank_you_return(record):
    """Generate a 'welcome back' letter for returning customers."""
    first_name = record.get('first_name', '')
    last_name  = record.get('last_name', '')
    country    = record.get('ship_country', '')
    gender = guess_gender(first_name, country)
    if gender is None:
        gender = ask_gender(f"{first_name} {last_name}")

    if country in FRENCH_COUNTRIES:
        salutation = (f"Cher M. {last_name}," if gender == 'M'
                      else f"Chère Mme {last_name},")
        body_paras = [
            "Nous sommes profondément touchés de vous retrouver parmi nous. Les clients qui reviennent sont la raison d'être de cet atelier, et savoir que notre travail a une nouvelle fois mérité votre confiance est pour nous une source de fierté sincère.",
            "Nous espérons que cette nouvelle pièce vous apportera la même satisfaction qu'auparavant — et qu'elle ajoutera exactement la touche qu'il faut à l'occasion que vous avez en tête.",
            "Comme toujours, si vous souhaitez des ajustements ou souhaitez simplement nous faire part de votre expérience, n'hésitez pas à nous contacter. Vous êtes toujours le bienvenu ici." if gender == 'M' else
            "Comme toujours, si vous souhaitez des ajustements ou souhaitez simplement nous faire part de votre expérience, n'hésitez pas à nous contacter. Vous êtes toujours la bienvenue ici.",
        ]
        closing   = "Avec nos chaleureuses salutations,"
        gap_lines = 2

    elif country in SPANISH_COUNTRIES:
        salutation = (f"Estimado señor {last_name}," if gender == 'M'
                      else f"Estimada señora {last_name},")
        volver = ("Nos alegra enormemente volver a verle."
                  if gender == 'M' else "Nos alegra enormemente volver a verla.")
        body_paras = [
            volver + " Los clientes que regresan son la razón de ser de este taller, y saber que nuestro trabajo ha merecido de nuevo su confianza nos llena de verdadero orgullo.",
            "Esperamos que esta nueva pieza le brinde la misma satisfacción que antes — y que llevarla añada exactamente el toque adecuado a la ocasión que tiene en mente.",
            "Como siempre, si necesita algún ajuste o simplemente desea contarnos cómo fue, no dude en ponerse en contacto con nosotros. Siempre es bienvenido aquí." if gender == 'M' else
            "Como siempre, si necesita algún ajuste o simplemente desea contarnos cómo fue, no dude en ponerse en contacto con nosotros. Siempre es bienvenida aquí.",
        ]
        closing   = "Con un cordial saludo,"
        gap_lines = 1

    else:
        salutation = (f"Dear Mr. {last_name}," if gender == 'M'
                      else f"Dear Ms. {last_name},")
        body_paras = [
            "It means a great deal to us to see you return. Customers who come back are the reason this workshop exists, and knowing that our work has earned your trust again fills us with genuine pride.",
            "We hope this new piece brings you the same satisfaction as before — and that wearing it adds exactly the right touch to whatever occasion you have in mind.",
            "As always, if you need any adjustments or simply wish to share how it went, please do not hesitate to reach out. You are always welcome here.",
        ]
        closing   = "With warm regards,"
        gap_lines = 2

    doc = OpenDocumentText()

    style_body = Style(name="LBody", family="paragraph")
    style_body.addElement(ParagraphProperties(textalign="justify"))
    style_body.addElement(TextProperties(
        fontname="Linux Libertine Display G", fontsize="14pt",
        fontsizeasian="14pt", fontsizecomplex="14pt",
    ))
    doc.styles.addElement(style_body)

    style_blank = Style(name="LBlank", family="paragraph")
    style_blank.addElement(ParagraphProperties(textalign="justify"))
    style_blank.addElement(TextProperties(
        fontname="Linux Libertine Display G", fontsize="14pt",
        fontsizeasian="14pt", fontsizecomplex="14pt",
    ))
    doc.styles.addElement(style_blank)

    def add_para(text, style="LBody"):
        p = P(stylename=style); p.addText(text); doc.text.addElement(p)

    def add_blank():
        add_para("", "LBlank")

    add_para(salutation); add_blank()
    for i, para in enumerate(body_paras):
        add_para(para)
        if i < len(body_paras) - 1:
            add_blank()
    for _ in range(gap_lines): add_blank()
    add_para(closing); add_blank()
    add_para("Constantine")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    date_str = datetime.date.today().strftime("%d_%m_%y")
    filename = f"{last_name.upper()}_{first_name.upper()}_{date_str}_thankyou_return.odt"
    doc.save(os.path.join(OUTPUT_DIR, filename))
    print(f"✓ Return thank-you letter: {filename}")


# ═══════════════════════════════════════════════════════════════════════════════
# ELTA SELENIUM AUTOMATION  (unchanged from v4.3)
# ═══════════════════════════════════════════════════════════════════════════════

RECEIPTS_DIR = "D:\\Downloads"
CUSTOMS_TARIFF_CODE = "6704110000"  # wigs of synthetic textile materials — matches
                                     # Zonos' 6704.11.0000 (dotted form there, plain
                                     # digits here). Confirmed as the correct heading
                                     # 2026-08-10; keep this identical across ELTA and
                                     # Zonos so both systems always declare the same code.
                                     # Fixed 2026-08-20: this was "67041100" (8 digits,
                                     # 2 zeros short of the real 10-digit HTS code) —
                                     # the comment above already said it should match
                                     # "6704.11.0000" but the plain-digit form never
                                     # actually did. Confirmed live: Zonos rejected/
                                     # errored on the truncated code (Donald MacDonald
                                     # order).
CUSTOMS_LINE_NET_WEIGHT_KG = "0,2"  # fallback per-item customs weight, used only if
                                     # no Zonos confirmation PDF weight was found for
                                     # that line; the box's real gross weight is
                                     # entered separately by hand.
CUSTOMS_DESCRIPTION_MAX_LEN = 24    # ELTA's live validator rejected a 25-char customs
                                     # description with "exceeds the maximum length of
                                     # '24'" (2026-08-18 real upload) — Instructions.xls
                                     # documents this field as 50 chars, but the actual
                                     # bulk-import validator enforces 24. Trust the live
                                     # limit over the doc.

_GREEK_RE = re.compile(r'[\u0370-\u03FF\u1F00-\u1FFF]')

def _english_only(text):
    """Keep only Latin-script words from a mixed Greek/English description cell."""
    if not text: return ""
    tokens = re.split(r'\s+', text.replace('\n', ' ').strip())
    kept = [t for t in tokens if t and not _GREEK_RE.search(t)]
    return ' '.join(kept).strip()

def _fmt_num(raw):
    n = _parse_num(raw, 0.0)
    return str(int(n)) if n == int(n) else str(round(n, 2)).replace('.', ',')

def _fmt_weight_kg(kg_value):
    """Format a kg weight for ELTA's net-weight field (comma decimal, no
    trailing zeros). Keeps gram-level precision since Zonos weights are
    entered in grams and can be small."""
    n = round(_parse_num(kg_value, 0.0), 4)
    if n < 0.01:
        print(f"⚠ Zonos net weight looks unusually low ({n*1000:g} g) — "
              f"double-check the unit-weight entry before submitting.")
    s = f"{n:.4f}".rstrip('0').rstrip('.')
    return (s or '0').replace('.', ',')

# ELTA's content-description / customs-description fields are length-limited —
# abbreviate word-by-word instead of sending the full description text. Add
# new (WORD → short form) pairs here as new product types come up; unmapped
# words are kept as-is (uppercased).
_WORD_ABBREVIATIONS = {
    "SYNTHETIC": "SYNTH",
    "FIBER":     "FIBR",
    "FIBRE":     "FIBR",
    "COSTUME":   "COSTME",
    "WIG":       "WIG",
    "BEARD":     "BEARD",
    "QUEUE":     "QUEUE",
    "MUSTACHE":  "MUSTCH",
    "MOUSTACHE": "MUSTCH",
}

def _short_customs_description(desc):
    words = re.findall(r"[A-Za-z']+", desc or '')
    return ' '.join(_WORD_ABBREVIATIONS.get(w.upper(), w.upper()) for w in words)

def find_receipt_candidates(last_name):
    """Search D:\\Downloads for MyData receipt PDFs matching this customer's surname.
    Files with "zonos" in the name are Zonos prep docs (also named with the
    customer's surname) and are never the MyData receipt — always excluded."""
    if not last_name or not os.path.isdir(RECEIPTS_DIR):
        return []
    surname_compact = strip_accents(last_name).upper().replace(' ', '')
    if not surname_compact:
        return []
    matches = []
    for fname in os.listdir(RECEIPTS_DIR):
        if not fname.lower().endswith('.pdf'):
            continue
        if 'zonos' in fname.lower():
            continue
        upper_compact = strip_accents(fname).upper().replace(' ', '')
        if surname_compact in upper_compact:
            matches.append(os.path.join(RECEIPTS_DIR, fname))
    return matches

def find_zonos_candidates(last_name):
    """Search D:\\Downloads for the Zonos Prepay confirmation PDF matching this
    customer's surname (e.g. "CLARKE - Zonos.pdf", "POU-Zonos.pdf") — the
    barcode/declaration page that has the per-item weight and description.
    Filenames containing "invoice" are the separate Zonos tax invoice, which
    never has that breakdown, and are always excluded."""
    if not last_name or not os.path.isdir(RECEIPTS_DIR):
        return []
    surname_compact = strip_accents(last_name).upper().replace(' ', '')
    if not surname_compact:
        return []
    matches = []
    for fname in os.listdir(RECEIPTS_DIR):
        if not fname.lower().endswith('.pdf'):
            continue
        lower = fname.lower()
        if 'zonos' not in lower or 'invoice' in lower:
            continue
        upper_compact = strip_accents(fname).upper().replace(' ', '')
        if surname_compact in upper_compact:
            matches.append(os.path.join(RECEIPTS_DIR, fname))
    return matches

# Product-code → clean English description, built up from real receipts as
# new codes are seen (the MyData/eskap 'Κωδικός' column, e.g. "AG-7467383" —
# not this project's own WIG-NNN catalog SKUs). Needed because a receipt's
# 'Περιγραφή' (description) cell can't be reliably split back into per-item
# text: when ELTA's PDF wraps a description onto an extra line, pdfplumber's
# linear text-extraction order pushes that continuation word to a different
# position in the stream than the item's own numbers (caught 2026-08-18 on a
# real order — "MOUSTACHE" landed after the NEXT item's Τεμάχια/numbers line,
# not after its own description). The Κωδικός/Ποσότ./Αξία table columns never
# wrap onto an extra line and stay reliably aligned one-segment-per-item, so
# those drive qty/value/item-count; description is looked up by code instead
# of parsed from the wrapped cell text. Add new (code → description) pairs
# here as new product types show up — parse_receipt_pdf prints a warning and
# falls back to a placeholder for any code not yet in this table.
_RECEIPT_CODE_DESCRIPTIONS = {
    'AG-7467383': 'SYNTHETIC FIBER COSTUME WIG',
    'AG-4649673': 'SYNTHETIC FIBER COSTUME MOUSTACHE',
    'AG-7469284': 'SYNTHETIC FIBER COSTUME BEARD',
}

def parse_receipt_pdf(path):
    """Extract invoice number + item lines (English-only desc, qty, value) from
    a MyData retail-sale receipt PDF."""
    import pdfplumber
    result = {'invoice_number': '', 'items': []}
    with pdfplumber.open(path) as pdf:
        full_text = ''
        item_table = None
        for page in pdf.pages:
            full_text += (page.extract_text() or '') + '\n'
            if item_table is None:
                for table in page.extract_tables():
                    if not table or len(table) < 2:
                        continue
                    header = [(c or '').replace('\n', ' ').strip() for c in table[0]]
                    if 'Κωδικός' in header and 'Περιγραφή' in header:
                        item_table = table
                        break

        m = re.search(r'ΑΛΜΥ-(\d+)', full_text)
        if m:
            result['invoice_number'] = str(int(m.group(1)))

        if item_table:
            header = [(c or '').replace('\n', ' ').strip() for c in item_table[0]]
            def col(label):
                for idx, h in enumerate(header):
                    if h == label: return idx
                return None
            idx_code, idx_qty, idx_val = col('Κωδικός'), col('Ποσότ.'), col('Αξία')
            for row in item_table[1:]:
                if idx_code is None or idx_code >= len(row) or not row[idx_code]:
                    continue
                # A single table row can hold multiple receipt lines that
                # pdfplumber visually merged (same row-height span) — but the
                # code/qty/value cells still hold one '\n'-joined segment per
                # real item, in order, so splitting them recovers each item
                # correctly regardless of how the description cell wrapped.
                codes = row[idx_code].split('\n')
                qtys  = (row[idx_qty] or '').split('\n') if idx_qty is not None and idx_qty < len(row) else []
                vals  = (row[idx_val] or '').split('\n') if idx_val is not None and idx_val < len(row) else []
                for i, code in enumerate(codes):
                    code = code.strip()
                    if not code:
                        continue
                    desc = _RECEIPT_CODE_DESCRIPTIONS.get(code)
                    if not desc:
                        print(f"⚠ Unknown product code '{code}' in receipt — add it to "
                              f"_RECEIPT_CODE_DESCRIPTIONS; using a placeholder description, "
                              f"check it by hand before uploading.")
                        desc = f"ITEM {code}"
                    qty = _fmt_num(qtys[i]) if i < len(qtys) else '1'
                    val = _fmt_num(vals[i]) if i < len(vals) else '0'
                    result['items'].append({'description': desc, 'qty': qty, 'value': val})
    return result

# Matches one item card on the Zonos Prepay confirmation PDF, e.g.:
#   SYNTHETIC FIBER COSTUME WIG          <- Zonos's own title, case varies
#   Customs description:
#   Synthetic fiber costume wig
#   Greece • 6704.11.0000
#   Weight: 0.5 g
#   (1 x 0.5 g)
# Anchored on the literal "Customs description:" marker rather than the
# title line above it: confirmed 2026-08-18 that Zonos renders that title
# inconsistently — ALL CAPS for some orders, sentence case for others, even
# with the identical entered text and HS code — so a regex requiring an
# all-caps title (the original 2026-08-11 assumption) silently matched zero
# items on 3 of 5 real orders in one batch. The "Customs description:" line
# right below is reliably present and holds the same text either way.
_ZONOS_ITEM_RE = re.compile(
    r'Customs description:\n'
    r'(.+?)\n'          # customs description line — the real per-item text
    r'.*?•\s*[\d.]+\n'  # "Country • HS code" line
    r'Weight:\s*([\d.,]+)\s*g',
    re.MULTILINE)

def parse_zonos_pdf(path):
    """Extract per-item (description, weight_kg) pairs from a Zonos Prepay
    confirmation PDF (the "SURNAME_zonos.pdf" barcode/declaration page — never
    the "-invoice" PDF, which has no weight/description breakdown)."""
    import pdfplumber
    items = []
    with pdfplumber.open(path) as pdf:
        full_text = '\n'.join((page.extract_text() or '') for page in pdf.pages)
    for m in _ZONOS_ITEM_RE.finditer(full_text):
        title    = m.group(1).strip()
        weight_g = _parse_num(m.group(2).replace(',', '.'), 0.0)
        items.append({'description': title, 'weight_kg': weight_g / 1000.0})
    return items

def ask_pdf_choice(last_name, candidates, purpose="MyData receipt"):
    """Dialog for when a PDF auto-match is missing/ambiguous.
    Returns a file path, '__RETRY__' to re-scan Downloads, or None to skip."""
    root = tk.Tk(); root.withdraw()
    win = tk.Toplevel(root); win.title(f"{purpose} lookup"); win.attributes('-topmost', True)
    result = {'value': None}
    msg = (f"Found {len(candidates)} possible {purpose} file(s) for '{last_name}' — pick one:"
           if candidates else f"No {purpose} found for '{last_name}' in D:\\Downloads.")
    tk.Label(win, text=msg, padx=20, pady=10, wraplength=420, justify='left').pack()
    listbox = None
    if candidates:
        listbox = tk.Listbox(win, width=60, height=min(6, len(candidates)))
        for c in candidates: listbox.insert(tk.END, os.path.basename(c))
        listbox.pack(padx=20); listbox.selection_set(0)

    def use_selected():
        if listbox and listbox.curselection():
            result['value'] = candidates[listbox.curselection()[0]]
        win.destroy(); root.quit()
    def browse():
        p = filedialog.askopenfilename(title=f"Select {purpose} PDF for {last_name}",
                                        initialdir=RECEIPTS_DIR, filetypes=[("PDF files","*.pdf")])
        result['value'] = p or None
        win.destroy(); root.quit()
    def retry():
        result['value'] = '__RETRY__'; win.destroy(); root.quit()
    def skip():
        win.destroy(); root.quit()

    btns = tk.Frame(win, pady=10); btns.pack()
    if candidates:
        tk.Button(btns, text="Use selected", command=use_selected, width=13).pack(side='left', padx=4)
    tk.Button(btns, text="Browse for file", command=browse, width=13).pack(side='left', padx=4)
    tk.Button(btns, text="Retry search", command=retry, width=13).pack(side='left', padx=4)
    tk.Button(btns, text="Skip (fill by hand)", command=skip, width=16).pack(side='left', padx=4)
    win.protocol("WM_DELETE_WINDOW", skip)
    win.mainloop(); root.destroy()
    return result['value']

def get_receipt_for_record(record):
    last_name = record.get('last_name', '')
    candidates = find_receipt_candidates(last_name)
    while True:
        if len(candidates) == 1:
            return candidates[0]
        choice = ask_pdf_choice(last_name, candidates, purpose="MyData receipt")
        if choice == '__RETRY__':
            candidates = find_receipt_candidates(last_name)
            continue
        return choice

def get_zonos_for_record(record):
    last_name = record.get('last_name', '')
    candidates = find_zonos_candidates(last_name)
    while True:
        if len(candidates) == 1:
            return candidates[0]
        choice = ask_pdf_choice(last_name, candidates, purpose="Zonos confirmation")
        if choice == '__RETRY__':
            candidates = find_zonos_candidates(last_name)
            continue
        return choice

def get_and_parse_receipt(record):
    """Look up the MyData receipt PDF (invoice number/qty/value) and the Zonos
    confirmation PDF (net weight/description) for this record's surname
    (once per record), and merge them: each receipt item's description and
    weight are overridden with the Zonos item at the same position, since
    Zonos has the real per-item weight and the exact declared description.
    Returns (items, invoice_number) — items is [] if nothing was found/parseable."""
    receipt_path = get_receipt_for_record(record)
    items, invoice_number = [], ''
    if receipt_path:
        try:
            parsed = parse_receipt_pdf(receipt_path)
            items = parsed.get('items', [])
            invoice_number = parsed.get('invoice_number', '')
            print(f"✓ Receipt parsed: {os.path.basename(receipt_path)} — "
                  f"{len(items)} item(s), invoice #{invoice_number}")
        except Exception as e:
            print(f"⚠ Could not parse receipt '{receipt_path}': {e}")
            wait_for_user(f"Could not read the receipt automatically ({e}).\n"
                          f"Fill the customs lines by hand, then click Done.")
    else:
        print("⚠ No receipt found — customs lines will need manual entry.")

    zonos_items = []
    if record.get('ship_country', '') in USA_COUNTRY_VALUES:
        zonos_path = get_zonos_for_record(record)
        if zonos_path:
            try:
                zonos_items = parse_zonos_pdf(zonos_path)
                print(f"✓ Zonos confirmation parsed: {os.path.basename(zonos_path)} — "
                      f"{len(zonos_items)} item(s)")
            except Exception as e:
                print(f"⚠ Could not parse Zonos confirmation '{zonos_path}': {e}")
        else:
            print("⚠ No Zonos confirmation found — customs net weight/description "
                  "will need manual entry.")
    # UK (and any non-US destination) has no Zonos step — skip the lookup
    # entirely instead of prompting for a file that will never exist.

    if zonos_items and not items:
        # No MyData receipt — build customs lines from Zonos alone; value/qty
        # need a manual check since Zonos' declared value isn't necessarily
        # the receipt's Aξία.
        items = [{'description': z['description'], 'weight_kg': z['weight_kg'],
                  'qty': '1', 'value': '0'} for z in zonos_items]
        print("⚠ Customs value/quantity defaulted — check against the receipt by hand.")
    elif zonos_items:
        if len(zonos_items) != len(items):
            print(f"⚠ Receipt has {len(items)} item(s) but Zonos confirmation has "
                  f"{len(zonos_items)} — matching by position, check the mismatch by hand.")
        for it, z in zip(items, zonos_items):
            it['description'] = z['description']
            it['weight_kg']   = z['weight_kg']

    return items, invoice_number

# ═══════════════════════════════════════════════════════════════════════════════
# ZONOS PREPAY AUTOMATION
# ═══════════════════════════════════════════════════════════════════════════════
# Selectors below (data-testid attributes) were confirmed live against
# dashboard.zonosprepay.com on 2026-08-18 by inspecting the real DOM — not
# guessed from screenshots. Two gaps, called out where they occur: the
# Ship-from/Ship-to comboboxes on the setup screen were never actually
# exercised live (their saved defaults were already correct both times this
# was tested), and the Invoice document URL is inferred from its observed
# pattern rather than confirmed fresh. Everything else (item entry, Made-in
# combobox, attestation, compliance, duties, reaching the payment step) was
# driven and verified end-to-end today.

ZONOS_URL         = "https://dashboard.zonosprepay.com/en/ship"
ZONOS_MADE_IN     = "Greece"
ZONOS_LOGIN_EMAIL = "damoncollective@gmail.com"
# Dotted form of CUSTOMS_TARIFF_CODE ("67041100" -> "6704.11.0000") — Zonos
# wants the dotted HS code, ELTA's CSV wants the plain digits; both must stay
# the same underlying code (see CUSTOMS_TARIFF_CODE's own comment).
ZONOS_HS_CODE = f"{CUSTOMS_TARIFF_CODE[:4]}.{CUSTOMS_TARIFF_CODE[4:6]}.{CUSTOMS_TARIFF_CODE[6:]}"

def compute_item_weights_kg(gross_kg, items):
    """Deterministic per-item net weight, replacing manual Zonos entry
    (rule confirmed by user 2026-08-18):

        net_g = round_nearest_10( min(gross_g * 0.8, gross_g - 120) )

    (the -120 is a packaging-weight floor: for light items, 80% of gross
    would leave less than 120g for packaging, which isn't realistic, so the
    net weight comes out lower than the 80% average for those).

    net_g is then split across items, ranked by PER-UNIT price (value/qty)
    descending — ties broken arbitrarily, it doesn't matter which:
      1 item   -> the whole net weight, no adjustment
      2 items  -> priciest baseline+30, other baseline-30
      3 items  -> priciest baseline+30, 2nd baseline-10, 3rd baseline-20
      4+ items -> rare in practice (user's own words) and not fully specified;
                  best-effort extension of the same shape (priciest +50,
                  remainder shared over the rest in 10g steps). The payment
                  pause is a natural checkpoint to eyeball/fix this by hand
                  before paying if it looks off.
    `baseline` = net_g / item_count, rounded to nearest 10g.

    Returns weights in KG, in the SAME order as `items` (not rank order).
    """
    n = len(items)
    if n == 0:
        return []
    gross_g = gross_kg * 1000.0
    net_g = max(0.0, min(gross_g * 0.8, gross_g - 120.0))
    net_g = round(net_g / 10.0) * 10
    if n == 1:
        return [net_g / 1000.0]

    baseline = round((net_g / n) / 10.0) * 10
    unit_prices = [_parse_num(it.get('value', '0')) / max(_parse_num(it.get('qty', '1'), 1), 1)
                   for it in items]
    order = sorted(range(n), key=lambda i: unit_prices[i], reverse=True)

    if n == 2:
        deltas = [30, -30]
    elif n == 3:
        deltas = [30, -10, -20]
    else:
        print(f"⚠ {n}-item order — the weight split beyond 3 items is a rare, "
              f"best-effort case (priciest +50g, rest share -50g). Double-check "
              f"the numbers on the Zonos page before paying.")
        remaining = n - 1
        share = round((-50 / remaining) / 10.0) * 10
        deltas = [50] + [share] * (remaining - 1)
        deltas.append(-50 - sum(deltas[1:]))  # exact remainder onto the last one

    weights_g = [0] * n
    for rank, idx in enumerate(order):
        weights_g[idx] = baseline + deltas[rank]
    return [w / 1000.0 for w in weights_g]

def launch_zonos_browser():
    driver = webdriver.Firefox()
    driver.maximize_window()
    return driver

def zonos_ensure_logged_in(driver):
    """Navigate to the Ship page; if Zonos isn't already logged in, pause for
    the user to log in by hand (email above) — the password is never stored
    or typed by this script, same pause-and-continue pattern as the old ELTA
    CAPTCHA step."""
    driver.get(ZONOS_URL)
    try:
        WebDriverWait(driver, 8).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="ship-from-selector"]')))
        return
    except Exception:
        pass
    wait_for_user(f"Please log in to Zonos Prepay in the browser window "
                  f"(email: {ZONOS_LOGIN_EMAIL}), then click Done.")
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="ship-from-selector"]')))

def _zonos_select_combo(driver, button_testid, search_text):
    """Click a react-select-style combobox button, type to filter, click the
    matching option. UNCONFIRMED for ship-from-selector/ship-to-selector
    specifically (their saved defaults were already correct both times this
    was tested live) — confirmed working for the per-item Made-in field,
    which uses the identical component pattern."""
    click_with_retry(driver, By.CSS_SELECTOR, f'[data-testid="{button_testid}"]',
                      f"Zonos: click combobox '{button_testid}'", use_js_fallback=False)
    time.sleep(0.4)
    active = driver.switch_to.active_element
    active.clear()
    active.send_keys(search_text)
    time.sleep(0.6)
    input_id = active.get_attribute('id')  # e.g. "react-select-1-input"
    m = re.match(r'(react-select-\d+)-input', input_id or '')
    if not m:
        # Added 2026-08-20: this used to raise, which escapes straight to
        # the order-level handler. The far more common cause in practice is
        # that the preceding click_with_retry paused for a manual fix, the
        # user picked the option themselves (closing the dropdown, moving
        # focus elsewhere) — so by the time we get here the field is
        # already correctly set and there's simply no combobox open to
        # click an option in. Trust that and move on instead of crashing.
        print(f"⚠ Could not resolve react-select id for '{button_testid}' "
              f"(got id='{input_id}') — assuming it was already set by hand, continuing.")
        return
    click_with_retry(driver, By.CSS_SELECTOR, f'[id^="{m.group(1)}-option"]',
                      f"Zonos: click combobox '{button_testid}' option", timeout=5)

def zonos_ensure_shipment_setup(driver):
    """Ship from Hellenic Post / Ship to United States / Standard package —
    checks the current state and only touches a field if it's wrong, since
    Zonos remembers the last-used values within a browser session."""
    driver.get(ZONOS_URL)
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="ship-from-selector"]')))
    if "Hellenic Post" not in driver.find_element(By.CSS_SELECTOR, '[data-testid="ship-from-selector"]').text:
        _zonos_select_combo(driver, "ship-from-selector", "Hellenic")
    if "United States" not in driver.find_element(By.CSS_SELECTOR, '[data-testid="ship-to-selector"]').text:
        _zonos_select_combo(driver, "ship-to-selector", "United States")
    std_btn = driver.find_element(By.XPATH, "//button[normalize-space()='Standard package']")
    if std_btn.get_attribute('aria-pressed') != 'true':
        click_with_retry(driver, By.XPATH, "//button[normalize-space()='Standard package']",
                          "Zonos: click 'Standard package'")
    click_with_retry(driver, By.CSS_SELECTOR, '[data-testid="ship-setup-continue"]',
                      "Zonos: click ship-setup Continue")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="step-add-items"]')))

def zonos_add_item(driver, description, unit_value_eur, qty, weight_g, is_first_item):
    """Fill one item card and Save. `is_first_item` controls whether
    '+ Add another item' needs clicking first to open a fresh form."""
    if not is_first_item:
        click_with_retry(driver, By.CSS_SELECTOR, '[data-testid="add-another-item-button"]',
                          "Zonos: click 'Add another item'")
        time.sleep(0.5)

    # The AI auto-fill toggle defaults ON for every fresh item form — confirmed
    # live 2026-08-18 that this resets per item, not just once per shipment.
    toggle_cb = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, '[data-testid="auto-classify-toggle"] input[type="checkbox"]')))
    if toggle_cb.is_selected():
        click_with_retry(driver, By.CSS_SELECTOR,
                          '[data-testid="auto-classify-toggle"] input[type="checkbox"]',
                          "Zonos: turn off auto-classify toggle")

    desc_el = find_with_wait(driver, By.CSS_SELECTOR, '[data-testid="item-description-input"]',
                              "Zonos: find item description field")
    desc_el.clear(); desc_el.send_keys(description)

    val_el = find_with_wait(driver, By.CSS_SELECTOR, '[data-testid="item-value-input"]',
                             "Zonos: find item value field")
    val_el.clear(); val_el.send_keys(f"{unit_value_eur:.2f}")

    hs_el = find_with_wait(driver, By.CSS_SELECTOR, '[data-testid="item-hs-code-input"]',
                            "Zonos: find item HS-code field")
    hs_el.clear(); hs_el.send_keys(ZONOS_HS_CODE)

    # Made in — react-select combobox: a real click opens it (a synthetic JS
    # click does not — confirmed live), typing filters it, then click the
    # single filtered option.
    click_with_retry(driver, By.CSS_SELECTOR, '[data-testid="amino--made-in--"]',
                      "Zonos: click Made-in field", use_js_fallback=False)
    time.sleep(0.4)
    made_in_input = driver.switch_to.active_element
    made_in_input.send_keys(ZONOS_MADE_IN)
    time.sleep(0.6)
    input_id = made_in_input.get_attribute('id')
    m = re.match(r'(react-select-\d+)-input', input_id or '')
    if not m:
        # Added 2026-08-20 (crashed live, Toni Willis order): if the earlier
        # click_with_retry above paused for a manual fix and the user picked
        # "Made in" themselves, the dropdown is already closed and focus has
        # moved on by the time we get here — there's no option left to
        # click. Trust the manual fix instead of crashing on m.group(1).
        print(f"⚠ Could not resolve react-select id for Made-in field "
              f"(got id='{input_id}') — assuming it was already set by hand, continuing.")
    else:
        click_with_retry(driver, By.CSS_SELECTOR, f'[id^="{m.group(1)}-option"]',
                          "Zonos: click Made-in option", timeout=5)

    # Qty and Unit weight have no data-testid of their own, but their position
    # within item-manual-fields is reliable (confirmed 2026-08-18): input
    # index 1 = Qty, last input = Unit weight (g) — regardless of whether the
    # Made-in field is open or closed at the time.
    fields_container = find_with_wait(driver, By.CSS_SELECTOR, '[data-testid="item-manual-fields"]',
                                       "Zonos: find item qty/weight fields container")
    inputs = fields_container.find_elements(By.TAG_NAME, "input")
    qty_el = inputs[1]
    qty_el.clear(); qty_el.send_keys(str(qty))
    weight_el = inputs[-1]
    weight_el.clear(); weight_el.send_keys(str(int(round(weight_g))))

    click_with_retry(driver, By.CSS_SELECTOR, '[data-testid="save-item-button"]',
                      "Zonos: click Save item")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="add-another-item-button"]')))

def zonos_finish_items_and_reach_payment(driver):
    """Tick attestation, check compliance, calculate duties, continue —
    stops right at the payment step, never touches the Pay button."""
    click_with_retry(driver, By.CSS_SELECTOR, '[data-testid="confirm-information-checkbox"]',
                      "Zonos: click attestation checkbox")
    time.sleep(0.3)
    click_with_retry(driver, By.CSS_SELECTOR, '[data-testid="calculate-duties-button"]',
                      "Zonos: click Calculate duties")
    click_with_retry(driver, By.CSS_SELECTOR, '[data-testid="clarify-success-continue-button"]',
                      "Zonos: click Continue after duties", timeout=10)
    click_with_retry(driver, By.CSS_SELECTOR, '[data-testid="amino--continue"]',
                      "Zonos: click final Continue to payment", timeout=15)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="step-review-pay"]')))

def zonos_pause_for_payment(record):
    """Blocks until the user completes card/CVC and clicks Pay themselves in
    the browser, then confirms here. Payment is deliberately never
    automated — same rule as every other pause in this project."""
    wait_for_user(
        f"Zonos: {record.get('full_name','?')} — review the items/duties shown, "
        f"complete payment (card/CVC) in the browser, then click Done here.")

def zonos_save_documents(driver, record, output_dir):
    """After payment, the browser lands on the confirmation page. Save both
    the confirmation/barcode page and the Invoice as real headless PDFs via
    Selenium's print_page() (CDP-backed, no native print dialog — this is
    exactly what blocked full automation when this step was done by hand via
    Claude in Chrome). Returns (confirmation_path, invoice_path)."""
    WebDriverWait(driver, 90).until(EC.url_contains("/en/confirmation/checkout_session_"))
    m = re.search(r'checkout_session_[\w-]+', driver.current_url)
    if not m:
        raise RuntimeError(f"Unexpected confirmation URL: {driver.current_url}")
    session_id = m.group(0)
    surname  = strip_accents(record.get('last_name', 'UNKNOWN')).upper().replace(' ', '')
    date_str = datetime.date.today().strftime('%d%m%y')
    os.makedirs(output_dir, exist_ok=True)

    conf_path = os.path.join(output_dir, f"{surname}_zonos_{date_str}.pdf")
    with open(conf_path, 'wb') as f:
        f.write(base64.b64decode(driver.print_page()))

    # Invoice document URL inferred from its observed pattern
    # (.../en/document/{session_id}?print=1&filename=...) seen in the
    # browser's own tab title during a live 2026-08-18 session — not yet
    # re-confirmed against a freshly automated order. If this 404s or shows
    # the wrong document, the fallback is clicking the page's own "Invoice"
    # button and print_page()-ing wherever that navigates to instead.
    invoice_url = f"https://dashboard.zonosprepay.com/en/document/{session_id}?print=1"
    driver.get(invoice_url)
    WebDriverWait(driver, 15).until(
        lambda d: d.execute_script("return document.readyState") == "complete")
    inv_path = os.path.join(output_dir, f"{surname}_zonos-invoice_{date_str}.pdf")
    with open(inv_path, 'wb') as f:
        f.write(base64.b64decode(driver.print_page()))

    print(f"✓ Zonos documents saved: {os.path.basename(conf_path)}, {os.path.basename(inv_path)}")
    return conf_path, inv_path

def process_zonos_batch(records, catalog=None):
    """End-to-end Zonos automation for a batch of US records: parse each
    receipt, compute per-item net weight, drive Zonos through item entry,
    compliance, and duties, pause for payment, then save both documents with
    the SURNAME_zonos_DDMMYY.pdf naming convention. Non-US records are
    skipped — there's no Zonos step outside the US."""
    us_records = [r for r in records if r.get('ship_country', '') in USA_COUNTRY_VALUES]
    if not us_records:
        wait_for_user("No US orders in this batch — nothing for Zonos to do.")
        return

    driver = launch_zonos_browser()
    try:
        zonos_ensure_logged_in(driver)
        for i, record in enumerate(us_records):
            print(f"\n--- Zonos {i+1}/{len(us_records)}: {record.get('full_name','?')} ---")
            try:
                receipt_path = get_receipt_for_record(record)
                if not receipt_path:
                    print(f"⚠ No receipt found for {record.get('last_name','?')} — skipping Zonos for this order.")
                    continue
                parsed = parse_receipt_pdf(receipt_path)
                items = parsed.get('items', [])
                if not items:
                    print(f"⚠ Receipt parsed but no items found for {record.get('last_name','?')} — skipping.")
                    continue

                gross_kg = _parse_num(record.get('weight_kg', ''), 0.0)
                if gross_kg <= 0:
                    print(f"⚠ No package weight on record for {record.get('last_name','?')} — skipping Zonos.")
                    continue
                weights_kg = compute_item_weights_kg(gross_kg, items)
                for it, w in zip(items, weights_kg):
                    it['weight_kg'] = w

                zonos_ensure_shipment_setup(driver)
                for idx, it in enumerate(items):
                    unit_value = _parse_num(it.get('value', '0')) / max(_parse_num(it.get('qty', '1'), 1), 1)
                    try:
                        zonos_add_item(driver, it['description'], unit_value,
                                       int(_parse_num(it.get('qty', '1'), 1)),
                                       it['weight_kg'] * 1000.0, is_first_item=(idx == 0))
                    except Exception as item_err:
                        # Added 2026-08-20: a failure filling ONE item used to
                        # escape all the way to the per-order handler below,
                        # abandoning every remaining item in this order. Now
                        # it pauses right here and resumes the SAME loop with
                        # the next item afterward, matching the try-step /
                        # ask-user / continue-next-step pattern used
                        # everywhere else in this script.
                        print(f"⚠ Zonos item {idx+1}/{len(items)} error for "
                              f"{record.get('full_name','?')}: {item_err}")
                        wait_for_user(f"Problem adding item {idx+1}/{len(items)} "
                                      f"({it.get('description','?')}) for "
                                      f"{record.get('full_name','?')}: {item_err}\n\n"
                                      f"Please add/fix this item by hand in the browser "
                                      f"(click '+ Add another item' first if needed), then "
                                      f"click Done to continue with the remaining items.")
                zonos_finish_items_and_reach_payment(driver)
                zonos_pause_for_payment(record)
                zonos_save_documents(driver, record, RECEIPTS_DIR)
            except Exception as e:
                print(f"❌ Zonos error for {record.get('full_name','?')}: {e}")
                wait_for_user(f"Zonos automation hit an error for "
                              f"{record.get('full_name','?')}: {e}\n\n"
                              f"Fix manually in the browser if needed, then click Done "
                              f"to continue with the next order.")
    finally:
        driver.quit()
        print("Zonos browser closed.")

# ═══════════════════════════════════════════════════════════════════════════════
# BULK-UPLOAD CSV EXPORT
# ═══════════════════════════════════════════════════════════════════════════════
# Header matches D:\Downloads\Sample_File.xlsx exactly (72 columns, A-BT) — the
# template ELTA gives business customers for "Εισαγωγή Στοιχείων Αντικειμένων
# Από Αρχείο". Field-by-field rules are in D:\Downloads\Instructions.xls.

CSV_HEADER = [
    "Country","Service","ID","Given Name","Surname","Organisation Name",
    "Registration Number","Pick Up Point","Parcel Locker","Street Name",
    "Street Number","Extension","Street Specification","Postal Code",
    "District Number","Town","Region / State","District","County",
    "Telephone Number","Email","Reference No","Weight (in Kg)","Length (in cm)",
    "Width (in cm)","Height (in cm)","Quantity","COD (In €)",
    "Insured Value (In €)","Gift","Documents","Commercial sample",
    "Returned goods","Sale Of Goods","Other","Explanation",
] + [
    "Detailed description of contents","Quantity","Net weight (in Kg)",
    "Value (in €)","HS tariff number","Country of origin of goods",
] * 5 + [
    "Comments","Importer's reference","Importer's telephone/fax/e-mail",
    "Licence No(s)","Certificate No(s)","Invoice No(s)",
]
assert len(CSV_HEADER) == 72

MAX_CUSTOMS_LINES = 5

def _csv_int(value, default=0):
    n = _parse_num(value, default)
    return str(int(round(n)))

def build_csv_row(record, service_pref, items, invoice_number):
    """Build one 72-column row (list of strings) for the ELTA bulk-upload CSV.
    `items`/`invoice_number` come from get_and_parse_receipt(record) — same
    merge of the MyData receipt + (US-only) Zonos confirmation used in 1.3."""
    country_iso = COUNTRY_TO_ISO2.get(record.get('ship_country',''), '')
    service     = resolve_service_code(country_iso, service_pref)

    # Same 70%-of-gross-weight fallback as 1.3 for customs lines with no
    # Zonos-sourced weight (US items always have one when Zonos parsed OK;
    # UK items never do, since there's no Zonos step for the UK).
    missing_weight_items = [it for it in items if not it.get('weight_kg')]
    fallback_each_kg = None
    if missing_weight_items:
        gross_kg = _parse_num(record.get('weight_kg', ''), 0.0)
        if gross_kg > 0:
            fallback_each_kg = (gross_kg * 0.7) / len(missing_weight_items)

    if len(items) > MAX_CUSTOMS_LINES:
        print(f"⚠ {record.get('full_name','?')}: {len(items)} items found, "
              f"only the first {MAX_CUSTOMS_LINES} fit the CSV's customs block — "
              f"the rest are dropped, check by hand.")

    customs_cols = []
    for item in items[:MAX_CUSTOMS_LINES]:
        desc = _short_customs_description(item.get('description', ''))[:CUSTOMS_DESCRIPTION_MAX_LEN]
        if item.get('weight_kg'):
            net_weight = _fmt_weight_kg(item['weight_kg'])
        elif fallback_each_kg is not None:
            net_weight = _fmt_weight_kg(fallback_each_kg)
            print(f"⚠ {record.get('full_name','?')}: no Zonos weight for '{desc}' — "
                  f"defaulted net weight to 70% of gross ÷ "
                  f"{len(missing_weight_items)} missing item(s) = {net_weight} kg")
        else:
            net_weight = CUSTOMS_LINE_NET_WEIGHT_KG
            print(f"⚠ {record.get('full_name','?')}: no Zonos weight and no gross "
                  f"weight available for '{desc}' — used the "
                  f"{CUSTOMS_LINE_NET_WEIGHT_KG} kg fallback constant.")
        customs_cols += [desc, _csv_int(item.get('qty', '1'), 1),
                          net_weight, item.get('value', '0'),
                          CUSTOMS_TARIFF_CODE, "GR"]
    customs_cols += [""] * (6 * (MAX_CUSTOMS_LINES - len(items[:MAX_CUSTOMS_LINES])))

    row = [
        country_iso,                                          # A  Country
        service,                                               # B  Service
        "",                                                     # C  ID (recipient code — always inline for v1)
        strip_accents(record.get("first_name","")),             # D  Given Name
        strip_accents(record.get("last_name","")),              # E  Surname
        "",                                                     # F  Organisation Name
        "",                                                     # G  Registration Number
        "",                                                     # H  Pick Up Point
        "0",                                                    # I  Parcel Locker
        strip_accents(record.get("street_1","")),                # J  Street Name
        strip_accents(record.get("street_number","")),           # K  Street Number
        "",                                                     # L  Extension
        strip_accents(record.get("street_2","")),                 # M  Street Specification (address line 2)
        strip_accents(record.get("ship_zipcode","")),             # N  Postal Code
        "",                                                     # O  District Number
        strip_accents(record.get("ship_city","")),                # P  Town
        strip_accents(record.get("ship_state","")),               # Q  Region / State
        "",                                                     # R  District
        "",                                                     # S  County
        re.sub(r'\D', '', record.get("phone","")),                # T  Telephone Number — digits
                                                                   # only (2026-08-20: a customer-
                                                                   # entered "(616)302-2487" survived
                                                                   # with only whitespace stripped and
                                                                   # ELTA's bulk-upload rejected it as
                                                                   # "Μη έγκυρη τιμή" — strip everything
                                                                   # but digits, not just whitespace)
        record.get("email",""),                                  # U  Email
        record.get("order_id",""),                               # V  Reference No
        _fmt_weight_kg(record.get("weight_kg","")),               # W  Weight (in Kg)
        _csv_int(record.get("length_cm",""), 0),                  # X  Length (in cm)
        _csv_int(record.get("width_cm",""), 0),                   # Y  Width (in cm)
        _csv_int(record.get("height_cm",""), 0),                  # Z  Height (in cm)
        "",                                                     # AA Quantity — package count, optional,
                                                                   # "Standard Value (1)" per spec; leave blank
                                                                   # and let ELTA default it (2026-08-18: a real
                                                                   # upload was rejected with "must not have a
                                                                   # value (Quantity)" when this held the item
                                                                   # count instead — this field is package count,
                                                                   # not item count, which is AL/AR/AX/BD/BJ below)
        "0",                                                     # AB COD (In €)
        "0",                                                     # AC Insured Value (In €)
        "0",                                                     # AD Gift
        "0",                                                     # AE Documents
        "0",                                                     # AF Commercial sample
        "0",                                                     # AG Returned goods
        "1",                                                     # AH Sale Of Goods
        "0",                                                     # AI Other
        "",                                                     # AJ Explanation
        *customs_cols,                                           # AK-BN customs lines ×5
        "",                                                     # BO Comments
        "",                                                     # BP Importer's reference
        "",                                                     # BQ Importer's telephone/fax/e-mail
        "",                                                     # BR Licence No(s)
        "",                                                     # BS Certificate No(s)
        invoice_number or "",                                    # BT Invoice No(s)
    ]
    assert len(row) == 72
    return row

def write_shipment_csv(rows):
    """Write rows (each a 72-item list, see build_csv_row) to a timestamped
    semicolon-delimited CSV in OUTPUT_DIR, matching the ';'-delimited,
    UTF-8-BOM format ELTA's own Recipient_Sample.xls turned out to actually be
    (a Greek-locale 'Excel → Save as CSV' export, not a real .xlsx)."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(OUTPUT_DIR, f"ELTA_BULK_{ts}.csv")
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(CSV_HEADER)
        w.writerows(rows)
    return path

def process_csv_export(shipping_records, mode, catalog, service_pref='parcel'):
    """Replaces 1.3's process_elta_labels/process_all_records — no browser, no
    per-record submission. Builds one CSV row per record (still via the same
    receipt+Zonos parsing, DB upsert, and thank-you-letter flow as before),
    then writes the whole batch to one file for the user to upload by hand on
    weblabeling.elta.gr.

    service_pref='ask' (2.2, 2026-08-19) means the run-wide choice was "let
    me choose per order" — pause once per record via
    ask_service_preference_for_record() instead of using one default for the
    whole batch."""
    if not shipping_records:
        return
    rows, problems = [], []
    for index, record in enumerate(shipping_records):
        print(f"\n--- Record {index+1}/{len(shipping_records)}: "
              f"{record.get('first_name','')} {record.get('last_name','')} ---")
        try:
            record_pref = (ask_service_preference_for_record(record)
                            if service_pref == 'ask' else service_pref)
            print(f"   Service: {'CP' if record_pref == 'parcel' else 'LL'}")

            parsed_items, invoice_number = ([], '')
            if needs_customs(record):
                parsed_items, invoice_number = get_and_parse_receipt(record)
                if not invoice_number:
                    problems.append(f"{record.get('full_name','?')}: no invoice number "
                                     f"found — Sale of Goods requires one, check by hand.")

            rows.append(build_csv_row(record, record_pref, parsed_items, invoice_number))

            # Was this customer already in the DB BEFORE this order? (must check
            # before upsert_customer(), which saves/increments this order into the DB)
            _db_pre = load_customer_db()
            _key    = customer_db_key(record)
            _in_db  = (_key and _key in _db_pre and
                       _db_pre[_key].get("total_orders", 0) > 0)

            upsert_customer(record, sku=record.get('sku',''), carrier='ELTA')
            if catalog:
                bump_items_shipped(catalog, record)

            if mode == 'both':
                is_returning = ask_yes_no(
                    f"Is {record.get('full_name', 'this customer')} a RETURNING customer?\n\n"
                    f"(Yes → returning letter,  No → first-time letter)"
                ) if _in_db else False
                try:
                    generate_thank_you(record)
                    if is_returning:
                        generate_thank_you_return(record)
                except Exception as e:
                    print(f"⚠ Letter error: {e}")

        except Exception as e:
            print(f"❌ Record {index+1} error: {e}")
            problems.append(f"{record.get('full_name','?')}: {e}")

    if not rows:
        print("⚠ No rows generated — nothing to write.")
        return

    path = write_shipment_csv(rows)
    print(f"\n✓ {len(rows)} shipment row(s) written to {path}")
    summary = [f"✓ {len(rows)} shipment row(s) written to:", path]
    if problems:
        print(f"\n⚠ {len(problems)} row(s) need a manual check before uploading:")
        for p in problems:
            print(f"   - {p}")
        summary += ["", f"⚠ {len(problems)} row(s) need a manual check (see console)."]

    root = tk.Tk(); root.withdraw(); root.attributes('-topmost', True)
    messagebox.showinfo("CSV export done", "\n".join(summary))
    root.destroy()


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("ELTA_Damon2.9 — Business-Account CSV Bulk-Upload + Automated Zonos Prepay")
    sync_dbs_from_github()
    try:
        run_mode = ask_run_mode()   # 'live' | 'historical' | 'from_db' | 'db_manager'

        # ── DB Manager ───────────────────────────────────────────────────────
        if run_mode == 'db_manager':
            open_db_manager()

        # ── From Database ─────────────────────────────────────────────────────
        elif run_mode == 'from_db':
            service_pref = ask_service_preference()
            customers = pick_customers_from_db()
            if not customers:
                raise SystemExit("No customer selected.")

            def _build_record(customer):
                full  = customer.get('full_name', '').strip()
                first = customer.get('first_name', '').strip()
                last  = customer.get('last_name', '').strip()
                if not first and not last and full:
                    parts = full.rsplit(' ', 1)
                    first = parts[0] if len(parts) == 2 else full
                    last  = parts[1] if len(parts) == 2 else ''
                return {
                    'order_id':      '',
                    'full_name':     full,
                    'first_name':    first,
                    'last_name':     last,
                    'street_1':      customer.get('street_1', ''),
                    'street_number': customer.get('street_number', ''),
                    'street_2':      customer.get('street_2', ''),
                    'ship_city':     customer.get('ship_city', ''),
                    'ship_state':    customer.get('ship_state', ''),
                    'ship_zipcode':  customer.get('ship_zipcode', ''),
                    'ship_country':  customer.get('ship_country', ''),
                    'email':         customer.get('email', ''),
                    'phone':         customer.get('phone', ''),
                    'buyer':         '',
                    'etsy_title':    '',
                    'etsy_items':    [],
                    'value_eur':     '',
                    'print_label':   True,
                    'carrier':       'ELTA',
                    'sku':           '',
                    'product_name':  '',
                    'weight_kg':     '0,49',
                    'length_cm':     '21',
                    'width_cm':      '28',
                    'height_cm':     '12',
                    'customs_qty':   '2',
                    'order_date':    datetime.date.today().isoformat(),
                }

            records = [_build_record(c) for c in customers]

            choice = ask_what_to_run()
            root = tk.Tk()
            app  = EltaShippingApp(root, filepath='', mode=choice['mode'],
                                   records=records, historical=False, from_db=True,
                                   service_pref=service_pref, zonos=choice['zonos'])
            root.after(50, app.load_orders)
            root.mainloop()

        # ── Live / Historical (from Etsy file) ───────────────────────────────
        else:
            service_pref = ask_service_preference() if run_mode == 'live' else 'parcel'
            while True:
                filepath = ask_for_orders_file()
                try:
                    all_records = load_orders_from_html(filepath)
                except ValueError as e:
                    fname = os.path.basename(filepath)
                    if "EMPTY_FILE" in str(e):
                        msg = f"There are no data in the file '{fname}'.\n\nTry another file?"
                    else:
                        msg = (f"Data in file '{fname}' are not in a format I can read.\n"
                               f"Please save the orders page again from Etsy and try again.\n\n"
                               f"Try another file?")
                    if ask_yes_no(msg):
                        continue
                    raise SystemExit("Aborted.")
                if not all_records:
                    fname = os.path.basename(filepath)
                    if ask_yes_no(f"No orders found in '{fname}'.\n\nTry another file?"):
                        continue
                    raise SystemExit("No orders found.")
                break

            selected = show_order_selection(all_records)
            if not selected:
                raise SystemExit("No orders selected.")
            print(f"✓ {len(selected)} order(s) selected.")

            if run_mode == 'historical':
                root = tk.Tk()
                app  = EltaShippingApp(root, filepath=filepath, mode='labels',
                                       records=selected, historical=True)
                root.after(50, app.load_orders)
                root.mainloop()

            else:
                choice = ask_what_to_run()
                if choice['mode'] == 'letters' and not choice['zonos']:
                    for r in selected:
                        try: generate_thank_you(r)
                        except Exception as e: print(f"⚠ {e}")
                    print("Done. Letters saved to", OUTPUT_DIR)
                else:
                    root = tk.Tk()
                    app  = EltaShippingApp(root, filepath=filepath, mode=choice['mode'],
                                           records=selected, historical=False,
                                           service_pref=service_pref, zonos=choice['zonos'])
                    root.after(50, app.load_orders)
                    root.mainloop()

    except SystemExit as e:
        print(str(e))
    except Exception as e:
        import traceback; traceback.print_exc()
