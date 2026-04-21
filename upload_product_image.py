import requests
import re
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

ADMIN_BASE = "https://alegro.gr/admin875fdclzkf27m3shsg9"
IMAGE_PATH = os.path.expanduser("~/Downloads/perouka-athanasios-diakos-hrwas-epanastasis-1821-wig-athanassios-diakos-hero-greek-revolution-black-male-wavy-long-wig.png")
PRODUCT_ID = 268

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})

def get_token(text):
    m = re.search(r"var token = '([^']+)'", text)
    if m: return m.group(1)
    m = re.search(r'token["\s]*[:=]["\s]*([A-Za-z0-9._\-]{30,})', text)
    return m.group(1) if m else ""

# Login
print("[1] Logging in...")
r = session.get(ADMIN_BASE + "/login")
form_token = re.search(r'name="_token"\s+value="([^"]+)"', r.text).group(1)
r = session.post(ADMIN_BASE + "/login", data={
    "email": "damoncollective@gmail.com",
    "passwd": "cultivatesandspreadslove13579!",
    "stay_logged_in": "0",
    "_token": form_token,
    "submitLogin": "1"
}, allow_redirects=True)
print("    Logged in:", "login" not in r.url)

# Get token from dashboard page
token = get_token(r.text)
if not token:
    m = re.search(r"_token=([A-Za-z0-9._\-]{30,})", r.url)
    token = m.group(1) if m else ""
print("    Token:", token[:50])

# Get product edit page to extract image upload URL/params
print(f"[2] Getting product {PRODUCT_ID} edit page...")
r2 = session.get(ADMIN_BASE + "/index.php", params={
    "controller": "AdminProducts",
    "id_product": PRODUCT_ID,
    "updateproduct": "1",
    "token": token,
})
print("    Status:", r2.status_code, "Size:", len(r2.text))

# Refresh token from edit page
t2 = get_token(r2.text)
if t2: token = t2
print("    Refreshed token:", token[:50])

# Find all image/upload related URLs in the page
upload_patterns = re.findall(r'(?:upload|addImage|add_image|image)[^"\']{0,200}', r2.text, re.I)
for p in upload_patterns[:5]:
    if "url" in p.lower() or "action" in p.lower() or "http" in p.lower():
        print("    Upload hint:", p[:150])

# Find dropzone or file input fields
dropzone = re.findall(r'dropzone[^<]{0,300}', r2.text, re.I)
for d in dropzone[:3]:
    print("    Dropzone:", d[:200])

# Look for the PS9 image upload route
img_routes = re.findall(r"/admin875fdclzkf27m3shsg9/[^\"' ]{5,100}(?:image|upload|photo)[^\"' ]{0,50}", r2.text, re.I)
print("    Image routes:", img_routes[:5])

# Read the image
with open(IMAGE_PATH, "rb") as f:
    img = f.read()
fname = os.path.basename(IMAGE_PATH)
print(f"\n[3] Uploading {fname} ({len(img):,} bytes)...")

# Try multiple upload methods
methods = [
    # Method 1: PS9 new route with 'file'
    {
        "url": f"{ADMIN_BASE}/index.php/sell/catalog/products/{PRODUCT_ID}/images",
        "params": {"_token": token},
        "field": "file",
    },
    # Method 2: PS9 new route with 'files[]'
    {
        "url": f"{ADMIN_BASE}/index.php/sell/catalog/products/{PRODUCT_ID}/images",
        "params": {"_token": token},
        "field": "files[]",
    },
    # Method 3: Legacy addImage with 'file'
    {
        "url": f"{ADMIN_BASE}/index.php",
        "params": {"controller": "AdminProducts", "id_product": PRODUCT_ID, "token": token, "action": "addImage", "ajax": "1"},
        "field": "file",
    },
    # Method 4: Legacy addImage with 'files[]'
    {
        "url": f"{ADMIN_BASE}/index.php",
        "params": {"controller": "AdminProducts", "id_product": PRODUCT_ID, "token": token, "action": "addImage", "ajax": "1"},
        "field": "files[]",
    },
    # Method 5: Prestools image upload if installed
    {
        "url": f"{ADMIN_BASE}/index.php",
        "params": {"controller": "AdminProducts", "id_product": PRODUCT_ID, "token": token, "action": "addImage", "ajax": "1"},
        "field": "image",
        "extra_data": {"id_product": str(PRODUCT_ID)},
    },
]

for i, m in enumerate(methods, 1):
    field = m["field"]
    extra = m.get("extra_data", {})
    files = {field: (fname, img, "image/png")}
    resp = session.post(
        m["url"],
        params=m["params"],
        files=files,
        data=extra,
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    result = resp.text[:200].strip()
    print(f"    Method {i} ({field}): status={resp.status_code} -> {result}")
    if resp.status_code in (200, 201) and ("error" not in result.lower() or result.strip().lstrip("-").isdigit()):
        if result.strip().lstrip("-").isdigit() and int(result.strip()) > 0:
            print(f"\n[OK] Image uploaded! Image ID: {result.strip()}")
            break
        elif "success" in result.lower():
            print(f"\n[OK] Image uploaded successfully!")
            break
