from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import time
import random
import json
import os
import re
import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
from odf.opendocument import OpenDocumentText
from odf.style import Style, TextProperties, ParagraphProperties
from odf.text import P, Span

def human_delay(min_sec=1, max_sec=3):
    """Random delay to mimic human behavior"""
    time.sleep(random.uniform(min_sec, max_sec))

def safe_screenshot(driver, filename):
    """Take a screenshot, silently skip if the browser session is dead."""
    try:
        driver.save_screenshot(filename)
        print(f"Screenshot saved: {filename}")
    except Exception:
        pass

# EU member states (no customs form required)
EU_COUNTRIES = {
    "Austria", "Belgium", "Bulgaria", "Croatia", "Cyprus", "Czech Republic",
    "Denmark", "Estonia", "Finland", "France", "Germany", "Greece",
    "Hungary", "Ireland", "Italy", "Latvia", "Lithuania", "Luxembourg",
    "Malta", "Netherlands", "Poland", "Portugal", "Romania", "Slovakia",
    "Slovenia", "Spain", "Sweden",
}

# Country name mapping: Etsy names → ELTA weblabeling dropdown names
COUNTRY_NAME_MAP = {
    "United Kingdom": "Great Britain",
    "Spain":          "ES Spain",
}

CUSTOMER_DB_PATH = os.path.expanduser("~/Documents/ELTA_NEW_PROGRAM/customer_db.json")

def load_customer_db():
    if os.path.exists(CUSTOMER_DB_PATH):
        with open(CUSTOMER_DB_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_customer_db(db):
    os.makedirs(os.path.dirname(CUSTOMER_DB_PATH), exist_ok=True)
    with open(CUSTOMER_DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

def customer_db_key(record):
    email = record.get('email', '').strip()
    if email:
        return email.lower()
    return record.get('full_name', '').strip().lower()


# ── Country → ISO-2 code (for genderize.io country_id hint) ─────────────────
COUNTRY_ISO = {
    "France": "FR", "Germany": "DE", "Spain": "ES", "Italy": "IT",
    "United Kingdom": "GB", "Great Britain": "GB", "Netherlands": "NL",
    "Belgium": "BE", "Switzerland": "CH", "Austria": "AT", "Sweden": "SE",
    "Norway": "NO", "Denmark": "DK", "Finland": "FI", "Poland": "PL",
    "Portugal": "PT", "Greece": "GR", "Australia": "AU", "Canada": "CA",
    "United States": "US", "Mexico": "MX", "Brazil": "BR", "Argentina": "AR",
}

# Countries that get Spanish letter
SPANISH_COUNTRIES = {
    "Spain", "Mexico", "Argentina", "Colombia", "Chile", "Peru", "Venezuela",
    "Ecuador", "Bolivia", "Paraguay", "Uruguay", "Costa Rica", "Guatemala",
    "Honduras", "El Salvador", "Nicaragua", "Panama", "Cuba", "Dominican Republic",
}

GENDER_CONFIDENCE_THRESHOLD = 0.85


def guess_gender(first_name, country=None):
    """Call genderize.io. Returns 'M', 'F', or None (ask user)."""
    try:
        params = {"name": first_name.split()[0]}  # use only the first given name
        iso = COUNTRY_ISO.get(country, '')
        if iso:
            params["country_id"] = iso
        resp = requests.get("https://api.genderize.io", params=params, timeout=5)
        data = resp.json()
        gender     = data.get("gender")        # "male", "female", or None
        probability = data.get("probability", 0)
        if gender and probability >= GENDER_CONFIDENCE_THRESHOLD:
            return 'M' if gender == "male" else 'F'
    except Exception as e:
        print(f"⚠ genderize.io error: {e}")
    return None  # ask user


def ask_gender(full_name):
    """Always-on-top dialog: ask Mr. or Ms. Returns 'M' or 'F'."""
    result = ['M']
    root = tk.Tk()
    root.title("Gender?")
    root.attributes('-topmost', True)
    root.resizable(False, False)

    tk.Label(root, text=f"Cannot determine gender for:\n{full_name}\n\nSelect salutation:",
             wraplength=320, justify='center', pady=12, padx=16,
             font=('Arial', 11)).pack()

    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=(4, 14))

    def on_mr():
        result[0] = 'M'
        root.destroy()

    def on_ms():
        result[0] = 'F'
        root.destroy()

    tk.Button(btn_frame, text="Mr.", command=on_mr,
              bg='#2980b9', fg='white', font=('Arial', 11, 'bold'),
              relief='flat', padx=20, pady=6, cursor='hand2').pack(side=tk.LEFT, padx=8)
    tk.Button(btn_frame, text="Ms.", command=on_ms,
              bg='#8e44ad', fg='white', font=('Arial', 11, 'bold'),
              relief='flat', padx=20, pady=6, cursor='hand2').pack(side=tk.LEFT, padx=8)

    root.update_idletasks()
    sw = root.winfo_screenwidth(); sh = root.winfo_screenheight()
    w = root.winfo_reqwidth();     h = root.winfo_reqheight()
    root.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")
    root.grab_set()
    root.mainloop()
    return result[0]


def generate_thank_you(record):
    """Generate a thank-you ODT letter and save it to OUTPUT_DIR."""
    first_name = record.get('first_name', '')
    last_name  = record.get('last_name', '')
    country    = record.get('ship_country', '')

    # Determine gender
    gender = guess_gender(first_name, country)
    if gender is None:
        gender = ask_gender(f"{first_name} {last_name}")

    # Choose language and salutation
    if country == "France":
        if gender == 'M':
            salutation = f"Cher M. {last_name},"
        else:
            salutation = f"Chère Mme. {last_name},"
        body = (
            "Nous tenions à exprimer notre profonde gratitude et nos sincères remerciements "
            "d'avoir choisi notre petite manufacture comme votre destination préférée pour "
            "l'achat de votre nouvelle perruque. Cela signifie beaucoup pour nous que vous "
            "nous ayez confié cette décision importante.\n\n"
            "Nous attendons avec impatience vos précieux commentaires et espérons sincèrement "
            "que la perruque que vous avez choisie surpassera vos attentes, vous apportant une "
            "satisfaction et une joie maximales. Cependant, nous comprenons que la perfection "
            "est subjective, et dans le rare cas où un aspect ne correspondrait pas à votre "
            "vision, nous vous encourageons vivement à nous en informer sans aucune hésitation. "
            "Vos commentaires sont inestimables pour nous, car nous nous efforçons d'améliorer "
            "continuellement nos produits et nos services.\n\n"
            "Depuis la belle ville d'Athènes, en Grèce, nous vous adressons nos salutations "
            "les plus chaleureuses. C'est un honneur de vous servir, et nous espérons entretenir "
            "une relation durable avec vous.\n\nCordialement,\nConstantine"
        )
    elif country in SPANISH_COUNTRIES:
        if gender == 'M':
            salutation = f"Estimado Sr. {last_name},"
        else:
            salutation = f"Estimada Sra. {last_name},"
        body = (
            "¡Bienvenido a nuestra manufactura de pelucas! Estamos verdaderamente encantados "
            "de que nos haya elegido para su compra. Es un honor tener la oportunidad de "
            "contribuir a su visión creativa. Esperamos que su nueva peluca aporte el toque "
            "perfecto a su presentación o evento.\n\n"
            "Si desea compartir algo sobre su experiencia o hay algo que podamos hacer para "
            "mejorarla, no dude en comunicarse con nosotros. Su opinión significa mucho para "
            "nosotros. Muchas gracias nuevamente por confiar en nosotros. Esperamos con "
            "entusiasmo la posibilidad de volver a colaborar en el futuro.\n\n"
            "Cordialmente,\nConstantine"
        )
    else:
        if gender == 'M':
            salutation = f"Dear Mr. {last_name},"
        else:
            salutation = f"Dear Ms. {last_name},"
        body = (
            "Welcome to our wig manufactory! We're truly delighted that you've chosen us for "
            "your purchase. It's an honor to have the chance to contribute to your creative "
            "vision. We hope your new wig adds the perfect touch to your performance or event.\n\n"
            "If there's anything you'd like to share about your experience or if there's "
            "anything we can do to make it even better, please don't hesitate to reach out. "
            "Your feedback means a lot to us. Thank you once again for trusting us with your "
            "needs. We look forward to the possibility of working together again in the future.\n\n"
            "Warm regards,\nConstantine"
        )

    # Build ODT document
    doc = OpenDocumentText()

    # Paragraph style with font
    style = Style(name="LetterBody", family="paragraph")
    style.addElement(ParagraphProperties(marginbottom="0.25cm"))
    style.addElement(TextProperties(fontsize="12pt", fontfamily="Arial"))
    doc.styles.addElement(style)

    def add_paragraph(text, bold=False):
        p = P(stylename="LetterBody")
        if bold:
            span_style = Style(name="Bold", family="text")
            span_style.addElement(TextProperties(fontweight="bold"))
            doc.styles.addElement(span_style)
            p.addElement(Span(stylename="Bold", text=text))
        else:
            p.addText(text)
        doc.text.addElement(p)

    add_paragraph(salutation, bold=True)
    add_paragraph("")
    for para in body.split("\n\n"):
        for line in para.split("\n"):
            add_paragraph(line)
        add_paragraph("")

    # Save file
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    date_str  = datetime.date.today().strftime("%d_%m_%y")
    surname   = last_name.upper()
    name      = first_name.upper()
    filename  = f"{surname}_{name}_{date_str}_thankyou.odt"
    filepath  = os.path.join(OUTPUT_DIR, filename)
    doc.save(filepath)
    print(f"✓ Thank-you letter saved: {filename}")


def load_orders_from_html(filepath):
    """Parse Etsy orders HTML file and return list of order records."""
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()

    # Extract the Etsy.Context JSON blob
    start = html.find('Etsy.Context=')
    if start == -1:
        raise ValueError("Could not find Etsy.Context in the file. Is this the right orders page?")
    start = html.find('{', start)
    depth = 0; end = start
    for i, c in enumerate(html[start:], start):
        if c == '{': depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0: end = i + 1; break

    data = json.loads(html[start:end])
    search = data['data']['initial_data']['orders']['orders_search']
    orders = search['orders']
    buyers = {b['buyer_id']: b for b in search['buyers']}

    records = []
    for order in orders:
        if order.get('is_canceled'):
            continue

        addr  = order['fulfillment']['to_address']
        buyer = buyers.get(order['buyer_id'], {})

        # Split full name: last word → last_name, rest → first_name
        full_name = addr.get('name', '').strip()
        parts = full_name.rsplit(' ', 1)
        first_name = parts[0] if len(parts) == 2 else full_name
        last_name  = parts[1] if len(parts) == 2 else ''

        # Extract street number (digits) + any suffix (e.g. A, /35, -11, /11A).
        # Suffix goes as prefix before the street name per ELTA convention.
        street = addr.get('first_line', '').strip()
        # Leading number: "33A Baker St", "9/11 Baker St", "33 Baker St"
        lead   = re.match(r'^(\d+)([^\s\d][^\s]*)?\s+(.*)', street)
        # Trailing number + optional immediate suffix: "Baker St 33A", "Baker St 9/11", "Baker St 33"
        trail  = re.match(r'^(.*\S)\s+(\d+)([^\s\d][^\s]*)?$', street)
        # Trailing number + space-separated short suffix: "Am Silberberg 33 A", "Rue Voltaire 12 Bis"
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

        records.append({
            'order_id':     str(order['order_id']),
            'full_name':    full_name,
            'first_name':   first_name,
            'last_name':    last_name,
            'street_1':     street_name,
            'street_number': street_number,
            'street_2':     addr.get('second_line', ''),
            'ship_city':    addr.get('city', ''),
            'ship_state':   addr.get('state', ''),
            'ship_zipcode': addr.get('zip', ''),
            'ship_country': addr.get('country', ''),
            'email':        buyer.get('email', ''),
            'phone':        addr.get('phone', ''),
            'buyer':        buyer.get('username', ''),
            'print_label':  True,
            'weight_kg':    '0,49',
            'length_cm':    '21',
            'width_cm':     '28',
            'height_cm':    '12',
            'customs_qty':  '2',
        })

    print(f"✓ Loaded {len(records)} orders from {os.path.basename(filepath)}")
    return records


def ask_for_orders_file():
    """Show a file picker to select the orders HTML file. Returns the chosen path."""
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    default_path = os.path.expanduser('~/Documents/ELTA_NEW_PROGRAM/orders.txt')
    path = filedialog.askopenfilename(
        title='Select Etsy orders file',
        initialdir=os.path.expanduser('~/Documents/ELTA_NEW_PROGRAM'),
        initialfile='orders.txt',
        filetypes=[('HTML/Text files', '*.txt *.html *.htm'), ('All files', '*.*')]
    )
    root.destroy()
    if not path:
        # User cancelled — use default if it exists
        if os.path.exists(default_path):
            print(f"No file selected, using default: {default_path}")
            return default_path
        raise SystemExit("No orders file selected.")
    return path


def wait_for_user(message):
    """Show a visible always-on-top window asking user to act manually, then click Done to continue."""
    root = tk.Tk()
    root.title("⚠ Action Required")
    root.attributes('-topmost', True)
    root.lift()
    root.focus_force()

    root.resizable(False, False)
    root.update_idletasks()  # let Tk compute natural size
    w = root.winfo_reqwidth()
    h = root.winfo_reqheight()
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    root.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")

    tk.Label(root, text=message, wraplength=440, justify='left',
             pady=12, padx=16, font=('Arial', 11)).pack()

    tk.Button(root, text="✓ Done — Continue", command=root.destroy,
              bg='#27ae60', fg='white', font=('Arial', 11, 'bold'),
              relief='flat', padx=12, pady=6, cursor='hand2').pack(pady=(4, 14))

    # Keep window on top even if user clicks elsewhere
    root.grab_set()
    root.mainloop()

def ask_yes_no(question):
    """Show an always-on-top Yes/No dialog. Returns True for Yes, False for No."""
    result = [False]

    root = tk.Tk()
    root.title("Question")
    root.attributes('-topmost', True)
    root.lift()
    root.focus_force()
    root.resizable(False, False)

    tk.Label(root, text=question, wraplength=420, justify='left',
             pady=14, padx=16, font=('Arial', 11)).pack()

    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=(4, 14))

    def on_yes():
        result[0] = True
        root.destroy()

    def on_no():
        result[0] = False
        root.destroy()

    tk.Button(btn_frame, text="Yes", command=on_yes,
              bg='#27ae60', fg='white', font=('Arial', 11, 'bold'),
              relief='flat', padx=20, pady=6, cursor='hand2').pack(side=tk.LEFT, padx=8)
    tk.Button(btn_frame, text="No", command=on_no,
              bg='#e74c3c', fg='white', font=('Arial', 11, 'bold'),
              relief='flat', padx=20, pady=6, cursor='hand2').pack(side=tk.LEFT, padx=8)

    root.update_idletasks()
    w = root.winfo_reqwidth()
    h = root.winfo_reqheight()
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    root.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")

    root.grab_set()
    root.mainloop()
    return result[0]

def ask_mode():
    """Ask whether to do Labels+Letters, Labels only, or Letters only.
    Returns 'both', 'labels', or 'letters'."""
    result = ['both']

    root = tk.Tk()
    root.title("What to do?")
    root.attributes('-topmost', True)
    root.lift()
    root.focus_force()
    root.resizable(False, False)

    tk.Label(root, text="What would you like to run?", wraplength=380, justify='center',
             pady=14, padx=16, font=('Arial', 12, 'bold')).pack()

    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=(4, 16))

    def pick(val):
        result[0] = val
        root.destroy()

    tk.Button(btn_frame, text="Labels + Thank-you Letters", command=lambda: pick('both'),
              bg='#2980b9', fg='white', font=('Arial', 11, 'bold'),
              relief='flat', padx=14, pady=7, cursor='hand2').pack(fill='x', padx=12, pady=4)
    tk.Button(btn_frame, text="Labels Only", command=lambda: pick('labels'),
              bg='#27ae60', fg='white', font=('Arial', 11, 'bold'),
              relief='flat', padx=14, pady=7, cursor='hand2').pack(fill='x', padx=12, pady=4)
    tk.Button(btn_frame, text="Thank-you Letters Only", command=lambda: pick('letters'),
              bg='#8e44ad', fg='white', font=('Arial', 11, 'bold'),
              relief='flat', padx=14, pady=7, cursor='hand2').pack(fill='x', padx=12, pady=4)

    root.update_idletasks()
    w = root.winfo_reqwidth()
    h = root.winfo_reqheight()
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    root.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")

    root.grab_set()
    root.mainloop()
    return result[0]


# Countries that ship to the USA (for filtering)
USA_COUNTRY_VALUES = {"United States", "United States of America", "USA", "US"}


def show_order_selection(records):
    """Show a table of all orders with checkboxes. Returns the selected records."""
    selected = []

    root = tk.Tk()
    root.title("ELTA 4.4 — Select Orders")
    root.attributes('-topmost', True)
    root.geometry("1050x560")
    root.resizable(True, True)

    # --- top label ---
    tk.Label(root, text="Select orders to process:",
             font=('Arial', 12, 'bold'), pady=8).pack()

    # --- treeview frame ---
    tree_frame = tk.Frame(root)
    tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)

    cols = ('#', 'Name', 'Country', 'City', 'Street', 'Street 2', 'ZIP')
    tree = ttk.Treeview(tree_frame, columns=cols, show='headings', selectmode='none')

    tree.column('#',        width=30,  anchor='center', stretch=False)
    tree.column('Name',     width=200, anchor='w')
    tree.column('Country',  width=130, anchor='w')
    tree.column('City',     width=130, anchor='w')
    tree.column('Street',   width=200, anchor='w')
    tree.column('Street 2', width=160, anchor='w')
    tree.column('ZIP',      width=70,  anchor='w')

    for c in cols:
        tree.heading(c, text=c)

    scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    tree.pack(fill=tk.BOTH, expand=True)

    # checked state per iid
    checked = {}

    def row_tag(iid):
        return 'checked' if checked.get(iid) else 'unchecked'

    tree.tag_configure('checked',   background='#d4edda')
    tree.tag_configure('unchecked', background='#f8f9fa')
    tree.tag_configure('usa',       background='#fff3cd')

    def refresh_row(iid):
        tree.item(iid, tags=(row_tag(iid),))
        # update the # column with ✓ or ☐
        vals = list(tree.item(iid, 'values'))
        vals[0] = '✓' if checked[iid] else '☐'
        tree.item(iid, values=vals)

    def on_click(event):
        iid = tree.identify_row(event.y)
        if iid:
            checked[iid] = not checked[iid]
            refresh_row(iid)
            update_count()

    tree.bind('<Button-1>', on_click)

    count_var = tk.StringVar()

    def update_count():
        n = sum(1 for v in checked.values() if v)
        count_var.set(f"{n} / {len(records)} selected")

    # populate rows
    for i, r in enumerate(records):
        name    = f"{r.get('first_name','')} {r.get('last_name','')}".strip()
        country = r.get('ship_country', '')
        street  = f"{r.get('street_1','')} {r.get('street_number','')}".strip()
        iid     = str(i)
        is_usa  = country in USA_COUNTRY_VALUES
        checked[iid] = not is_usa   # pre-check non-USA, leave USA unchecked
        tree.insert('', 'end', iid=iid, values=(
            '✓' if checked[iid] else '☐',
            name, country,
            r.get('ship_city', ''),
            street,
            r.get('street_2', ''),
            r.get('ship_zipcode', ''),
        ))
        tree.item(iid, tags=(row_tag(iid),))

    update_count()

    # --- button bar ---
    btn_frame = tk.Frame(root)
    btn_frame.pack(fill=tk.X, padx=10, pady=6)

    def select_all():
        for iid in checked:
            checked[iid] = True
            refresh_row(iid)
        update_count()

    def deselect_all():
        for iid in checked:
            checked[iid] = False
            refresh_row(iid)
        update_count()

    def toggle_usa():
        """Toggle USA orders: if any USA checked → uncheck all USA; else check all USA."""
        usa_iids = [str(i) for i, r in enumerate(records)
                    if r.get('ship_country','') in USA_COUNTRY_VALUES]
        any_checked = any(checked[iid] for iid in usa_iids)
        for iid in usa_iids:
            checked[iid] = not any_checked
            refresh_row(iid)
        update_count()

    def proceed():
        for i, r in enumerate(records):
            if checked.get(str(i)):
                selected.append(r)
        root.destroy()

    tk.Button(btn_frame, text="Select All",   command=select_all,
              bg='#27ae60', fg='white', font=('Arial', 10, 'bold'),
              relief='flat', padx=10, pady=5).pack(side=tk.LEFT, padx=4)
    tk.Button(btn_frame, text="Deselect All", command=deselect_all,
              bg='#c0392b', fg='white', font=('Arial', 10, 'bold'),
              relief='flat', padx=10, pady=5).pack(side=tk.LEFT, padx=4)
    tk.Button(btn_frame, text="Toggle USA",      command=toggle_usa,
              bg='#e67e22', fg='white', font=('Arial', 10, 'bold'),
              relief='flat', padx=10, pady=5).pack(side=tk.LEFT, padx=4)

    tk.Label(btn_frame, textvariable=count_var,
             font=('Arial', 10), fg='#333').pack(side=tk.LEFT, padx=16)

    tk.Button(btn_frame, text="▶  Proceed", command=proceed,
              bg='#2980b9', fg='white', font=('Arial', 11, 'bold'),
              relief='flat', padx=18, pady=6).pack(side=tk.RIGHT, padx=6)

    root.grab_set()
    root.mainloop()
    return selected


# ── Review & Edit screen ─────────────────────────────────────────────────────

class EltaShippingApp:
    """Review & edit screen shown after order selection, before browser automation."""

    # Fields that must not be empty before processing
    REQUIRED = {
        'first_name', 'last_name',
        'street_1', 'street_number',
        'ship_zipcode', 'ship_city', 'ship_country',
        'weight_kg', 'length_cm', 'width_cm', 'height_cm',
    }

    # Grouped field layout: (field_key, display_label)
    SECTIONS = [
        ("Name", [
            ('first_name',    'First Name *'),
            ('last_name',     'Last Name *'),
        ]),
        ("Address", [
            ('street_1',      'Street Name *'),
            ('street_number', 'Street Number *'),
            ('street_2',      'Address Line 2'),
            ('ship_city',     'City *'),
            ('ship_state',    'State / Region'),
            ('ship_zipcode',  'ZIP / Postal Code *'),
            ('ship_country',  'Country *'),
        ]),
        ("Contact", [
            ('email', 'Email'),
            ('phone', 'Phone'),
        ]),
        ("Parcel", [
            ('weight_kg',   'Weight (kg) *'),
            ('length_cm',   'Length (cm) *'),
            ('width_cm',    'Width (cm) *'),
            ('height_cm',   'Height (cm) *'),
            ('customs_qty', 'Customs Qty'),
        ]),
    ]

    def __init__(self, root, records, mode='both'):
        self.root = root
        self.records = records
        self.mode = mode
        self.current_index = 0

        root.title("ELTA 4.4 — Review & Edit Orders")
        root.geometry("860x660")
        root.attributes('-topmost', True)
        root.resizable(True, True)

        # ── Title bar ──
        tk.Label(root,
                 text=f"Review & Edit  —  {len(records)} order(s) selected",
                 font=('Arial', 13, 'bold'), pady=8).pack()

        # ── Navigation bar ──
        nav = tk.Frame(root, bg='#ecf0f1', relief='ridge', bd=1)
        nav.pack(fill=tk.X, padx=10, pady=(0, 4))

        self.prev_btn = tk.Button(nav, text="◀ Previous", command=self.prev_record,
                                  font=('Arial', 10, 'bold'), bg='#95a5a6', fg='white',
                                  relief='flat', padx=10, pady=4, cursor='hand2')
        self.prev_btn.pack(side=tk.LEFT, padx=6, pady=4)

        self.status_var = tk.StringVar()
        tk.Label(nav, textvariable=self.status_var, font=('Arial', 10),
                 fg='#2c3e50', bg='#ecf0f1').pack(side=tk.LEFT, padx=12)

        self.next_btn = tk.Button(nav, text="Next ▶", command=self.next_record,
                                  font=('Arial', 10, 'bold'), bg='#95a5a6', fg='white',
                                  relief='flat', padx=10, pady=4, cursor='hand2')
        self.next_btn.pack(side=tk.RIGHT, padx=6, pady=4)

        # ── Scrollable fields area ──
        outer = tk.Frame(root)
        outer.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)

        canvas = tk.Canvas(outer, highlightthickness=0)
        vsb = ttk.Scrollbar(outer, orient='vertical', command=canvas.yview)
        self.fields_frame = tk.Frame(canvas)
        self.fields_frame.bind(
            '<Configure>',
            lambda e: canvas.configure(scrollregion=canvas.bbox('all'))
        )
        canvas.create_window((0, 0), window=self.fields_frame, anchor='nw')
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Bind mousewheel to canvas
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all('<MouseWheel>', _on_mousewheel)

        self.entries = {}
        self._build_fields()

        # ── Action bar ──
        actions = tk.Frame(root, bg='#dfe6e9', relief='ridge', bd=1)
        actions.pack(fill=tk.X, padx=10, pady=(4, 8))

        tk.Button(actions, text="Save Changes", command=self.save_changes,
                  font=('Arial', 10), bg='#e67e22', fg='white',
                  relief='flat', padx=12, pady=5, cursor='hand2').pack(side=tk.LEFT, padx=6, pady=6)

        tk.Button(actions, text="▶▶  Start Processing", command=self.start_processing,
                  font=('Arial', 12, 'bold'), bg='#27ae60', fg='white',
                  relief='flat', padx=18, pady=7, cursor='hand2').pack(side=tk.RIGHT, padx=6, pady=6)

        # Load first record after the window is fully drawn (avoids frozen Entry widgets)
        root.after(50, self._init_data)

    def _build_fields(self):
        f = self.fields_frame
        row = 0
        for section_name, fields in self.SECTIONS:
            # Section header
            hdr = tk.Label(f, text=section_name,
                           font=('Arial', 10, 'bold'), anchor='w',
                           bg='#d6eaf8', padx=8, pady=3, relief='flat')
            hdr.grid(row=row, column=0, columnspan=2, sticky='ew', pady=(10, 2), padx=2)
            row += 1
            for field_key, label_text in fields:
                tk.Label(f, text=label_text, font=('Arial', 10),
                         anchor='w', padx=8).grid(row=row, column=0, sticky='w', pady=2)
                entry = tk.Entry(f, font=('Arial', 10), width=46)
                entry.grid(row=row, column=1, sticky='ew', padx=(4, 12), pady=2)
                self.entries[field_key] = entry
                row += 1
        f.grid_columnconfigure(1, weight=1)

    def _init_data(self):
        """Check customer DB for repeat customers, then display first record."""
        db = load_customer_db()
        for record in self.records:
            key = customer_db_key(record)
            if not (key and key in db):
                continue
            stored = db[key]
            addr_line = (
                f"{stored.get('street_1','')} {stored.get('street_number','')}".strip() + ", "
                f"{stored.get('ship_zipcode','')} {stored.get('ship_city','')}".strip() + ", "
                f"{stored.get('ship_country','')}".strip()
            )
            parcel_line = (
                f"Weight: {stored.get('weight_kg','?')} kg  |  "
                f"{stored.get('length_cm','?')} × {stored.get('width_cm','?')} × "
                f"{stored.get('height_cm','?')} cm"
            )
            use_stored = messagebox.askyesno(
                "Repeat Customer",
                f"Stored data found for {record['full_name']}:\n\n"
                f"Address: {addr_line}\n"
                f"Parcel:  {parcel_line}\n\n"
                "Use stored address + parcel details?",
                parent=self.root
            )
            if use_stored:
                for field in ('street_1', 'street_number', 'street_2',
                              'ship_city', 'ship_state', 'ship_zipcode', 'ship_country',
                              'weight_kg', 'length_cm', 'width_cm', 'height_cm'):
                    if stored.get(field) is not None:
                        record[field] = stored[field]
                print(f"✓ Using stored data for {record['full_name']}")

        self.display_record(0)

    def display_record(self, index):
        if not (0 <= index < len(self.records)):
            return
        self.current_index = index
        record = self.records[index]

        for field, entry in self.entries.items():
            entry.delete(0, tk.END)
            val = record.get(field, '')
            if val:
                entry.insert(0, str(val))

        self._highlight_required()
        name = record.get('full_name') or f"{record.get('first_name','')} {record.get('last_name','')}".strip()
        self.status_var.set(f"Order {index + 1} of {len(self.records)}  —  {name}")
        self.prev_btn.config(state=tk.NORMAL if index > 0 else tk.DISABLED)
        self.next_btn.config(state=tk.NORMAL if index < len(self.records) - 1 else tk.DISABLED)

    def _highlight_required(self):
        for field, entry in self.entries.items():
            if field in self.REQUIRED and not entry.get().strip():
                entry.config(bg='#ffd7d7')
            else:
                entry.config(bg='white')

    def save_changes(self):
        if not (0 <= self.current_index < len(self.records)):
            return
        record = self.records[self.current_index]
        for field, entry in self.entries.items():
            record[field] = entry.get().strip()
        # Keep full_name in sync
        record['full_name'] = f"{record.get('first_name','')} {record.get('last_name','')}".strip()
        self._highlight_required()
        name = record.get('full_name', '')
        self.status_var.set(
            f"Order {self.current_index + 1} of {len(self.records)}  —  {name}  ✓ saved"
        )

    def next_record(self):
        self.save_changes()
        if self.current_index < len(self.records) - 1:
            self.display_record(self.current_index + 1)

    def prev_record(self):
        self.save_changes()
        if self.current_index > 0:
            self.display_record(self.current_index - 1)

    def start_processing(self):
        self.save_changes()

        # Warn about any missing required fields
        problems = []
        for i, r in enumerate(self.records):
            missing = [f for f in self.REQUIRED if not r.get(f, '').strip()]
            if missing:
                problems.append(f"Order {i+1} ({r.get('full_name','?')}): {', '.join(missing)}")

        if problems:
            msg = ("The following orders have missing required fields:\n\n"
                   + "\n".join(problems)
                   + "\n\nProceed anyway?")
            if not messagebox.askyesno("Missing Fields", msg, parent=self.root):
                return

        generate_letters = (self.mode == 'both')
        self.root.destroy()
        process_elta_labels(self.records, sender_email="math4econ@gmail.com",
                            generate_letters=generate_letters)


# ─────────────────────────────────────────────────────────────────────────────

def process_elta_labels(shipping_records, sender_email="math4econ@gmail.com", generate_letters=True):
    """Process ELTA label creation for the given shipping records"""
    if not shipping_records:
        print("No shipping records to process.")
        return

    # Configure Firefox (auto-detect on Windows/macOS; snap path on Linux)
    import platform
    options = webdriver.FirefoxOptions()
    if platform.system() == "Linux":
        options.binary_location = "/snap/firefox/current/usr/lib/firefox/firefox"
    driver = webdriver.Firefox(options=options)

    try:
        # Open ELTA WebLabeling
        print("Opening ELTA WebLabeling...")
        driver.get("https://weblabeling.elta.gr/")
        human_delay(1, 2)  # Initial page load delay

        # --- GUEST LOGIN ---
        print("Navigating to guest login...")
        driver.get("https://weblabeling.elta.gr/el-GR/Account/NCLogin")
        WebDriverWait(driver, 10).until(
            lambda d: "NCLogin" in d.current_url
        )
        print("✓ On guest login page")
        print("Current URL:", driver.current_url)

        # --- HANDLE LOGIN FORM ---
        print("Filling login form...")

        # Fill the email field using sender's fixed email (not from records)
        email = "math4econ@gmail.com"  # Fixed sender email for ELTA login
        email_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "Email"))
        )
        human_delay(0.5, 1.5)
        email_field.clear()  # Clear any default value
        human_delay(0.3, 0.8)
        # Type the email with human-like behavior
        for char in email:
            email_field.send_keys(char)
            human_delay(0.05, 0.15)  # Brief delay between keystrokes

        print("✓ Email entered")

        # Ask user to complete CAPTCHA manually
        print("\n⚠️ ACTION REQUIRED: Please complete the CAPTCHA in the browser.")
        print("When you've completed the CAPTCHA and accepted terms, the program will automatically continue...")

        # Wait for user to solve CAPTCHA and submit the form themselves
        print("Waiting for you to solve the CAPTCHA and click Next in the browser...")
        try:
            # Wait up to 3 minutes for the URL to leave the login page
            WebDriverWait(driver, 180).until(
                lambda d: "NCLogin" not in d.current_url
            )
            print("✓ Successfully moved to next page")
            print("Current URL:", driver.current_url)
        except Exception as e:
            print(f"Timed out waiting for CAPTCHA: {str(e)}")
            wait_for_user("Please complete the CAPTCHA and click Next in the browser, then click OK here.")

        # --- HANDLE COUNTRY SELECTION ---
        print("Selecting country...")

        # Get country from first record (translate name if needed)
        country = shipping_records[0].get('ship_country', 'United States')
        country = COUNTRY_NAME_MAP.get(country, country)

        # Find the country Select2 dropdown
        try:
            # Find all select2 dropdown containers
            select2_containers = driver.find_elements(By.XPATH, "//span[contains(@class, 'select2-container')]")
            print(f"Found {len(select2_containers)} Select2 containers")

            # Find the country dropdown container
            country_dropdown = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(@class, 'select2-selection')]"))
            )

            # Click to open the dropdown
            country_dropdown.click()
            print("Clicked country dropdown")
            human_delay(0.5, 1)

            # Wait for dropdown to open and search for the country
            search_input = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//input[contains(@class, 'select2-search__field')]"))
            )

            # Type country with human-like behavior
            for char in country:
                search_input.send_keys(char)
                human_delay(0.05, 0.1)

            human_delay(0.5, 1)  # Wait for search results

            # Press Enter to select
            search_input.send_keys(Keys.ENTER)
            print(f"✓ Selected country: {country}")

            # Wait for the select2 dropdown to close completely
            WebDriverWait(driver, 10).until(
                EC.invisibility_of_element_located((By.XPATH, "//span[@class='select2-dropdown']"))
            )
            print("✓ Country dropdown closed")

            # Additional delay to make sure all AJAX calls complete and page updates
            human_delay(2, 3)
        except Exception as e:
            print(f"Automated country selection failed: {str(e)}")
            safe_screenshot(driver, "country_selection_failed.png")

            wait_for_user(f"Please select '{country}' manually in the country dropdown, then click OK.")
            # Extra delay after manual interaction
            human_delay(2, 3)

        # --- HANDLE DELIVERY TYPE SELECTION ---
        print("Selecting delivery type...")

        try:
            # Use the underlying <select> element directly — bypasses Select2 UI entirely
            service_select_el = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH,
                    "//select[contains(@id,'Service') or contains(@name,'Service') or contains(@id,'service') or contains(@name,'service')]"
                ))
            )
            # Print available options for debugging
            service_select = Select(service_select_el)
            available = [o.text for o in service_select.options]
            print(f"Service options: {available}")

            # Find option value containing '854'
            target_option = next((o for o in service_select_el.find_elements(By.TAG_NAME, 'option') if '854' in o.text), None)
            if target_option:
                # Use JS to set value and trigger change event (Select2 hides the element)
                driver.execute_script(
                    "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('change'));",
                    service_select_el, target_option.get_attribute('value')
                )
                human_delay(1, 2)  # Wait for Select2 to update its display
                print(f"✓ Selected delivery type: {target_option.text}")
            else:
                raise Exception(f"No option containing '854' found. Options: {available}")

        except Exception as e:
            print(f"Automated delivery type selection failed: {str(e)}")
            safe_screenshot(driver, "delivery_selection_failed.png")
            wait_for_user("Please select '854 LL' manually in the delivery type dropdown, then click OK.")

        human_delay(1, 2)  # Wait for any updates after delivery selection

        # Click Next: service → sender
        find_and_click_next_button(driver, step=1)
        WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located((By.ID, "SenderFirstName"))
        )
        print("✓ Sender step active")

        # --- HANDLE SENDER DATA FORM ---
        print("Filling sender data form...")

        # Define sender's data (fixed values)
        sender_data = {
            "Όνομα": "KOSTAS",           # First Name
            "Επώνυμο": "PAPANAYITOU",          # Last Name
            "Όνομα Οδού": "ANAXIMENOUS",        # Street Name
            "Αρ. Οδού": "18",                  # Street Number
            "Ταχ. Κώδικας": "11631",           # Postal Code
            "Πόλη": "ATHENS"                   # City
        }

        # Fill in the form fields
        try:
            # Helper function to fill a text field with human-like typing
            def fill_field(field_label, value):
                if not value:  # Skip empty values
                    return

                try:
                    # Find field by XPath — use contains() to handle asterisks/extra text in labels
                    input_field = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, f"//label[contains(normalize-space(),'{field_label}')]/following::input[1]"))
                    )

                    # Clear field and type value with human-like delay
                    input_field.clear()
                    human_delay(0.2, 0.5)
                    for char in value:
                        input_field.send_keys(char)
                        human_delay(0.05, 0.15)
                    print(f"✓ Filled {field_label}: {value}")
                except Exception as e:
                    print(f"Error finding field for {field_label}: {str(e)}")

                    # Try alternative approach with JavaScript
                    try:
                        # Get all inputs and look for nearby labels
                        all_inputs = driver.find_elements(By.TAG_NAME, "input")

                        for inp in all_inputs:
                            label_for_input = None
                            try:
                                # Look for a label near this input
                                label_for_input = driver.execute_script("""
                                    var input = arguments[0];
                                    var labels = document.getElementsByTagName('label');
                                    for(var i = 0; i < labels.length; i++) {
                                        if(labels[i].htmlFor == input.id || labels[i].textContent.trim() == arguments[1]) {
                                            return labels[i].textContent.trim();
                                        }
                                    }
                                    return null;
                                """, inp, field_label)
                            except:
                                pass

                            if label_for_input and label_for_input.strip() == field_label.strip():
                                # Found the right input
                                inp.clear()
                                human_delay(0.2, 0.5)
                                for char in value:
                                    inp.send_keys(char)
                                    human_delay(0.05, 0.15)
                                print(f"✓ Filled {field_label} (alternative method): {value}")
                                break
                    except Exception as e2:
                        print(f"Alternative method also failed for {field_label}: {str(e2)}")

            # Fill each required field
            for label, value in sender_data.items():
                try:
                    fill_field(label, value)
                    human_delay(0.2, 0.5)  # Delay between fields
                except Exception as e:
                    print(f"Error filling {label}: {str(e)}")

            print("✓ Completed sender data form")

        except Exception as e:
            print(f"Error filling sender form: {str(e)}")
            safe_screenshot(driver, "sender_form_error.png")

            wait_for_user("Please fill in the sender data manually, then click OK.")

        # Click Next: sender → receiver, then wait for receiver step
        find_and_click_next_button(driver, step=2)
        WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located((By.ID, "RecipientFirstName"))
        )
        print("✓ Receiver step active")

        # Process each shipping record
        process_all_records(shipping_records, driver, generate_letters)

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        # Save screenshot for debugging
        safe_screenshot(driver, "error_screenshot.png")

    finally:
        # Clean up
        driver.quit()
        print("Browser closed.")

def process_all_records(shipping_records, driver, generate_letters=True):
    """Process all shipping records one by one"""
    for index, record in enumerate(shipping_records):
        print(f"\n--- Processing record {index+1} of {len(shipping_records)} ---")
        print(f"Recipient: {record.get('first_name', '')} {record.get('last_name', '')}")

        # If this is not the first record, we need to create a new shipment
        if index > 0:
            try:
                print("Creating a new shipment for next recipient...")

                # Look for "New Shipment" or similar button
                new_shipment_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Νέα αποστολή')] | //button[contains(text(), 'Νέα αποστολή')] | //a[contains(@href, 'New')] | //a[contains(@href, 'Create')]"))
                )
                human_delay(0.5, 1.5)
                new_shipment_button.click()
                print("✓ Clicked 'New Shipment' button")

                # Wait for page to change to new shipment form
                WebDriverWait(driver, 15).until(
                    lambda d: "Create" in d.current_url or "New" in d.current_url or len(d.find_elements(By.XPATH, "//div[contains(@class, 'load') or contains(@class, 'progress')]")) == 0
                )

                # Select country and service type for this order
                select_country_and_service(driver, record.get('ship_country', 'United States'))

                # Service → Sender (step 1) — sender already filled, so silently skip if button not found
                find_and_click_next_button(driver, step=1, quiet=True)
                WebDriverWait(driver, 15).until(
                    EC.visibility_of_element_located((By.ID, "SenderFirstName"))
                )
                # Sender already filled — just click Next to skip it (step 2)
                find_and_click_next_button(driver, step=2)
                WebDriverWait(driver, 15).until(
                    EC.visibility_of_element_located((By.ID, "RecipientFirstName"))
                )
                print("✓ Receiver step is now active")

            except Exception as e:
                print(f"Error creating new shipment: {str(e)}")
                safe_screenshot(driver, f"new_shipment_error_{index}.png")

                wait_for_user("Please navigate to create a new shipment manually. When at the receiver form, click OK.")

        try:
            # --- HANDLE RECEIVER DATA FORM ---
            print("Filling receiver data form...")

            # Define receiver data mapping from our record to ELTA form fields
            receiver_data = {
                "Όνομα": record.get("first_name", ""),           # First Name
                "Επώνυμο": record.get("last_name", ""),          # Last Name
                "Όνομα Οδού": record.get("street_1", ""),        # Street Name
                "Αρ. Οδού": record.get("street_number", ""),     # Street Number
                "Ταχ. Κώδικας": record.get("ship_zipcode", ""),  # Postal Code
                "Πόλη": record.get("ship_city", ""),             # City
                "E-Mail": record.get("email", ""),               # Buyer email from Etsy orders page
                "Οργανισμός": record.get("street_2", ""),        # Address line 2 → Οργανισμός
                "Σημείο παραλαβής": record.get("street_2", ""),  # Address line 2 → Σημείο παραλαβής
            }

            # Fill in weight and dimensions
            weight_data = {
                "Βάρος (Kg)": record.get("weight_kg", "0,49")
            }

            # Dimensions data
            dimensions_data = {
                "length": record.get("length_cm", "21"),
                "width": record.get("width_cm", "28"),
                "height": record.get("height_cm", "12")
            }

            # Fill the receiver form (same page also has content/weight/dimensions)
            fill_receiver_form(driver, receiver_data, weight_data, dimensions_data)

            # Fill content description (on the same wizard page as receiver)
            # Skipped automatically for EU countries — no customs form
            country = record.get('ship_country', '')
            fill_content_description(driver, country=country)

            # Click Next: receiver → customs (non-EU) or print (EU)
            find_and_click_next_button(driver, step=3)
            human_delay(1, 2)

            # For non-EU: fill the Τελωνειακή Δήλωση page, then click Next again
            if country not in EU_COUNTRIES:
                fill_customs_declaration(driver, record)
                find_and_click_next_button(driver, step=4)
                human_delay(1, 2)

            # Print the label
            print_shipping_label(driver, record)

            # Save this customer's address + parcel details to the DB for future orders
            try:
                db = load_customer_db()
                key = customer_db_key(record)
                if key:
                    db[key] = {k: record.get(k, '') for k in (
                        'full_name', 'first_name', 'last_name',
                        'street_1', 'street_number', 'street_2',
                        'ship_city', 'ship_state', 'ship_zipcode', 'ship_country', 'email',
                        'weight_kg', 'length_cm', 'width_cm', 'height_cm',
                    )}
                    save_customer_db(db)
                    print(f"✓ Saved address + parcel for {record['full_name']} to customer DB")
            except Exception as e:
                print(f"⚠ Could not save to customer DB: {e}")

            # Generate thank-you letter
            if generate_letters:
                try:
                    generate_thank_you(record)
                except Exception as e:
                    print(f"⚠ Could not generate thank-you letter: {e}")

        except Exception as e:
            print(f"❌ Error processing record {index+1} ({record.get('full_name', '?')}): {e}")
            safe_screenshot(driver, f"record_{index+1}_error.png")
            wait_for_user(
                f"Error on record {index+1}: {record.get('full_name', '?')}\n\n"
                f"{e}\n\n"
                f"Fix it manually in the browser, then click Done to continue to the next label."
            )

        # Wait before next record
        human_delay(2, 3)

def select_country_and_service(driver, country="United States"):
    """Select country and service type"""
    country = COUNTRY_NAME_MAP.get(country, country)
    # --- HANDLE COUNTRY SELECTION ---
    print("Selecting country...")

    # Find the country Select2 dropdown
    try:
        # Find all select2 dropdown containers
        select2_containers = driver.find_elements(By.XPATH, "//span[contains(@class, 'select2-container')]")
        print(f"Found {len(select2_containers)} Select2 containers")

        # Find the country dropdown container
        country_dropdown = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[contains(@class, 'select2-selection')]"))
        )

        # Click to open the dropdown
        country_dropdown.click()
        print("Clicked country dropdown")
        human_delay(0.5, 1)

        # Wait for dropdown to open and search for the country
        search_input = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//input[contains(@class, 'select2-search__field')]"))
        )

        # Type country with human-like behavior
        for char in country:
            search_input.send_keys(char)
            human_delay(0.05, 0.1)

        human_delay(0.5, 1)  # Wait for search results

        # Click the exact matching option (avoids "Spain Canary Islands" etc.)
        try:
            exact = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH,
                    f"//li[contains(@class,'select2-results__option') and normalize-space(text())='{country}']"
                ))
            )
            exact.click()
        except Exception:
            # Fall back to Enter if exact match not found
            search_input.send_keys(Keys.ENTER)
        print(f"✓ Selected country: {country}")

        # Wait for the select2 dropdown to close completely
        WebDriverWait(driver, 10).until(
            EC.invisibility_of_element_located((By.XPATH, "//span[@class='select2-dropdown']"))
        )
        print("✓ Country dropdown closed")

        # Additional delay to make sure all AJAX calls complete and page updates
        human_delay(2, 3)
    except Exception as e:
        print(f"Automated country selection failed: {str(e)}")
        safe_screenshot(driver, "country_selection_failed.png")

        wait_for_user(f"Please select '{country}' manually in the country dropdown, then click OK.")
        human_delay(2, 3)

    # --- HANDLE DELIVERY TYPE SELECTION ---
    print("Selecting delivery type...")

    try:
        service_select_el = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH,
                "//select[contains(@id,'Service') or contains(@name,'Service') or contains(@id,'service') or contains(@name,'service')]"
            ))
        )
        service_select = Select(service_select_el)
        available = [o.text for o in service_select.options]
        print(f"Service options: {available}")
        target_option = next((o for o in service_select_el.find_elements(By.TAG_NAME, 'option') if '854' in o.text), None)
        if target_option:
            driver.execute_script(
                "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('change'));",
                service_select_el, target_option.get_attribute('value')
            )
            human_delay(1, 2)
            print(f"✓ Selected delivery type: {target_option.text}")
        else:
            raise Exception(f"No option containing '854' found. Options: {available}")
    except Exception as e:
        print(f"Automated delivery type selection failed: {str(e)}")
        safe_screenshot(driver, "delivery_selection_failed.png")
        wait_for_user("Please select '854 LL' manually in the delivery type dropdown, then click OK.")

    human_delay(1, 2)  # Wait for any updates after delivery selection

def fill_sender_form(driver):
    """Fill in the sender data form"""
    print("Filling sender data form...")

    # Define sender's data (fixed values)
    sender_data = {
        "Όνομα": "KONSTANTINOS",           # First Name
        "Επώνυμο": "PAPANAYITOU",          # Last Name
        "Όνομα Οδού": "ERASINIDOU",        # Street Name
        "Αρ. Οδού": "58",                  # Street Number
        "Ταχ. Κώδικας": "11632",           # Postal Code
        "Πόλη": "ATHENS"                   # City
    }

    # Fill in the form fields
    try:
        # Fill each required field
        for label, value in sender_data.items():
            try:
                fill_field(driver, label, value)
                human_delay(0.2, 0.5)  # Delay between fields
            except Exception as e:
                print(f"Error filling {label}: {str(e)}")

        print("✓ Completed sender data form")

    except Exception as e:
        print(f"Error filling sender form: {str(e)}")
        safe_screenshot(driver, "sender_form_error.png")

        wait_for_user("Please fill in the sender data manually, then click OK.")

def fill_by_id(driver, field_id, value):
    """Fill a field by its ID using JS to scroll it into view first."""
    try:
        el = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, field_id)))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        human_delay(0.2, 0.4)
        el.clear()
        human_delay(0.1, 0.3)
        for char in value:
            el.send_keys(char)
            human_delay(0.04, 0.1)
        print(f"✓ Filled {field_id}: {value}")
        return True
    except Exception as e:
        print(f"⚠ Could not fill {field_id}: {str(e)}")
        return False

def fill_visible_field(driver, field_label, value):
    """Fill the first VISIBLE input after a label containing field_label text."""
    if not value:
        return False
    try:
        # Get all inputs following any label that contains this text
        candidates = driver.find_elements(
            By.XPATH,
            f"//label[contains(normalize-space(),'{field_label}')]/following::input[self::input[@type='text' or @type='email' or @type='number' or not(@type)]][1]"
        )
        # Filter to only displayed+enabled ones
        visible = [el for el in candidates if el.is_displayed() and el.is_enabled()]
        if not visible:
            # Broader search: any visible text input on page (last resort)
            print(f"⚠ No visible input found for label '{field_label}'")
            return False
        el = visible[0]
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        human_delay(0.1, 0.3)
        el.clear()
        human_delay(0.1, 0.2)
        for char in value:
            el.send_keys(char)
            human_delay(0.04, 0.1)
        print(f"✓ Filled (visible) '{field_label}': {value}")
        return True
    except Exception as e:
        print(f"⚠ fill_visible_field failed for '{field_label}': {e}")
        return False

def fill_receiver_form(driver, receiver_data, weight_data, dimensions_data):
    """Fill in the receiver data form using known field IDs."""
    print("Filling receiver data form...")

    try:
        # Map our data keys to actual ELTA receiver field IDs (confirmed from debug dump)
        id_map = {
            "Όνομα":              "RecipientFirstName",
            "Επώνυμο":            "RecipientLastName",
            "Όνομα Οδού":         "RecipientStreetName",
            "Αρ. Οδού":           "RecipientStreetNumber",
            "Ταχ. Κώδικας":       "RecipientPostalCode",
            "Πόλη":               "RecipientTown",
            "E-Mail":             "RecipientEmail",
            "Οργανισμός":         "RecipientOrganization",
            "Σημείο παραλαβής":   "RecipientDeliveryPoint",
        }

        for label, field_id in id_map.items():
            value = receiver_data.get(label, "")
            if not value:
                continue
            if not fill_by_id(driver, field_id, value):
                # Fallback: find VISIBLE inputs after a label matching this text
                fill_visible_field(driver, label, value)
            human_delay(0.2, 0.4)

        # Weight and dimensions — use confirmed field IDs from debug dump
        fill_by_id(driver, "VoucherDetailWeight", weight_data.get("Βάρος (Kg)", "0,49"))
        fill_by_id(driver, "VoucherDetailLength", dimensions_data.get("length", "21"))
        fill_by_id(driver, "VoucherDetailWidth",  dimensions_data.get("width", "28"))
        fill_by_id(driver, "VoucherDetailHeight", dimensions_data.get("height", "12"))

        # Tick the "Δώρο" (Gift) checkbox
        try:
            gift_cb = driver.find_element(By.ID, "VoucherDetailGift")
            if not gift_cb.is_selected():
                driver.execute_script("arguments[0].click();", gift_cb)
            print("✓ Checked gift checkbox (VoucherDetailGift)")
        except Exception as e:
            print(f"⚠ Could not check gift checkbox: {e}")

        print("✓ Completed receiver data form")

    except Exception as e:
        print(f"Error filling receiver form: {str(e)}")
        safe_screenshot(driver, "receiver_form_error.png")

        wait_for_user("Please fill in the receiver data manually, then click OK.")

def fill_content_description(driver, country=''):
    """Fill in the content description form (customs). Skipped for EU countries."""
    if country in EU_COUNTRIES:
        print(f"ℹ Skipping content description — EU country ({country}), no customs form")
        return

    print("Filling content description form...")

    try:
        # VoucherDetailExplanation is disabled until a content type is selected.
        # Force-enable it via JS, set value and dispatch change event.
        driver.execute_script("""
            var el = document.getElementById('VoucherDetailExplanation');
            if (el) {
                el.removeAttribute('disabled');
                el.removeAttribute('readonly');
                el.value = 'festive items';
                el.dispatchEvent(new Event('input'));
                el.dispatchEvent(new Event('change'));
            }
        """)
        print("✓ Filled VoucherDetailExplanation: festive items")

        driver.execute_script("""
            var el = document.getElementById('ProtectedVoucherDetailQuantity');
            if (el) {
                el.removeAttribute('disabled');
                el.removeAttribute('readonly');
                el.value = '1';
                el.dispatchEvent(new Event('input'));
                el.dispatchEvent(new Event('change'));
            }
        """)
        print("✓ Filled ProtectedVoucherDetailQuantity: 1")

        print("✓ Completed content description form")

    except Exception as e:
        print(f"Error filling content description: {str(e)}")
        safe_screenshot(driver, "content_form_error.png")
        wait_for_user("Please fill in the content description manually, then click OK.")

def fill_customs_declaration(driver, record):
    """Fill the Τελωνειακή Δήλωση step (non-EU countries only)."""
    print("Filling customs declaration form...")
    try:
        WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located((By.ID, "CustomsDeclarationDetailedDescriptionOfContents1"))
        )
        qty        = record.get('customs_qty', '2')
        total_str  = record.get('weight_kg', '0,49')
        # Net weight = 80% of total weight (goods only, no packaging)
        total_kg   = float(total_str.replace(',', '.'))
        net_kg     = round(total_kg * 0.8, 2)
        net_weight = str(net_kg).replace('.', ',')

        fill_by_id(driver, "CustomsDeclarationDetailedDescriptionOfContents1", "Carnival Wigs")
        fill_by_id(driver, "CustomsDeclarationQuantity1",                       qty)
        fill_by_id(driver, "CustomsDeclarationNetWeight1",                       net_weight)
        fill_by_id(driver, "CustomsDeclarationValue1",                           "15")
        fill_by_id(driver, "CustomsDeclarationHSTarifNumber1",                   "9505900014")
        fill_by_id(driver, "CustomsDeclarationCounryOfOrigionOfGoods1",          "GR")

        print("✓ Customs declaration filled")
    except Exception as e:
        print(f"Error filling customs form: {e}")
        safe_screenshot(driver, "customs_form_error.png")
        wait_for_user("Please fill in the customs declaration manually, then click OK.")


OUTPUT_DIR = os.path.expanduser("~/Documents/ELTA_NEW_PROGRAM")

def rename_latest_pdf(last_name, first_name, tracking_number):
    """Move and rename the most recently downloaded PDF to OUTPUT_DIR/SURNAME_NAME_DD_MM_YY.pdf"""
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        downloads_dir = os.path.expanduser("~/Downloads")
        pdf_files = [
            os.path.join(downloads_dir, f)
            for f in os.listdir(downloads_dir)
            if f.lower().endswith('.pdf')
        ]
        if not pdf_files:
            print("⚠ No PDF found in ~/Downloads to rename")
            return
        latest_pdf = max(pdf_files, key=os.path.getmtime)
        surname = last_name.upper()
        name   = first_name.upper()
        date_str = datetime.date.today().strftime("%d_%m_%y")
        new_name = f"{surname}_{name}_{date_str}.pdf"
        new_path = os.path.join(OUTPUT_DIR, new_name)
        # Remove destination first if it exists (avoids FileExistsError same customer same day)
        if os.path.exists(new_path):
            os.remove(new_path)
        import shutil
        shutil.move(latest_pdf, new_path)
        print(f"✓ PDF saved as: {new_name}  →  {OUTPUT_DIR}")
    except Exception as e:
        print(f"⚠ Could not rename PDF: {e}")

def print_shipping_label(driver, record):
    """Print the shipping label and extract tracking number"""
    print("Processing final screen and printing label...")

    first_name = record.get('first_name', 'UNKNOWN')
    last_name  = record.get('last_name',  'UNKNOWN')

    try:
        # The print button has a known ID — use it directly
        print_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.ID, "printVoucher"))
        )
        human_delay(0.5, 1.5)
        driver.execute_script("arguments[0].click();", print_button)
        print("✓ Clicked print button (printVoucher)")

        # Wait for PDF to download
        human_delay(4, 6)

        # Extract ELTA tracking number (e.g. LL123456789GR)
        page_text = driver.page_source
        tracking_match = re.search(r'[A-Z]{2}\d{9}[A-Z]{2}', page_text)
        if tracking_match:
            tracking_number = tracking_match.group(0)
            print(f"✓ Tracking number: {tracking_number}")
        else:
            tracking_number = None
            print("⚠ Could not find tracking number on page")

        # Rename and move the downloaded PDF
        rename_latest_pdf(last_name, first_name, tracking_number)

        # Brief pause then continue — no manual confirm needed
        human_delay(1, 2)

    except Exception as e:
        print(f"Error on final screen: {str(e)}")
        wait_for_user(
            f"Cannot find the print button for {first_name} {last_name}.\n"
            f"Please click Εκτύπωση manually, then click Done."
        )

def fill_field(driver, field_label, value):
    """Helper function to fill a form field with human-like typing"""
    if not value:  # Skip empty values
        return

    try:
        # Find all inputs after the label, pick the first visible+enabled one
        candidates = driver.find_elements(
            By.XPATH,
            f"//label[contains(normalize-space(),'{field_label}')]/following::input[1]"
        )
        input_field = next((el for el in candidates if el.is_displayed() and el.is_enabled()), None)
        if input_field is None:
            raise Exception("No visible+enabled input found")

        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", input_field)
        # Clear field and type value with human-like delay
        input_field.clear()
        human_delay(0.2, 0.5)
        for char in value:
            input_field.send_keys(char)
            human_delay(0.05, 0.15)
        print(f"✓ Filled {field_label}: {value}")
    except Exception as e:
        print(f"Error finding field for {field_label}: {str(e)}")

        # Try alternative approach with JavaScript
        try:
            # Get all inputs and look for nearby labels
            all_inputs = driver.find_elements(By.TAG_NAME, "input")

            for inp in all_inputs:
                label_for_input = None
                try:
                    # Look for a label near this input
                    label_for_input = driver.execute_script("""
                        var input = arguments[0];
                        var labels = document.getElementsByTagName('label');
                        for(var i = 0; i < labels.length; i++) {
                            if(labels[i].htmlFor == input.id || labels[i].textContent.trim() == arguments[1]) {
                                return labels[i].textContent.trim();
                            }
                        }
                        return null;
                    """, inp, field_label)
                except:
                    pass

                if label_for_input and label_for_input.strip() == field_label.strip():
                    # Found the right input
                    inp.clear()
                    human_delay(0.2, 0.5)
                    for char in value:
                        inp.send_keys(char)
                        human_delay(0.05, 0.15)
                    print(f"✓ Filled {field_label} (alternative method): {value}")
                    break
        except Exception as e2:
            print(f"Alternative method also failed for {field_label}: {str(e2)}")

def find_and_click_next_button(driver, step=None, quiet=False):
    """Click the Επόμενο button for the given wizard step.

    step=None or 1 → service selection step  (no data-step attr)
    step=2         → sender step              (data-step="2")
    step=3         → receiver step            (data-step="3")
    step=4         → customs step             (data-step="4")

    Each step has its own btn-next in the DOM; targeting by data-step
    avoids clicking the wrong one (they are all present simultaneously).
    """
    if step is None or step == 1:
        selector = 'button.btn-next:not([data-step])'
    else:
        selector = f'button.btn-next[data-step="{step}"]'

    print(f"Clicking Next button (step={step or 1})...")
    human_delay(0.4, 0.8)

    try:
        btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
        )
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        human_delay(0.2, 0.4)
        driver.execute_script("arguments[0].click();", btn)
        print(f"✓ Clicked btn-next (step={step or 1})")
        return True
    except Exception as e:
        print(f"⚠ Could not click btn-next step={step or 1}: {e}")
        if not quiet:
            wait_for_user("Please click the Επόμενο button manually, then click Done.")
        return False

# Main execution block
if __name__ == "__main__":
    print("ELTA Weblabeling 4.4 — starting...")
    try:
        # 1. Pick the orders file
        filepath = ask_for_orders_file()

        # 2. Load all orders
        all_records = load_orders_from_html(filepath)
        if not all_records:
            raise SystemExit("No orders found in file.")

        # Add weight/dimension defaults
        default_values = {
            "weight_kg": "0,49", "length_cm": "21",
            "width_cm": "28", "height_cm": "12", "customs_qty": "2"
        }
        for r in all_records:
            for k, v in default_values.items():
                r.setdefault(k, v)

        # 3. Selection table — user ticks which orders to process
        selected = show_order_selection(all_records)
        if not selected:
            raise SystemExit("No orders selected.")
        print(f"✓ {len(selected)} order(s) selected.")

        # 4. What to do: labels + letters / labels only / letters only
        mode = ask_mode()

        if mode == 'letters':
            # Letters-only: no browser needed, no review screen needed
            print(f"\nGenerating thank-you letters for {len(selected)} record(s)...")
            for record in selected:
                try:
                    generate_thank_you(record)
                except Exception as e:
                    print(f"⚠ Letter failed for {record.get('full_name', '?')}: {e}")
            print("\nDone. Letters saved to", OUTPUT_DIR)
        else:
            # Labels (+ optional letters): show review & edit screen first
            root = tk.Tk()
            EltaShippingApp(root, selected, mode)
            root.mainloop()
            # EltaShippingApp.start_processing() calls process_elta_labels() after root.destroy()
            print("Processing finished.")

    except SystemExit as e:
        print(str(e))
    except Exception as e:
        print(f"Error occurred: {e}")
        import traceback
        traceback.print_exc()
else:
    print(f"Script imported as module with name: {__name__}")
