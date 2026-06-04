"""
ELTA Weblabeling & Shipping CRM — v5.3
Features:
  - Product catalog with unique SKUs (WIG-001, WIG-002 …)
  - Auto-SKU resolution: fuzzy title match + confirm dialog (same item / new item)
  - Auto-save dims/weight/customs value to catalog per SKU
  - Customer CRM: returning customer dialog with stored vs new address comparison
  - Keep / Update (session only) / Update + Save to DB options
  - Historical import mode (data only, no labels)
  - Carrier selection per order: ELTA or FedEx
  - FedEx batch CSV export
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
import time, random, json, os, re, datetime, csv, unicodedata
from difflib import SequenceMatcher
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

SENDER = {
    "name":    "KONSTANTINOS PAPAPANAGIOTOU",
    "phone":   "2107511202",
    "line1":   "DAMAGITOU 24",
    "postcode":"11631",
    "city":    "ATHENS",
    "country": "GR",
    "email":   "damoncollective@gmail.com",
}

FEDEX_ITEM_PREFIX = "MID ELDAM24DAATH/ "   # prefix in FedEx itemDescription column

EU_COUNTRIES = {
    "Austria","Belgium","Bulgaria","Croatia","Cyprus","Czech Republic",
    "Denmark","Estonia","Finland","France","Germany","Greece","Hungary",
    "Ireland","Italy","Latvia","Lithuania","Luxembourg","Malta","Netherlands",
    "Poland","Portugal","Romania","Slovakia","Slovenia","Spain","Sweden",
}

COUNTRY_NAME_MAP = {
    "United Kingdom": "Great Britain",
    "Spain": "ES Spain",
}

COUNTRY_TO_ISO2 = {
    "United States":"US","United States of America":"US","USA":"US",
    "United Kingdom":"GB","Great Britain":"GB","Germany":"DE","France":"FR",
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
    with open(CATALOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

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

def ask_similar_or_new(catalog, etsy_title, similar_skus):
    """
    Dialog: is the new Etsy title the same product as an existing SKU, or a new product?
    Returns (sku, entry).
    """
    result = [None, None]
    root = tk.Tk(); root.title("New Product — Match?")
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
    root.grab_set(); root.mainloop()
    return result[0], result[1]

def auto_resolve_sku(catalog, etsy_title):
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
        return ask_similar_or_new(catalog, etsy_title, similar)
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
    with open(CUSTOMER_DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

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


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def human_delay(a=1, b=3):
    time.sleep(random.uniform(a, b))

def safe_screenshot(driver, filename):
    try:
        driver.save_screenshot(filename)
    except Exception:
        pass

def strip_accents(text):
    text = str(text).replace('ß', 'ss').replace('SS', 'SS')
    nfkd = unicodedata.normalize('NFKD', text)
    return ''.join(c for c in nfkd if not unicodedata.combining(c))


# ═══════════════════════════════════════════════════════════════════════════════
# ETSY ORDER PARSER
# ═══════════════════════════════════════════════════════════════════════════════

def load_orders_from_html(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()

    start = html.find('Etsy.Context=')
    if start == -1:
        raise ValueError("Could not find Etsy.Context in the file.")
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
            'ship_state':    addr.get('state', ''),
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

def show_customer_update_dialog(record, stored):
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

    root = tk.Tk(); root.title("Returning Customer")
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
    root.grab_set(); root.mainloop()
    return result[0], result[1]


def ask_run_mode():
    """Returns 'live' or 'historical'."""
    result = ['live']
    root = tk.Tk(); root.title("ELTA 5.3 — Mode")
    root.attributes('-topmost', True); root.resizable(False, False)
    tk.Label(root, text="Choose processing mode:",
             font=('Arial', 13, 'bold'), pady=16, padx=20).pack()
    bf = tk.Frame(root); bf.pack(pady=(0, 18), padx=20)
    def pick(v): result[0]=v; root.destroy()
    tk.Button(bf, text="▶  Live Processing\n(labels, letters, FedEx CSV)",
              command=lambda: pick('live'),
              bg='#2980b9', fg='white', font=('Arial',11,'bold'),
              relief='flat', padx=20, pady=10, cursor='hand2', width=28).pack(pady=6)
    tk.Button(bf, text="📂  Historical Import\n(data only — no labels)",
              command=lambda: pick('historical'),
              bg='#7f8c8d', fg='white', font=('Arial',11,'bold'),
              relief='flat', padx=20, pady=10, cursor='hand2', width=28).pack(pady=6)
    root.update_idletasks()
    w, h = root.winfo_reqwidth(), root.winfo_reqheight()
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")
    root.grab_set(); root.mainloop()
    return result[0]

def ask_mode():
    """Labels+Letters / Labels only / Letters only. Returns 'both','labels','letters'."""
    result = ['both']
    root = tk.Tk(); root.title("What to run?")
    root.attributes('-topmost', True); root.resizable(False, False)
    tk.Label(root, text="What to process?", font=('Arial',12,'bold'),
             pady=14, padx=16).pack()
    bf = tk.Frame(root); bf.pack(pady=(4,16))
    def pick(v): result[0]=v; root.destroy()
    tk.Button(bf, text="Ετικέτες + Ευχαριστήρια", command=lambda:pick('both'),
              bg='#2980b9', fg='white', font=('Arial',11,'bold'),
              relief='flat', padx=14, pady=7, cursor='hand2').pack(fill='x',padx=12,pady=4)
    tk.Button(bf, text="Μόνο Ετικέτες", command=lambda:pick('labels'),
              bg='#27ae60', fg='white', font=('Arial',11,'bold'),
              relief='flat', padx=14, pady=7, cursor='hand2').pack(fill='x',padx=12,pady=4)
    tk.Button(bf, text="Μόνο Ευχαριστήρια", command=lambda:pick('letters'),
              bg='#8e44ad', fg='white', font=('Arial',11,'bold'),
              relief='flat', padx=14, pady=7, cursor='hand2').pack(fill='x',padx=12,pady=4)
    root.update_idletasks()
    w, h = root.winfo_reqwidth(), root.winfo_reqheight()
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")
    root.grab_set(); root.mainloop()
    return result[0]


# ═══════════════════════════════════════════════════════════════════════════════
# ORDER SELECTION TABLE  (with Carrier column)
# ═══════════════════════════════════════════════════════════════════════════════

def show_order_selection(records):
    selected = []
    root = tk.Tk(); root.title("ELTA 5.3 — Order Selection")
    root.attributes('-topmost', True); root.geometry("1150x580"); root.resizable(True, True)

    tk.Label(root, text="Select orders and choose carrier (click Carrier cell to toggle ELTA ↔ FedEx):",
             font=('Arial', 11, 'bold'), pady=8).pack()

    tf = tk.Frame(root); tf.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)
    cols = ('#', 'Name', 'Country', 'City', 'Street', 'ZIP', 'Carrier')
    tree = ttk.Treeview(tf, columns=cols, show='headings', selectmode='none')

    tree.column('#',       width=30,  anchor='center', stretch=False)
    tree.column('Name',    width=200, anchor='w')
    tree.column('Country', width=120, anchor='w')
    tree.column('City',    width=120, anchor='w')
    tree.column('Street',  width=220, anchor='w')
    tree.column('ZIP',     width=70,  anchor='w')
    tree.column('Carrier', width=80,  anchor='center', stretch=False)
    for c in cols: tree.heading(c, text=c)

    sb = ttk.Scrollbar(tf, orient='vertical', command=tree.yview)
    tree.configure(yscrollcommand=sb.set); sb.pack(side=tk.RIGHT, fill=tk.Y)
    tree.pack(fill=tk.BOTH, expand=True)

    tree.tag_configure('checked_elta',  background='#d4edda')
    tree.tag_configure('checked_fedex', background='#d0e8ff')
    tree.tag_configure('unchecked',     background='#f8f9fa')

    checked  = {}
    carriers = {}   # iid → 'ELTA' | 'FedEx'

    def row_tag(iid):
        if not checked.get(iid): return 'unchecked'
        return 'checked_fedex' if carriers[iid] == 'FedEx' else 'checked_elta'

    def refresh(iid):
        tree.item(iid, tags=(row_tag(iid),))
        vals = list(tree.item(iid,'values'))
        vals[0] = '✓' if checked[iid] else '☐'
        vals[6] = carriers[iid]
        tree.item(iid, values=vals)

    def on_click(event):
        iid    = tree.identify_row(event.y)
        col    = tree.identify_column(event.x)
        if not iid: return
        if col == '#7':   # Carrier column
            carriers[iid] = 'FedEx' if carriers[iid] == 'ELTA' else 'ELTA'
        else:
            checked[iid] = not checked[iid]
        refresh(iid); update_count()

    tree.bind('<Button-1>', on_click)
    count_var = tk.StringVar()

    def update_count():
        n = sum(1 for v in checked.values() if v)
        f = sum(1 for iid,v in checked.items() if v and carriers[iid]=='FedEx')
        count_var.set(f"{n} selected  ({n-f} ELTA, {f} FedEx)")

    for i, r in enumerate(records):
        name    = f"{r.get('first_name','')} {r.get('last_name','')}".strip()
        country = r.get('ship_country', '')
        street  = f"{r.get('street_1','')} {r.get('street_number','')}".strip()
        iid     = str(i)
        is_usa  = country in USA_COUNTRY_VALUES
        checked[iid]  = not is_usa
        carriers[iid] = 'FedEx' if is_usa else 'ELTA'
        tree.insert('', 'end', iid=iid, values=(
            '✓' if checked[iid] else '☐',
            name, country, r.get('ship_city',''), street,
            r.get('ship_zipcode',''), carriers[iid],
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
                r['carrier'] = carriers[iid]
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

def ask_sku(catalog, etsy_title="", current_sku=""):
    """
    Show a dialog to assign a SKU to an order.
    Returns (sku, entry) — entry is the catalog dict for that SKU.
    """
    result = [None, None]

    root = tk.Tk(); root.title("Assign Product / SKU")
    root.attributes('-topmost', True); root.geometry("600x520"); root.resizable(True, True)

    tk.Label(root, text="Assign a product SKU to this order",
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
    tree = ttk.Treeview(lf, columns=cols, show='headings', height=10)
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
            if sku == current_sku:
                tree.selection_set(sku)

    populate()
    search_var.trace_add('write', lambda *_: populate(search_var.get()))

    # New product form
    nf = ttk.LabelFrame(root, text="  Create new product  ", padding=8)
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

    # Buttons
    bf = tk.Frame(root); bf.pack(fill=tk.X, padx=10, pady=8)

    def select_existing():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("No selection","Please select a product from the list.")
            return
        sku = sel[0]
        entry = catalog["skus"][sku]
        # Link the etsy_title to this SKU if not already mapped
        if etsy_title:
            link_title_to_sku(catalog, sku, etsy_title)
        result[0] = sku; result[1] = entry; root.destroy()

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
        result[0] = sku; result[1] = entry; root.destroy()

    def skip():
        root.destroy()

    tk.Button(bf, text="✓ Use Selected",  command=select_existing,
              bg='#27ae60',fg='white',font=('Arial',10,'bold'),relief='flat',padx=12,pady=5).pack(side=tk.LEFT,padx=4)
    tk.Button(bf, text="+ Create New",    command=create_new,
              bg='#2980b9',fg='white',font=('Arial',10,'bold'),relief='flat',padx=12,pady=5).pack(side=tk.LEFT,padx=4)
    tk.Button(bf, text="Skip",            command=skip,
              bg='#95a5a6',fg='white',font=('Arial',10,'bold'),relief='flat',padx=12,pady=5).pack(side=tk.RIGHT,padx=4)

    root.grab_set(); root.mainloop()
    return result[0], result[1]


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
        self.key     = key
        self.data    = dict(data)
        self.on_save = on_save
        self.win.title(f"Edit — {data.get('full_name', key)}")
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
        if self.key not in db:
            self.win.destroy(); return
        for field, e in self.entries.items():
            db[self.key][field] = e.get().strip()
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
        self.sku     = sku
        self.data    = dict(data)
        self.on_save = on_save
        self.win.title(f"Edit Product — {sku}")
        self.win.geometry("500x430")
        self.win.attributes('-topmost', True)
        self._build()
        self.win.grab_set()

    def _build(self):
        ff = ttk.LabelFrame(self.win, text=f"  {self.sku}  ", padding="10")
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
                 records=None, historical=False):
        self.root            = root
        self.filepath        = filepath
        self.include_usa     = include_usa
        self.mode            = mode
        self.pre_loaded      = records
        self.historical      = historical
        self.catalog         = load_catalog()
        self.shipping_data   = []
        self.current_index   = 0

        self.root.title("ELTA 5.3 — Review & Edit")
        self.root.geometry("1020x800")

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

        # Carrier toggle button (click to switch ELTA ↔ FedEx)
        ttk.Label(self.data_frame, text="Carrier:").grid(
            row=row, column=0, sticky=tk.W, padx=5, pady=2)
        self.carrier_btn = tk.Button(self.data_frame, text="ELTA",
                                     font=('Arial', 10, 'bold'), fg='white',
                                     bg='#2980b9', relief='flat', padx=10, pady=2,
                                     cursor='hand2', command=self._toggle_carrier)
        self.carrier_btn.grid(row=row, column=1, sticky=tk.W, padx=5); row += 1

        self.print_label_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.data_frame, text="Print Label?",
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
        rec         = self.shipping_data[self.current_index] if self.shipping_data else {}
        etsy_title  = rec.get('etsy_title', '')
        current_sku = rec.get('sku', '')
        sku, entry  = ask_sku(self.catalog, etsy_title, current_sku)
        if sku and entry:
            self._current_sku   = sku
            self._current_entry = entry
            self.sku_label.config(text=f"{sku}  —  {entry.get('name','')}", fg='#27ae60')
            # Auto-fill dims/weight/value from catalog
            mapping = {
                'weight_kg': entry.get('weight_kg',''),
                'length_cm': entry.get('length_cm',''),
                'width_cm':  entry.get('width_cm',''),
                'height_cm': entry.get('height_cm',''),
                'value_eur': entry.get('value_eur',''),
            }
            for k, v in mapping.items():
                if v and k in self.entries:
                    self.entries[k].delete(0, tk.END)
                    self.entries[k].insert(0, str(v))
            # Write back to record
            if self.shipping_data:
                self.shipping_data[self.current_index]['sku']          = sku
                self.shipping_data[self.current_index]['product_name'] = entry.get('name','')

    def _toggle_carrier(self):
        if not self.shipping_data:
            return
        rec     = self.shipping_data[self.current_index]
        carrier = 'FedEx' if rec.get('carrier', 'ELTA') == 'ELTA' else 'ELTA'
        rec['carrier'] = carrier
        self.carrier_btn.config(
            text=carrier,
            bg='#2980b9' if carrier == 'ELTA' else '#e67e22')

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
                    sku, entry = auto_resolve_sku(self.catalog, r['etsy_title'])
                    if sku and entry:
                        r['sku']          = sku
                        r['product_name'] = entry.get('name', '')
                        for k in ('weight_kg','length_cm','width_cm','height_cm','value_eur'):
                            if entry.get(k) and not r.get(k):
                                r[k] = entry[k]

            # Returning customer check with full address comparison dialog
            db = load_customer_db()
            for record in self.shipping_data:
                key = customer_db_key(record)
                if key and key in db:
                    stored = db[key]
                    action, save_to_db = show_customer_update_dialog(record, stored)
                    if action == 'keep':
                        for field in ('street_1','street_number','street_2',
                                      'ship_city','ship_state','ship_zipcode','ship_country'):
                            if stored.get(field) is not None:
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
        carrier = rec.get('carrier', 'ELTA')
        self.carrier_btn.config(
            text=carrier,
            bg='#2980b9' if carrier == 'ELTA' else '#e67e22')
        self._update_history_panel(rec)
        sku   = rec.get('sku', '')
        pname = rec.get('product_name', '')
        self._current_sku   = sku
        self._current_entry = self.catalog["skus"].get(sku) if sku else None
        if sku:
            self.sku_label.config(text=f"{sku}  —  {pname}", fg='#27ae60')
        else:
            self.sku_label.config(text="— not assigned —", fg='#c0392b')
        self.current_index = index

    def save_changes(self):
        if not (0 <= self.current_index < len(self.shipping_data)):
            return
        rec = self.shipping_data[self.current_index]
        for field in self.entries:
            rec[field] = self.entries[field].get()
        rec["print_label"]   = self.print_label_var.get()
        rec["sku"]           = self._current_sku
        rec["product_name"]  = (self._current_entry or {}).get('name', '')
        # Auto-save dims/weight/value to catalog whenever they are filled
        if self._current_sku:
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
                                carrier=r.get('carrier','ELTA'),
                                order_date=r.get('order_date',''),
                                historical=True)
                if r.get('sku'):
                    bump_sku_shipment(self.catalog, r['sku'])
            messagebox.showinfo("Done",
                f"✓ {len(to_process)} records saved to customer DB.\nNo labels generated.")
            self.root.destroy()
            return

        # Live mode — split by carrier
        elta_records  = [r for r in to_process if r.get('carrier','ELTA') == 'ELTA']
        fedex_records = [r for r in to_process if r.get('carrier','ELTA') == 'FedEx']
        self.root.destroy()
        process_live(elta_records, fedex_records, self.mode, self.catalog)


# ═══════════════════════════════════════════════════════════════════════════════
# LIVE PROCESSING DISPATCHER
# ═══════════════════════════════════════════════════════════════════════════════

def process_live(elta_records, fedex_records, mode, catalog):
    # FedEx CSV first (no browser needed)
    if fedex_records:
        ts       = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_path = os.path.join(OUTPUT_DIR, f"fedex_batch_{ts}.csv")
        export_fedex_csv(fedex_records, csv_path)
        for r in fedex_records:
            upsert_customer(r, sku=r.get('sku',''), carrier='FedEx')
            if r.get('sku'):
                bump_sku_shipment(catalog, r['sku'])
        messagebox.showinfo("FedEx CSV Ready",
            f"✓ {len(fedex_records)} FedEx order(s) exported to:\n{csv_path}")

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
                if catalog and r.get('sku'):
                    bump_sku_shipment(catalog, r['sku'])
            except Exception as e:
                print(f"⚠ Letter error: {e}")
        return

    if elta_records:
        process_elta_labels(elta_records, generate_letters=(mode=='both'),
                            catalog=catalog)


# ═══════════════════════════════════════════════════════════════════════════════
# FEDEX CSV EXPORT
# ═══════════════════════════════════════════════════════════════════════════════

FEDEX_COLUMNS = [
    'serviceType','shipmentType','senderContactName','senderContactNumber',
    'senderLine1','senderPostcode','senderCity','senderCountry','senderEmail',
    'recipientContactName','recipientContactNumber','recipientLine1','recipientLine2',
    'recipientPostcode','recipientCity','recipientState','recipientCountry',
    'recipientEmail','recipientResidential','numberOfPackages','packageWeight',
    'weightUnits','length','width','height','etdEnabled','baseRate','packageType',
    'currencyType','commodityType','itemDescription','manufacturingCountry',
    'commodityQuantity','commodityMeasureUnit','commodityWeight','customsValue',
    'purposeOfShipment','generateInvoice',
]

def export_fedex_csv(records, filepath):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=FEDEX_COLUMNS)
        writer.writeheader()
        for r in records:
            country_name = r.get('ship_country','')
            iso2         = COUNTRY_TO_ISO2.get(country_name, country_name[:2].upper())
            weight_str   = str(r.get('weight_kg','1.2')).replace(',','.')
            try:    net_weight = str(round(float(weight_str)*0.8, 2))
            except: net_weight = '0.4'
            item_desc = (FEDEX_ITEM_PREFIX +
                         (r.get('product_name') or r.get('etsy_title') or 'Wig'))
            street1 = f"{r.get('street_1','')} {r.get('street_number','')}".strip()
            writer.writerow({
                'serviceType':          'INTERNATIONAL_ECONOMY',
                'shipmentType':         'OUTBOUND',
                'senderContactName':    SENDER['name'],
                'senderContactNumber':  SENDER['phone'],
                'senderLine1':          SENDER['line1'],
                'senderPostcode':       SENDER['postcode'],
                'senderCity':           SENDER['city'],
                'senderCountry':        SENDER['country'],
                'senderEmail':          SENDER['email'],
                'recipientContactName': r.get('full_name',''),
                'recipientContactNumber': re.sub(r'\s+','', r.get('phone','')),
                'recipientLine1':       street1,
                'recipientLine2':       r.get('street_2',''),
                'recipientPostcode':    r.get('ship_zipcode',''),
                'recipientCity':        r.get('ship_city',''),
                'recipientState':       r.get('ship_state',''),
                'recipientCountry':     iso2,
                'recipientEmail':       r.get('email',''),
                'recipientResidential': 'Y',
                'numberOfPackages':     '1',
                'packageWeight':        weight_str,
                'weightUnits':          'KGS',
                'length':               r.get('length_cm',''),
                'width':                r.get('width_cm',''),
                'height':               r.get('height_cm',''),
                'etdEnabled':           'Y',
                'baseRate':             '',
                'packageType':          'YOUR_PACKAGING',
                'currencyType':         'EUR',
                'commodityType':        'ITEMS',
                'itemDescription':      item_desc,
                'manufacturingCountry': 'GR',
                'commodityQuantity':    r.get('customs_qty','1'),
                'commodityMeasureUnit': 'PCS',
                'commodityWeight':      net_weight,
                'customsValue':         str(r.get('value_eur','')).replace(',','.'),
                'purposeOfShipment':    'SOLD',
                'generateInvoice':      'CI',
            })
    print(f"✓ FedEx CSV saved: {filepath}")


# ═══════════════════════════════════════════════════════════════════════════════
# THANK-YOU LETTERS
# ═══════════════════════════════════════════════════════════════════════════════

def guess_gender(first_name, country=None):
    try:
        params = {"name": first_name.split()[0]}
        iso = COUNTRY_ISO.get(country,'')
        if iso: params["country_id"] = iso
        resp = requests.get("https://api.genderize.io", params=params, timeout=5)
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

def fill_by_id(driver, field_id, value):
    value = strip_accents(str(value))
    try:
        el = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, field_id)))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        human_delay(0.2, 0.4); el.clear(); human_delay(0.1, 0.3)
        for char in value: el.send_keys(char); human_delay(0.04, 0.1)
        print(f"✓ Filled {field_id}: {value}"); return True
    except Exception as e:
        print(f"⚠ Could not fill {field_id}: {e}"); return False

def fill_visible_field(driver, field_label, value):
    if not value: return False
    value = strip_accents(str(value))
    try:
        candidates = driver.find_elements(By.XPATH,
            f"//label[contains(normalize-space(),'{field_label}')]"
            f"/following::input[self::input[@type='text' or @type='email' or @type='number' or not(@type)]][1]")
        visible = [el for el in candidates if el.is_displayed() and el.is_enabled()]
        if not visible: return False
        el = visible[0]
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        human_delay(0.1, 0.3); el.clear(); human_delay(0.1, 0.2)
        for char in value: el.send_keys(char); human_delay(0.04, 0.1)
        print(f"✓ Filled (visible) '{field_label}': {value}"); return True
    except Exception as e:
        print(f"⚠ fill_visible_field '{field_label}': {e}"); return False

def find_and_click_next_button(driver, step=None, quiet=False):
    # Try data-step="1" first (current ELTA site), fall back to :not([data-step])
    selectors = ([f'button.btn-next[data-step="{step}"]', 'button.btn-next:not([data-step])']
                 if (step is None or step == 1)
                 else [f'button.btn-next[data-step="{step}"]'])
    human_delay(0.4, 0.8)
    for sel in selectors:
        try:
            btn = WebDriverWait(driver, 6).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, sel)))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
            human_delay(0.2, 0.4)
            driver.execute_script("arguments[0].click();", btn)
            print(f"✓ Clicked btn-next (step={step or 1})"); return True
        except Exception:
            continue
    print(f"⚠ btn-next step={step or 1}: not found")
    if not quiet: wait_for_user("Please click Επόμενο manually, then click Done.")
    return False

def select_country_and_service(driver, country="United States"):
    country = COUNTRY_NAME_MAP.get(country, country)
    try:
        cd = WebDriverWait(driver,10).until(
            EC.element_to_be_clickable((By.XPATH,"//span[contains(@class,'select2-selection')]")))
        cd.click(); human_delay(0.5,1)
        si = WebDriverWait(driver,5).until(
            EC.presence_of_element_located((By.XPATH,"//input[contains(@class,'select2-search__field')]")))
        for char in country: si.send_keys(char); human_delay(0.05,0.1)
        human_delay(0.5,1)
        try:
            exact = WebDriverWait(driver,5).until(EC.element_to_be_clickable((By.XPATH,
                f"//li[contains(@class,'select2-results__option') and normalize-space(text())='{country}']")))
            exact.click()
        except Exception:
            si.send_keys(Keys.ENTER)
        WebDriverWait(driver,10).until(
            EC.invisibility_of_element_located((By.XPATH,"//span[@class='select2-dropdown']")))
        human_delay(2,3)
    except Exception as e:
        print(f"Country selection failed: {e}")
        wait_for_user(f"Please select '{country}' manually, then click Done.")
        human_delay(2,3)
    try:
        sel_el = WebDriverWait(driver,10).until(EC.presence_of_element_located((By.XPATH,
            "//select[contains(@id,'Service') or contains(@name,'Service')]")))
        opt = next((o for o in sel_el.find_elements(By.TAG_NAME,'option') if '854' in o.text), None)
        if opt:
            driver.execute_script(
                "arguments[0].value=arguments[1];arguments[0].dispatchEvent(new Event('change'));",
                sel_el, opt.get_attribute('value'))
            human_delay(1,2); print(f"✓ Service: {opt.text}")
        else:
            raise Exception("No 854 option found")
    except Exception as e:
        print(f"Service selection failed: {e}")
        wait_for_user("Please select '854 LL' manually, then click Done.")

def fill_receiver_form(driver, receiver_data, weight_data, dimensions_data):
    id_map = {
        "Όνομα":"RecipientFirstName","Επώνυμο":"RecipientLastName",
        "Όνομα Οδού":"RecipientStreetName","Αρ. Οδού":"RecipientStreetNumber",
        "Ταχ. Κώδικας":"RecipientPostalCode","Πόλη":"RecipientTown",
        "E-Mail":"RecipientEmail","Οργανισμός":"RecipientOrganization",
        "Σημείο παραλαβής":"RecipientDeliveryPoint",
    }
    for label, fid in id_map.items():
        value = receiver_data.get(label,"")
        if not value: continue
        if not fill_by_id(driver, fid, value):
            fill_visible_field(driver, label, value)
        human_delay(0.2,0.4)
    fill_by_id(driver,"VoucherDetailWeight", weight_data.get("Βάρος (Kg)","0,49"))
    fill_by_id(driver,"VoucherDetailLength", dimensions_data.get("length","21"))
    fill_by_id(driver,"VoucherDetailWidth",  dimensions_data.get("width","28"))
    fill_by_id(driver,"VoucherDetailHeight", dimensions_data.get("height","12"))
    try:
        cb = driver.find_element(By.ID,"VoucherDetailGift")
        if not cb.is_selected():
            driver.execute_script("arguments[0].click();",cb)
        print("✓ Gift checkbox ticked")
    except Exception as e:
        print(f"⚠ Gift checkbox: {e}")

def fill_content_description(driver, country=''):
    if country in EU_COUNTRIES: return
    try:
        driver.execute_script("""
            var el=document.getElementById('VoucherDetailExplanation');
            if(el){el.removeAttribute('disabled');el.removeAttribute('readonly');
                   el.value='festive items';el.dispatchEvent(new Event('input'));
                   el.dispatchEvent(new Event('change'));}
        """)
        driver.execute_script("""
            var el=document.getElementById('ProtectedVoucherDetailQuantity');
            if(el){el.removeAttribute('disabled');el.removeAttribute('readonly');
                   el.value='1';el.dispatchEvent(new Event('input'));
                   el.dispatchEvent(new Event('change'));}
        """)
    except Exception as e:
        print(f"Content description: {e}")
        wait_for_user("Please fill content description manually, then click Done.")

def fill_customs_declaration(driver, record):
    try:
        WebDriverWait(driver,15).until(
            EC.visibility_of_element_located((By.ID,"CustomsDeclarationDetailedDescriptionOfContents1")))
        qty       = record.get('customs_qty','2')
        total_kg  = float(str(record.get('weight_kg','0,49')).replace(',','.'))
        net_weight= str(round(total_kg*0.8,2)).replace('.',',')
        fill_by_id(driver,"CustomsDeclarationDetailedDescriptionOfContents1","Carnival Wigs")
        fill_by_id(driver,"CustomsDeclarationQuantity1",                      qty)
        fill_by_id(driver,"CustomsDeclarationNetWeight1",                      net_weight)
        fill_by_id(driver,"CustomsDeclarationValue1",                          "15")
        fill_by_id(driver,"CustomsDeclarationHSTarifNumber1",                  "9505900014")
        fill_by_id(driver,"CustomsDeclarationCounryOfOrigionOfGoods1",         "GR")
    except Exception as e:
        print(f"Customs error: {e}")
        wait_for_user("Please fill customs declaration manually, then click Done.")

def rename_latest_pdf(last_name, first_name):
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        date_str = datetime.date.today().strftime("%d_%m_%y")
        new_name = f"{last_name.upper()}_{first_name.upper()}_{date_str}.pdf"
        new_path = os.path.join(OUTPUT_DIR, new_name)
        dl = "D:\\Downloads"
        for search_dir in [dl, OUTPUT_DIR]:
            if not os.path.isdir(search_dir):
                continue
            pdfs = [os.path.join(search_dir, f) for f in os.listdir(search_dir)
                    if f.lower().endswith('.pdf') and f != new_name]
            if not pdfs:
                continue
            latest = max(pdfs, key=os.path.getmtime)
            for _ in range(20):
                size1 = os.path.getsize(latest); time.sleep(1)
                if os.path.getsize(latest) == size1: break
            if os.path.exists(new_path): os.remove(new_path)
            import shutil; shutil.move(latest, new_path)
            print(f"✓ PDF saved: {new_name}"); return new_name
        print("⚠ No PDF found in ELTA_NEW_PROGRAM or Downloads"); return None
    except Exception as e:
        print(f"⚠ rename PDF: {e}"); return None

def print_shipping_label(driver, record):
    first_name = record.get('first_name','UNKNOWN')
    last_name  = record.get('last_name','UNKNOWN')
    tracking   = None
    try:
        btn = WebDriverWait(driver,15).until(
            EC.element_to_be_clickable((By.ID,"printVoucher")))
        human_delay(0.5,1.5)
        driver.execute_script("arguments[0].click();",btn)
        print("✓ Print button clicked")
        human_delay(4,6)
        m = re.search(r'[A-Z]{2}\d{9}[A-Z]{2}', driver.page_source)
        if m: tracking = m.group(0); print(f"✓ Tracking: {tracking}")
        rename_latest_pdf(last_name, first_name)
        human_delay(1,2)
    except Exception as e:
        print(f"Print error: {e}")
        wait_for_user(f"Click Εκτύπωση manually for {first_name} {last_name}, then Done.")
    return tracking

def process_all_records(shipping_records, driver, generate_letters=True, catalog=None):
    for index, record in enumerate(shipping_records):
        print(f"\n--- Record {index+1}/{len(shipping_records)}: "
              f"{record.get('first_name','')} {record.get('last_name','')} ---")
        if index > 0:
            try:
                btn = WebDriverWait(driver,10).until(EC.element_to_be_clickable((By.XPATH,
                    "//a[contains(text(),'Νέα αποστολή') or contains(text(),'Δημιουργ')]"
                    "|//button[contains(text(),'Νέα αποστολή') or contains(text(),'Δημιουργ')]")))
                human_delay(0.5,1.5); btn.click()
                WebDriverWait(driver,15).until(lambda d: len(d.find_elements(
                    By.XPATH,"//div[contains(@class,'load')]"))==0)
                select_country_and_service(driver, record.get('ship_country','United States'))
                find_and_click_next_button(driver, step=1, quiet=True)
                WebDriverWait(driver,10).until(
                    EC.visibility_of_element_located((By.ID,"SenderFirstName")))
                find_and_click_next_button(driver, step=2)
                WebDriverWait(driver,10).until(
                    EC.visibility_of_element_located((By.ID,"RecipientFirstName")))
            except Exception as e:
                print(f"New shipment error: {e}")
                wait_for_user("Navigate to new shipment receiver form manually, then Done.")

        try:
            receiver_data = {
                "Όνομα":           record.get("first_name",""),
                "Επώνυμο":         record.get("last_name",""),
                "Όνομα Οδού":      record.get("street_1",""),
                "Αρ. Οδού":        record.get("street_number",""),
                "Ταχ. Κώδικας":    record.get("ship_zipcode",""),
                "Πόλη":            record.get("ship_city",""),
                "E-Mail":          record.get("email",""),
                "Οργανισμός":      record.get("street_2",""),
                "Σημείο παραλαβής":record.get("street_2",""),
            }
            weight_data = {"Βάρος (Kg)": record.get("weight_kg","0,49")}
            dims_data   = {"length": record.get("length_cm","21"),
                           "width":  record.get("width_cm","28"),
                           "height": record.get("height_cm","12")}

            fill_receiver_form(driver, receiver_data, weight_data, dims_data)
            fill_content_description(driver, country=record.get('ship_country',''))
            find_and_click_next_button(driver, step=3)
            human_delay(1,2)
            if record.get('ship_country','') not in EU_COUNTRIES:
                fill_customs_declaration(driver, record)
                find_and_click_next_button(driver, step=4)
                human_delay(1,2)
            tracking = print_shipping_label(driver, record)

            # Check returning customer BEFORE upserting
            _db_pre      = load_customer_db()
            _key         = customer_db_key(record)
            is_returning = (_key and _key in _db_pre and
                            _db_pre[_key].get("total_orders", 0) > 0)

            # Save to customer DB
            upsert_customer(record, sku=record.get('sku',''),
                            carrier='ELTA', tracking=tracking)
            if catalog and record.get('sku'):
                bump_sku_shipment(catalog, record['sku'])

            if generate_letters:
                try:
                    generate_thank_you(record)
                    if is_returning:
                        generate_thank_you_return(record)
                except Exception as e: print(f"⚠ Letter error: {e}")

        except Exception as e:
            print(f"❌ Record {index+1} error: {e}")
            safe_screenshot(driver, f"record_{index+1}_error.png")
            wait_for_user(f"Error on {record.get('full_name','?')}: {e}\n\nFix manually then Done.")

        human_delay(2,3)

def process_elta_labels(shipping_records, sender_email="math4econ@gmail.com",
                        generate_letters=True, catalog=None):
    if not shipping_records: return
    import platform
    options = webdriver.FirefoxOptions()
    if platform.system()=="Linux":
        options.binary_location="/snap/firefox/current/usr/lib/firefox/firefox"
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.download.dir", OUTPUT_DIR)
    options.set_preference("browser.download.useDownloadDir", True)
    options.set_preference("browser.helperApps.neverAsk.saveToDisk",
                           "application/pdf,application/octet-stream")
    options.set_preference("pdfjs.disabled", True)
    options.set_preference("browser.download.manager.showWhenStarting", False)
    driver = webdriver.Firefox(options=options)
    try:
        driver.get("https://weblabeling.elta.gr/el-GR/Account/NCLogin")
        WebDriverWait(driver,10).until(lambda d: "NCLogin" in d.current_url)
        email_field = WebDriverWait(driver,10).until(
            EC.presence_of_element_located((By.ID,"Email")))
        human_delay(0.5,1.5); email_field.clear()
        for char in sender_email: email_field.send_keys(char); human_delay(0.05,0.15)
        print("⚠ Solve CAPTCHA in browser then proceed.")
        try:
            WebDriverWait(driver,180).until(lambda d: "NCLogin" not in d.current_url)
        except Exception:
            wait_for_user("Solve CAPTCHA, click Next in browser, then Done here.")

        select_country_and_service(driver,
            shipping_records[0].get('ship_country','United States'))
        find_and_click_next_button(driver, step=1)
        WebDriverWait(driver,15).until(
            EC.visibility_of_element_located((By.ID,"SenderFirstName")))

        # Fill sender (fixed data)
        sender_map = {
            "Όνομα":"KOSTAS","Επώνυμο":"PAPANAYITOU",
            "Όνομα Οδού":"ANAXIMENOUS","Αρ. Οδού":"18",
            "Ταχ. Κώδικας":"11631","Πόλη":"ATHENS",
        }
        for label,value in sender_map.items():
            fill_visible_field(driver,label,value); human_delay(0.2,0.5)

        find_and_click_next_button(driver, step=2)
        WebDriverWait(driver,15).until(
            EC.visibility_of_element_located((By.ID,"RecipientFirstName")))

        process_all_records(shipping_records, driver,
                            generate_letters=generate_letters, catalog=catalog)
    except Exception as e:
        print(f"ELTA error: {e}"); safe_screenshot(driver,"elta_error.png")
    finally:
        driver.quit(); print("Browser closed.")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("ELTA Weblabeling & CRM — v5.3")
    try:
        filepath    = ask_for_orders_file()
        all_records = load_orders_from_html(filepath)
        if not all_records:
            raise SystemExit("No orders found in file.")

        run_mode = ask_run_mode()   # 'live' or 'historical'

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
            mode = ask_mode()
            if mode == 'letters':
                for r in selected:
                    try: generate_thank_you(r)
                    except Exception as e: print(f"⚠ {e}")
                print("Done. Letters saved to", OUTPUT_DIR)
            else:
                root = tk.Tk()
                app  = EltaShippingApp(root, filepath=filepath, mode=mode,
                                       records=selected, historical=False)
                root.after(50, app.load_orders)
                root.mainloop()

    except SystemExit as e:
        print(str(e))
    except Exception as e:
        import traceback; traceback.print_exc()
