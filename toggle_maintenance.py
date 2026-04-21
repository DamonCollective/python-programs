import requests
from bs4 import BeautifulSoup
import re
import sys

ADMIN_URL = "https://alegro.gr/admin875fdclzkf27m3shsg9"
EMAIL = "damoncollective@gmail.com"
PASSWORD = "cultivatesandspreadslove13579!"

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})

# Login
login_page = session.get(f"{ADMIN_URL}/index.php?controller=AdminLogin")
soup = BeautifulSoup(login_page.text, "html.parser")
token_input = soup.find("input", {"name": "token"})
token = token_input["value"] if token_input else ""
resp = session.post(f"{ADMIN_URL}/index.php?controller=AdminLogin", data={
    "email": EMAIL, "passwd": PASSWORD, "back": "", "token": token, "submitLogin": "1"
}, allow_redirects=True)
print(f"Logged in: {resp.url[:80]}")

# Get maintenance page
maint_url = f"{ADMIN_URL}/index.php/configure/shop/maintenance/"
maint_resp = session.get(maint_url)
soup_maint = BeautifulSoup(maint_resp.text, "html.parser")

# Find the maintenance form by searching all inputs for "enable_shop"
maint_form = None
for form in soup_maint.find_all("form"):
    form_str = str(form)
    if "enable_shop" in form_str:
        maint_form = form
        break

if not maint_form:
    print("ERROR: Could not find maintenance form")
    print(f"Total forms on page: {len(soup_maint.find_all('form'))}")
    # Dump all input names across all forms
    for i, f in enumerate(soup_maint.find_all("form")):
        print(f"Form {i} inputs: {[inp.get('name') for inp in f.find_all('input')]}")
    sys.exit(1)

# Collect form data
post_data = {}
for inp in maint_form.find_all("input"):
    name = inp.get("name")
    val = inp.get("value", "")
    itype = inp.get("type", "text")
    if not name:
        continue
    if itype == "radio":
        if name not in post_data:
            post_data[name] = val
    else:
        post_data[name] = val

# Set enable_shop = 1 (store ON = maintenance OFF)
post_data["form[enable_shop]"] = "1"

print("Submitting:")
for k, v in post_data.items():
    print(f"  {k} = {(v or '')[:60]}")

resp2 = session.post(maint_resp.url, data=post_data)
print(f"\nResponse: {resp2.status_code} -> {resp2.url[:80]}")

# Verify
verify = session.get(maint_url)
soup_v = BeautifulSoup(verify.text, "html.parser")
for inp in soup_v.find_all("input"):
    if "enable_shop" in (inp.get("name") or ""):
        if inp.get("checked"):
            val = inp.get("value")
            print(f"Verified: enable_shop = {val} -> {'Shop ENABLED (maintenance OFF)' if val == '1' else 'Shop DISABLED (maintenance ON)'}")
