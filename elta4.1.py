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
    root.title("Τι θέλετε να κάνετε;")
    root.attributes('-topmost', True)
    root.lift()
    root.focus_force()
    root.resizable(False, False)

    tk.Label(root, text="Τι θέλετε να εκτελεστεί;", wraplength=380, justify='center',
             pady=14, padx=16, font=('Arial', 12, 'bold')).pack()

    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=(4, 16))

    def pick(val):
        result[0] = val
        root.destroy()

    tk.Button(btn_frame, text="Ετικέτες + Ευχαριστήρια", command=lambda: pick('both'),
              bg='#2980b9', fg='white', font=('Arial', 11, 'bold'),
              relief='flat', padx=14, pady=7, cursor='hand2').pack(fill='x', padx=12, pady=4)
    tk.Button(btn_frame, text="Μόνο Ετικέτες", command=lambda: pick('labels'),
              bg='#27ae60', fg='white', font=('Arial', 11, 'bold'),
              relief='flat', padx=14, pady=7, cursor='hand2').pack(fill='x', padx=12, pady=4)
    tk.Button(btn_frame, text="Μόνο Ευχαριστήρια", command=lambda: pick('letters'),
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

class EltaShippingApp:
    def __init__(self, root, filepath, include_usa=True, mode='both'):
        self.root = root
        self.filepath = filepath
        self.include_usa = include_usa
        self.mode = mode  # 'both' or 'labels'
        self.root.title("ELTA Shipping Label Generator")
        self.root.geometry("1000x750")

        # Store shipping data
        self.shipping_data = []
        self.current_index = 0
        
        # Create main frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create data display/edit frame
        self.data_frame = ttk.LabelFrame(main_frame, text="Shipping Data", padding="10")
        self.data_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create entry fields
        self.entries = {}
        
        # Define fields to display
        self.fields = [
            "full_name", "first_name", "last_name",
            "street_1", "street_number", "street_2",
            "ship_city", "ship_state", "ship_zipcode", "ship_country",
            "email", "phone", "buyer"
        ]

        # Editable defaults (weight/dimensions)
        self.default_values = {
            "weight_kg":   "0,49",
            "length_cm":   "21",
            "width_cm":    "28",
            "height_cm":   "12",
            "customs_qty": "2"
        }

        # Sender's email for ELTA login (fixed)
        self.sender_email = "math4econ@gmail.com"
        
        # Create entry fields for CSV data
        row = 0
        for field in self.fields:
            ttk.Label(self.data_frame, text=field.replace('_', ' ').title() + ":").grid(
                row=row, column=0, sticky=tk.W, padx=5, pady=2)
            
            self.entries[field] = ttk.Entry(self.data_frame, width=50)
            self.entries[field].grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
            row += 1
        
        # Create entry fields for default data
        for field, value in self.default_values.items():
            ttk.Label(self.data_frame, text=field.replace('_', ' ').title() + ":").grid(
                row=row, column=0, sticky=tk.W, padx=5, pady=2)
            
            self.entries[field] = ttk.Entry(self.data_frame, width=50)
            self.entries[field].grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
            self.entries[field].insert(0, value)
            row += 1
        
        # Add print label checkbox
        self.print_label_var = tk.BooleanVar(value=True)
        self.print_label_check = ttk.Checkbutton(
            self.data_frame, 
            text="Print Label?", 
            variable=self.print_label_var
        )
        self.print_label_check.grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=5, pady=10)
        
        # Navigation buttons
        nav_frame = ttk.Frame(main_frame)
        nav_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(nav_frame, text="Previous", command=self.prev_record).pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="Next", command=self.next_record).pack(side=tk.LEFT, padx=5)
        
        # Status label
        self.status_var = tk.StringVar()
        ttk.Label(nav_frame, textvariable=self.status_var).pack(side=tk.LEFT, padx=20)
        
        # Action buttons
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(action_frame, text="Start Processing", command=self.start_processing).pack(side=tk.RIGHT, padx=5)
        ttk.Button(action_frame, text="Save Changes", command=self.save_changes).pack(side=tk.RIGHT, padx=5)
        
        # Load orders from HTML file
        self.load_orders()

    def load_orders(self):
        """Load orders from Etsy HTML file."""
        try:
            self.shipping_data = load_orders_from_html(self.filepath)

            # Add weight/dimension defaults
            for r in self.shipping_data:
                for k, v in self.default_values.items():
                    r.setdefault(k, v)

            # Filter USA if needed
            if not self.include_usa:
                n_before = len(self.shipping_data)
                self.shipping_data = [r for r in self.shipping_data
                                      if r.get('ship_country', '') not in USA_COUNTRY_VALUES]
                skipped = n_before - len(self.shipping_data)
                if skipped:
                    print(f"ℹ Skipping {skipped} USA order(s)")

            # Check customer DB — offer to use stored address for known customers
            db = load_customer_db()
            for record in self.shipping_data:
                key = customer_db_key(record)
                if key and key in db:
                    stored = db[key]
                    addr_summary = (
                        f"{stored.get('street_1', '')} {stored.get('street_number', '')}, "
                        f"{stored.get('ship_zipcode', '')} {stored.get('ship_city', '')}, "
                        f"{stored.get('ship_country', '')}"
                    )
                    use_stored = messagebox.askyesno(
                        "Previous Address Found",
                        f"Previous address found for {record['full_name']}:\n\n"
                        f"{addr_summary}\n\nUse it?"
                    )
                    if use_stored:
                        for field in ('street_1', 'street_number', 'street_2',
                                      'ship_city', 'ship_state', 'ship_zipcode', 'ship_country'):
                            if stored.get(field) is not None:
                                record[field] = stored[field]
                        print(f"✓ Using stored address for {record['full_name']}")

            # Data check log
            print(f"\n{'='*75}")
            print(f"LOADED {len(self.shipping_data)} ORDERS:")
            print(f"{'#':<4} {'Name':<26} {'Email':<30} {'Street':<28} {'No.':<5} {'ZIP':<8} {'City':<18} {'Country'}")
            print(f"{'-'*4} {'-'*26} {'-'*30} {'-'*28} {'-'*5} {'-'*8} {'-'*18} {'-'*12}")
            for i, r in enumerate(self.shipping_data, 1):
                name = f"{r.get('first_name','')} {r.get('last_name','')}".strip()
                print(f"{i:<4} {name:<26} {r.get('email',''):<30} {r.get('street_1',''):<28} "
                      f"{r.get('street_number',''):<5} {r.get('ship_zipcode',''):<8} "
                      f"{r.get('ship_city',''):<18} {r.get('ship_country','')}")
            print(f"{'='*75}\n")

            if self.shipping_data:
                self.display_record(0)
                self.status_var.set(f"Record 1 of {len(self.shipping_data)}")
            else:
                messagebox.showwarning("No Orders", "No orders found in the file.")

        except Exception as e:
            messagebox.showerror("Error Loading Orders", f"Error: {str(e)}")
    
    def display_record(self, index):
        """Display record at the given index"""
        if 0 <= index < len(self.shipping_data):
            # Clear existing entries
            for field in self.entries:
                self.entries[field].delete(0, tk.END)
            
            # Populate with data
            record = self.shipping_data[index]
            for field in self.entries:
                if field in record and record[field]:
                    self.entries[field].insert(0, record[field])
            
            # Set checkbox
            self.print_label_var.set(record.get("print_label", True))
            
            self.current_index = index
    
    def save_changes(self):
        """Save changes to the current record"""
        if 0 <= self.current_index < len(self.shipping_data):
            record = self.shipping_data[self.current_index]
            
            # Update with values from entries
            for field in self.entries:
                record[field] = self.entries[field].get()
            
            # Update print label flag
            record["print_label"] = self.print_label_var.get()
            
            # No messagebox here - we'll handle feedback in the navigation methods
    
    def next_record(self):
        """Move to the next record"""
        if self.current_index < len(self.shipping_data) - 1:
            self.save_changes()
            
            # Show a temporary message that disappears after 0.3 seconds
            self.status_var.set("Changes saved!")
            self.root.update()  # Force update to show message
            self.root.after(300, lambda: self.update_status_after_save())
            
            self.display_record(self.current_index + 1)
    
    def update_status_after_save(self):
        """Update the status bar after saving changes"""
        self.status_var.set(f"Record {self.current_index + 1} of {len(self.shipping_data)}")
    
    def prev_record(self):
        """Move to the previous record"""
        if self.current_index > 0:
            self.save_changes()
            
            # Show a temporary message that disappears after 0.3 seconds
            self.status_var.set("Changes saved!")
            self.root.update()  # Force update to show message
            self.root.after(300, lambda: self.update_status_after_save())
            
            self.display_record(self.current_index - 1)
    
    def start_processing(self):
        """Start the ELTA automation process"""
        # Save current changes
        self.save_changes()
        
        # Filter records where print_label is True
        to_process = [r for r in self.shipping_data if r.get("print_label", True)]
        
        if not to_process:
            messagebox.showwarning("No Labels", "No records selected for label printing.")
            return
        
        messagebox.showinfo("Processing", f"Starting ELTA automation for {len(to_process)} labels.")
        
        # Start the ELTA automation
        self.root.destroy()  # Close the tkinter window
        process_elta_labels(to_process, self.sender_email, generate_letters=(self.mode == 'both'))

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
        process_all_records(shipping_records, driver)

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        # Save screenshot for debugging
        safe_screenshot(driver, "error_screenshot.png")

    finally:
        # Clean up
        driver.quit()
        print("Browser closed.")

def process_all_records(shipping_records, driver):
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

            # Save this customer's address to the DB for future orders
            try:
                db = load_customer_db()
                key = customer_db_key(record)
                if key:
                    db[key] = {k: record.get(k, '') for k in (
                        'full_name', 'first_name', 'last_name',
                        'street_1', 'street_number', 'street_2',
                        'ship_city', 'ship_state', 'ship_zipcode', 'ship_country', 'email'
                    )}
                    save_customer_db(db)
                    print(f"✓ Saved address for {record['full_name']} to customer DB")
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
            "Όνομα":        "RecipientFirstName",
            "Επώνυμο":      "RecipientLastName",
            "Όνομα Οδού":   "RecipientStreetName",
            "Αρ. Οδού":     "RecipientStreetNumber",
            "Ταχ. Κώδικας": "RecipientPostalCode",
            "Πόλη":         "RecipientTown",
            "E-Mail":       "RecipientEmail",
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
        os.rename(latest_pdf, new_path)
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
    print("Starting main execution block...")
    try:
        # 1. Pick the orders file
        filepath = ask_for_orders_file()

        # 2. Ask what to do
        mode = ask_mode()

        if mode == 'letters':
            # Letters-only: no browser needed
            records = load_orders_from_html(filepath)
            # Filter out USA if desired (USA orders rarely get thank-you notes via ELTA)
            non_usa = [r for r in records if r.get('ship_country', '') not in USA_COUNTRY_VALUES]
            print(f"\nGenerating thank-you letters for {len(non_usa)} record(s)...")
            for record in non_usa:
                try:
                    generate_thank_you(record)
                except Exception as e:
                    print(f"⚠ Letter failed for {record.get('full_name', '?')}: {e}")
            print("\nDone. Letters saved to", OUTPUT_DIR)
        else:
            # Labels (+ optional letters)
            include_usa = ask_yes_no("Shall I create labels for USA orders too?")

            root = tk.Tk()
            app = EltaShippingApp(root, filepath=filepath, include_usa=include_usa, mode=mode)
            root.mainloop()
            print("Mainloop finished")
    except Exception as e:
        print(f"Error occurred: {e}")
        import traceback
        traceback.print_exc()
else:
    print(f"Script imported as module with name: {__name__}")