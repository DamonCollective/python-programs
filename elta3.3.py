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
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

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

# Countries that ship to the USA (for filtering)
USA_COUNTRY_VALUES = {"United States", "United States of America", "USA", "US"}

class EltaShippingApp:
    def __init__(self, root, filepath, include_usa=True):
        self.root = root
        self.filepath = filepath
        self.include_usa = include_usa
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
            "weight_kg": "0,49",
            "length_cm": "21",
            "width_cm":  "28",
            "height_cm": "12"
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
        process_elta_labels(to_process, self.sender_email)

def process_elta_labels(shipping_records, sender_email="math4econ@gmail.com"):
    """Process ELTA label creation for the given shipping records"""
    if not shipping_records:
        print("No shipping records to process.")
        return
    
    # Configure Firefox
    options = webdriver.FirefoxOptions()
    options.binary_location = "/snap/firefox/current/usr/lib/firefox/firefox"

    # Initialize WebDriver
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
        
        # Get country from first record
        country = shipping_records[0].get('ship_country', 'United States')
        
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
        
        # Click the Next/Continue button to go to the sender form
        find_and_click_next_button(driver)
        human_delay(2, 3)
        print("Current URL:", driver.current_url)
        
        # --- HANDLE SENDER DATA FORM ---
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

        # Click the Next/Continue button to go to the receiver form
        try:
            # Use the helper function to find and click the Next button
            next_button = find_and_click_next_button(driver)
            
            # Wait for page to change
            current_url = driver.current_url
            WebDriverWait(driver, 10).until(
                lambda d: d.current_url != current_url or len(d.find_elements(By.XPATH, "//div[contains(@class, 'load') or contains(@class, 'progress')]")) == 0
            )
            print("✓ Page updated after clicking Next")
            print("Current URL:", driver.current_url)
        except Exception as e:
            print(f"Could not click Next button: {str(e)}")
            safe_screenshot(driver, "next_button_error.png")
            
            wait_for_user("Please click the Next button manually, then click OK.")
        
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
                
                # Need to select country and service type again for new shipment
                select_country_and_service(driver, record.get('ship_country', 'United States'))
                
                # Click Next to go to sender form
                find_and_click_next_button(driver)

                # Wait for sender fields to be visible
                WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.ID, "SenderFirstName"))
                )

                # Fill sender form again (using the same fixed sender data)
                fill_sender_form(driver)

                # Click Next to go to receiver form
                find_and_click_next_button(driver)

                # Wait specifically for RecipientFirstName to become VISIBLE (not just present)
                WebDriverWait(driver, 15).until(
                    EC.visibility_of_element_located((By.ID, "RecipientFirstName"))
                )
                print("✓ Receiver step is now active")
                
            except Exception as e:
                print(f"Error creating new shipment: {str(e)}")
                safe_screenshot(driver, f"new_shipment_error_{index}.png")
                
                wait_for_user("Please navigate to create a new shipment manually. When at the receiver form, click OK.")
        
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
            "E-Mail": record.get("email", ""),                # Buyer email from Etsy orders page
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
        fill_content_description(driver)

        # Click Next — may land on summary/review page first
        find_and_click_next_button(driver)
        human_delay(1, 2)

        # If there is another Next button (summary step), click it too
        try:
            extra_next = driver.find_elements(By.XPATH,
                "//button[contains(@class,'btn-next')] | //button[contains(text(),'Επόμενο')]")
            if extra_next and extra_next[0].is_displayed():
                driver.execute_script("arguments[0].click();", extra_next[0])
                print("✓ Clicked extra Next (summary step)")
                human_delay(1, 2)
        except Exception:
            pass

        # Print the label
        print_shipping_label(driver, record)

        # Wait before next record
        human_delay(2, 3)

def select_country_and_service(driver, country="United States"):
    """Select country and service type"""
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
        
        # Find and tick the "Gift" checkbox — debug dump to discover its ID
        try:
            all_checkboxes = driver.find_elements(By.XPATH, "//input[@type='checkbox']")
            print(f"Checkboxes on page: {[(c.get_attribute('id'), c.get_attribute('name')) for c in all_checkboxes]}")
            # Try by JS: find any checkbox whose nearby label mentions Gift/Δώρο
            clicked = driver.execute_script("""
                var inputs = document.querySelectorAll('input[type="checkbox"]');
                for (var i = 0; i < inputs.length; i++) {
                    var id = inputs[i].id;
                    var label = document.querySelector('label[for="' + id + '"]');
                    if (!label) label = inputs[i].closest('label');
                    if (label && (label.textContent.includes('Δώρο') || label.textContent.toLowerCase().includes('gift'))) {
                        if (!inputs[i].checked) inputs[i].click();
                        return label.textContent.trim();
                    }
                }
                return null;
            """)
            if clicked:
                print(f"✓ Checked gift checkbox (label: {clicked!r})")
            else:
                print("⚠ Gift checkbox not found — will fix once ID is known")
        except Exception as e:
            print(f"Error checking gift checkbox: {e}")
        
        print("✓ Completed receiver data form")

    except Exception as e:
        print(f"Error filling receiver form: {str(e)}")
        safe_screenshot(driver, "receiver_form_error.png")
        
        wait_for_user("Please fill in the receiver data manually, then click OK.")

def fill_content_description(driver):
    """Fill in the content description form"""
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
                el.value = '2';
                el.dispatchEvent(new Event('input'));
                el.dispatchEvent(new Event('change'));
            }
        """)
        print("✓ Filled ProtectedVoucherDetailQuantity: 2")

        print("✓ Completed content description form")

    except Exception as e:
        print(f"Error filling content description: {str(e)}")
        safe_screenshot(driver, "content_form_error.png")
        wait_for_user("Please fill in the content description manually, then click OK.")

OUTPUT_DIR = os.path.expanduser("~/Documents/ELTA_NEW_PROGRAM")

def rename_latest_pdf(last_name, first_name, tracking_number):
    """Move and rename the most recently downloaded PDF to OUTPUT_DIR/SURNAME_LL123456789GR.pdf"""
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
        tracking_part = f"_{tracking_number}" if tracking_number else ""
        new_name = f"{surname}{tracking_part}.pdf"
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
        # Look for the print/download button (try multiple possible texts)
        print_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH,
                "//button[contains(text(),'Εκτύπωση') or contains(text(),'Λήψη') or contains(text(),'Print') or contains(text(),'Download')]"
                " | //a[contains(text(),'Εκτύπωση') or contains(text(),'Λήψη')]"
                " | //input[@type='button' and (contains(@value,'Εκτύπωση') or contains(@value,'Λήψη'))]"
            ))
        )
        human_delay(0.5, 1.5)
        driver.execute_script("arguments[0].click();", print_button)
        print(f"✓ Clicked print/download button")

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

        # Rename the latest downloaded PDF to LastName_FirstName_tracking.pdf
        rename_latest_pdf(last_name, first_name, tracking_number)

        # Wait for user to handle print dialog / confirm PDF is saved
        wait_for_user(
            f"Label for {first_name} {last_name} — please save/print the PDF,\n"
            f"then click Done to continue with the next label."
        )

    except Exception as e:
        print(f"Error on final screen: {str(e)}")
        wait_for_user(
            f"Cannot find the print/download button.\n"
            f"Please click it manually for {first_name} {last_name},\n"
            f"then click Done to continue."
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

def find_and_click_next_button(driver):
    """Helper function to find and click the Next button using multiple approaches"""
    print("Looking for the Next button...")
    
    # Try multiple approaches to find the Next button
    found_button = False
    
    # Approach 1: Standard button search
    try:
        next_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Επόμενο')] | //input[contains(@value, 'Επόμενο')] | //a[contains(text(), 'Επόμενο')]"))
        )
        human_delay(0.5, 1.5)
        next_button.click()
        print("✓ Clicked the 'Επόμενο' (Next) button")
        found_button = True
        return next_button
    except Exception as e:
        print(f"Standard button search failed: {str(e)}")
    
    # Approach 2: Try to find any button that looks like a "Next" button
    if not found_button:
        try:
            # Look for buttons with common next/continue related classes or attributes
            buttons = driver.find_elements(By.XPATH, "//button[contains(@class, 'next') or contains(@class, 'continue') or contains(@class, 'submit')] | //input[@type='submit']")
            
            if buttons:
                # Click the first button found
                driver.execute_script("arguments[0].scrollIntoView(true);", buttons[0])
                human_delay(0.5, 1)
                buttons[0].click()
                print(f"✓ Clicked button using alternative method (class-based)")
                found_button = True
                return buttons[0]
        except Exception as e:
            print(f"Class-based button search failed: {str(e)}")
    
    # Approach 3: Try using JavaScript to find and click the button
    if not found_button:
        try:
            clicked = driver.execute_script("""
                var buttons = document.getElementsByTagName('button');
                for(var i = 0; i < buttons.length; i++) {
                    if(buttons[i].textContent.includes('Επόμενο') || 
                       buttons[i].id.toLowerCase().includes('next') || 
                       buttons[i].className.toLowerCase().includes('next') ||
                       buttons[i].className.toLowerCase().includes('continue')) {
                        buttons[i].click();
                        return true;
                    }
                }
                
                // Try input buttons too
                var inputs = document.getElementsByTagName('input');
                for(var i = 0; i < inputs.length; i++) {
                    if(inputs[i].type === 'submit' || 
                       inputs[i].value.includes('Επόμενο') || 
                       inputs[i].id.toLowerCase().includes('next')) {
                        inputs[i].click();
                        return true;
                    }
                }
                
                return false;
            """)
            print("✓ Attempted to click Next button using JavaScript")
            found_button = True
            return True
        except Exception as e:
            print(f"JavaScript button search failed: {str(e)}")
    
    # If none of the approaches worked, ask for manual help
    if not found_button:
        wait_for_user("Please click the Next button manually, then click OK.")
        return True

# Main execution block
if __name__ == "__main__":
    print("Starting main execution block...")
    try:
        # 1. Pick the orders file
        filepath = ask_for_orders_file()

        # 2. Ask about USA — both before main window to avoid two-Tk conflict
        include_usa = ask_yes_no("Shall I create labels for USA orders too?")

        # 3. Open main window
        root = tk.Tk()
        app = EltaShippingApp(root, filepath=filepath, include_usa=include_usa)
        root.mainloop()
        print("Mainloop finished")
    except Exception as e:
        print(f"Error occurred: {e}")
        import traceback
        traceback.print_exc()
else:
    print(f"Script imported as module with name: {__name__}")