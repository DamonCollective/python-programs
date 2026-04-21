#!/usr/bin/env python3
"""
Create Kapodistrias Wig product on alegro.gr (PrestaShop 9)
and upload all 15 product images.

Run: python create_kapodistrias.py
"""

import requests
import re
import os
import sys
import json
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# ── Configuration ──────────────────────────────────────────────────────────────
ADMIN_BASE = "https://alegro.gr/admin875fdclzkf27m3shsg9"
EMAIL      = "damoncollective@gmail.com"
PASSWORD   = "cultivatesandspreadslove13579" + chr(33)   # chr(33) = !

# Product data
REFERENCE = "KAPO-2026"
PRICE     = "24.900000"   # PrestaShop uses 6 decimal places

NAME_EN = "Ioannis Kapodistrias Theatrical Wig | Reenactment Stage Wig | Made in Greece"
NAME_EL = "Περούκα Ιωάννης Καποδίστριας | Θεατρική Ιστορική Περούκα | Κατασκευή Ελλάδα"

SHORT_EN = (
    "Theatrical stage wig inspired by the 2026 film Kapodistrias by Ioannis Smaragdis. "
    "Voluminous silver-grey curls. Handcrafted in Greece by Alegro."
)
SHORT_EL = (
    "Θεατρική περούκα εμπνευσμένη από την ταινία Καποδίστριας 2026 του Ι. Σμαράγδη. "
    "Πλούσιες ασημόγκριζες μπούκλες. Κατασκευή στην Ελλάδα από την Alegro."
)

DESC_EN = (
    "<p>The <strong>Ioannis Kapodistrias Theatrical Wig</strong> is a stage-quality wig that "
    "faithfully recreates the iconic look of Greece's first Governor, as seen in the 2026 epic "
    "film <em>Kapodistrias</em> directed by Ioannis Smaragdis. Featuring voluminous silver-grey "
    "curls in authentic 18th\u201319th century aristocratic style, this wig is the ideal choice for "
    "theatre productions, historical reenactments, carnival costumes, and period film or TV "
    "productions.</p>"
    "<p>Handcrafted in Greece by <strong>Alegro</strong>, with over 45 years of professional "
    "wig-making expertise. One size fits most adults.</p>"
    "<ul>"
    "<li>Color: Silver-grey with dark undertones</li>"
    "<li>Style: Voluminous curls, mid-length</li>"
    "<li>Inspired by the film Kapodistrias (2026) \u2013 Ioannis Smaragdis</li>"
    "<li>Ideal for: theatre, reenactment, carnival, film/TV</li>"
    "<li>Made in Greece</li>"
    "</ul>"
)

DESC_EL = (
    "<p>H <strong>\u03b8\u03b5\u03b1\u03c4\u03c1\u03b9\u03ba\u03ae \u03c0\u03b5\u03c1\u03bf\u03cd\u03ba\u03b1 \u0399\u03c9\u03ac\u03bd\u03bd\u03b7\u03c2 \u039a\u03b1\u03c0\u03bf\u03b4\u03af\u03c3\u03c4\u03c1\u03b9\u03b1\u03c2</strong> "
    "\u03b5\u03af\u03bd\u03b1\u03b9 \u03bc\u03b9\u03b1 \u03c0\u03b5\u03c1\u03bf\u03cd\u03ba\u03b1 \u03b5\u03c0\u03b1\u03b3\u03b3\u03b5\u03bb\u03bc\u03b1\u03c4\u03b9\u03ba\u03ae\u03c2 "
    "\u03c0\u03bf\u03b9\u03cc\u03c4\u03b7\u03c4\u03b1\u03c2 \u03c0\u03bf\u03c5 \u03b1\u03bd\u03b1\u03c0\u03b1\u03c1\u03ac\u03b3\u03b5\u03b9 \u03bc\u03b5 \u03c0\u03b9\u03c3\u03c4\u03cc\u03c4\u03b7\u03c4\u03b1 "
    "\u03c4\u03bf \u03b5\u03bc\u03b2\u03bb\u03b7\u03bc\u03b1\u03c4\u03b9\u03ba\u03cc look \u03c4\u03bf\u03c5 \u03c0\u03c1\u03ce\u03c4\u03bf\u03c5 \u039a\u03c5\u03b2\u03b5\u03c1\u03bd\u03ae\u03c4\u03b7 "
    "\u03c4\u03b7\u03c2 \u0395\u03bb\u03bb\u03ac\u03b4\u03b1\u03c2, \u03cc\u03c0\u03c9\u03c2 \u03b5\u03bc\u03c6\u03b1\u03bd\u03af\u03b6\u03b5\u03c4\u03b1\u03b9 \u03c3\u03c4\u03b7\u03bd \u03b5\u03c0\u03b9\u03ba\u03ae "
    "\u03c4\u03b1\u03b9\u03bd\u03af\u03b1 \u00ab<em>\u039a\u03b1\u03c0\u03bf\u03b4\u03af\u03c3\u03c4\u03c1\u03b9\u03b1\u03c2</em>\u00bb 2026 "
    "\u03c4\u03bf\u03c5 \u03c3\u03ba\u03b7\u03bd\u03bf\u03b8\u03ad\u03c4\u03b7 \u0399\u03c9\u03ac\u03bd\u03bd\u03b7 \u03a3\u03bc\u03b1\u03c1\u03ac\u03b3\u03b4\u03b7. "
    "\u03a0\u03bb\u03bf\u03cd\u03c3\u03b9\u03b5\u03c2 \u03b1\u03c3\u03b7\u03bc\u03cc\u03b3\u03ba\u03c1\u03b9\u03b6\u03b5\u03c2 \u03bc\u03c0\u03bf\u03cd\u03ba\u03bb\u03b5\u03c2 "
    "\u03c3\u03b5 \u03b1\u03c1\u03b9\u03c3\u03c4\u03bf\u03ba\u03c1\u03b1\u03c4\u03b9\u03ba\u03cc \u03cd\u03c6\u03bf\u03c2 18\u03bf\u03c5\u201319\u03bf\u03c5 \u03b1\u03b9\u03ce\u03bd\u03b1.</p>"
    "<p>\u039a\u03b1\u03c4\u03b1\u03c3\u03ba\u03b5\u03c5\u03ae \u03c3\u03c4\u03b7\u03bd \u0395\u03bb\u03bb\u03ac\u03b4\u03b1 \u03b1\u03c0\u03cc \u03c4\u03b7\u03bd "
    "<strong>Alegro</strong>, \u03bc\u03b5 \u03c0\u03ac\u03bd\u03c9 \u03b1\u03c0\u03cc 45 \u03c7\u03c1\u03cc\u03bd\u03b9\u03b1 "
    "\u03b5\u03bc\u03c0\u03b5\u03b9\u03c1\u03af\u03b1\u03c2. \u0388\u03bd\u03b1 \u03bc\u03ad\u03b3\u03b5\u03b8\u03bf\u03c2 \u03b3\u03b9\u03b1 \u03cc\u03bb\u03bf\u03c5\u03c2.</p>"
    "<ul>"
    "<li>\u03a7\u03c1\u03ce\u03bc\u03b1: \u0391\u03c3\u03b7\u03bc\u03cc\u03b3\u03ba\u03c1\u03b9\u03b6\u03bf \u03bc\u03b5 \u03c3\u03ba\u03bf\u03cd\u03c1\u03b5\u03c2 \u03c1\u03af\u03b6\u03b5\u03c2</li>"
    "<li>\u03a3\u03c4\u03c5\u03bb: \u03a0\u03bb\u03bf\u03cd\u03c3\u03b9\u03b5\u03c2 \u03bc\u03c0\u03bf\u03cd\u03ba\u03bb\u03b5\u03c2, \u03bc\u03b5\u03c3\u03b1\u03af\u03bf \u03bc\u03ae\u03ba\u03bf\u03c2</li>"
    "<li>\u0395\u03bc\u03c0\u03bd\u03b5\u03c5\u03c3\u03bc\u03ad\u03bd\u03b7 \u03b1\u03c0\u03cc \u03c4\u03b7\u03bd \u03c4\u03b1\u03b9\u03bd\u03af\u03b1 \u039a\u03b1\u03c0\u03bf\u03b4\u03af\u03c3\u03c4\u03c1\u03b9\u03b1\u03c2 (2026)</li>"
    "<li>\u0399\u03b4\u03b1\u03bd\u03b9\u03ba\u03ae \u03b3\u03b9\u03b1: \u03b8\u03ad\u03b1\u03c4\u03c1\u03bf, reenactment, \u03b1\u03c0\u03bf\u03ba\u03c1\u03b9\u03ad\u03c2, \u03ba\u03b9\u03bd\u03b7\u03bc\u03b1\u03c4\u03bf\u03b3\u03c1\u03ac\u03c6\u03bf/TV</li>"
    "<li>\u039a\u03b1\u03c4\u03b1\u03c3\u03ba\u03b5\u03c5\u03ae \u03c3\u03c4\u03b7\u03bd \u0395\u03bb\u03bb\u03ac\u03b4\u03b1</li>"
    "</ul>"
)

META_TITLE_EN = "Ioannis Kapodistrias Theatrical Wig | Made in Greece | Alegro"
META_TITLE_EL = "\u03a0\u03b5\u03c1\u03bf\u03cd\u03ba\u03b1 \u039a\u03b1\u03c0\u03bf\u03b4\u03af\u03c3\u03c4\u03c1\u03b9\u03b1\u03c2 | \u0398\u03b5\u03b1\u03c4\u03c1\u03b9\u03ba\u03ae \u0399\u03c3\u03c4\u03bf\u03c1\u03b9\u03ba\u03ae | Alegro"
META_DESC_EN  = ("Buy the Ioannis Kapodistrias theatrical wig as seen in the 2026 film by "
                 "Ioannis Smaragdis. Silver-grey curls, made in Greece by Alegro.")
META_DESC_EL  = ("\u0391\u03b3\u03bf\u03c1\u03ac\u03c3\u03c4\u03b5 \u03c4\u03b7\u03bd \u03c0\u03b5\u03c1\u03bf\u03cd\u03ba\u03b1 \u039a\u03b1\u03c0\u03bf\u03b4\u03af\u03c3\u03c4\u03c1\u03b9\u03b1\u03c2 \u03b1\u03c0\u03cc \u03c4\u03b7\u03bd \u03c4\u03b1\u03b9\u03bd\u03af\u03b1 2026. "
                 "\u0391\u03c3\u03b7\u03bc\u03cc\u03b3\u03ba\u03c1\u03b9\u03b6\u03b5\u03c2 \u03bc\u03c0\u03bf\u03cd\u03ba\u03bb\u03b5\u03c2, \u03ba\u03b1\u03c4\u03b1\u03c3\u03ba\u03b5\u03c5\u03ae \u03c3\u03c4\u03b7\u03bd \u0395\u03bb\u03bb\u03ac\u03b4\u03b1 \u03b1\u03c0\u03cc \u03c4\u03b7\u03bd Alegro.")
LINK_EN = "ioannis-kapodistrias-theatrical-wig-reenactment-stage-wig"
LINK_EL = "perouka-ioannis-kapodistrias-theatriki-istoriki-perouka"

# ── Images: John photos first (cover), then doll-head views ───────────────────
DOWNLOADS = str(Path.home() / "Downloads")
all_imgs  = sorted([
    os.path.join(DOWNLOADS, f)
    for f in os.listdir(DOWNLOADS)
    if f.startswith("Kapodistrias") and f.endswith(".png")
])
john_imgs = [p for p in all_imgs if "John" in os.path.basename(p)]
doll_imgs = [p for p in all_imgs if "doll" in os.path.basename(p)]
IMAGES    = john_imgs + doll_imgs

print(f"Images to upload: {len(IMAGES)}")
for i, p in enumerate(IMAGES, 1):
    print(f"  {i:02d}. {os.path.basename(p)}")

# ── Session ────────────────────────────────────────────────────────────────────
session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})


def extract_url_token(url):
    m = re.search(r'[?&]_?token=([A-Za-z0-9._\-]+)', url)
    return m.group(1) if m else None


# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — Login
# ══════════════════════════════════════════════════════════════════════════════
print("\n[1] Logging in...")
r = session.get(f"{ADMIN_BASE}/login")
ft = re.search(r'name="_token"\s+value="([^"]+)"', r.text).group(1)
r = session.post(f"{ADMIN_BASE}/login", data={
    "email": EMAIL, "passwd": PASSWORD,
    "stay_logged_in": "0", "_token": ft, "submitLogin": "1",
}, allow_redirects=True)

if "login" in r.url:
    print("  [ERROR] Login failed!")
    sys.exit(1)

legacy_token = extract_url_token(r.url)
print(f"  OK — {r.url[:80]}")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — Get the create product form and its token
# ══════════════════════════════════════════════════════════════════════════════
print("\n[2] Fetching product catalog to get create URL...")
r2 = session.get(f"{ADMIN_BASE}/index.php",
                  params={"controller": "AdminProducts", "token": legacy_token},
                  allow_redirects=True)
create_tok_m = re.search(r'/products/create\?_token=([A-Za-z0-9._\-]+)', r2.text)
if not create_tok_m:
    print("  [ERROR] Could not find create product link in catalog page!")
    sys.exit(1)
create_token = create_tok_m.group(1)
print(f"  Create token: {create_token[:60]}")

# Fetch create page to get form _token
r3 = session.get(f"{ADMIN_BASE}/index.php/sell/catalog/products/create",
                  params={"_token": create_token}, allow_redirects=True)
page_token = extract_url_token(r3.url) or create_token

# Extract the form token (hidden input create_product[_token])
form_tok_m = re.search(r'name="create_product\[_token\]"\s+value="([^"]+)"', r3.text)
form_token = form_tok_m.group(1) if form_tok_m else page_token
shop_id_m  = re.search(r'name="create_product\[shop_id\]"\s+value="([^"]+)"', r3.text)
shop_id    = shop_id_m.group(1) if shop_id_m else "1"
print(f"  Form token: {form_token[:60]}")
print(f"  Shop ID: {shop_id}")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — Create the minimal product (POST the create form)
# ══════════════════════════════════════════════════════════════════════════════
print("\n[3] Creating product (step 1 — initial save)...")
r_create = session.post(
    f"{ADMIN_BASE}/index.php/sell/catalog/products/create",
    params={"_token": page_token},
    data={
        "create_product[shop_id]": shop_id,
        "create_product[_token]":  form_token,
    },
    headers={"Referer": r3.url},
    allow_redirects=True,
)
print(f"  Response: {r_create.status_code} → {r_create.url[:100]}")

# Extract new product ID from redirect
pid_m = (
    re.search(r'/products/(\d+)/edit', r_create.url)
    or re.search(r'/products/(\d+)', r_create.url)
    or re.search(r'id_product=(\d+)', r_create.url)
)
if not pid_m:
    print("  [ERROR] Product created but ID not found in redirect URL.")
    print("  Full URL:", r_create.url)
    sys.exit(1)

PRODUCT_ID = int(pid_m.group(1))
print(f"  Product created! ID = {PRODUCT_ID}")
print(f"  Edit URL: {ADMIN_BASE}/index.php/sell/catalog/products/{PRODUCT_ID}/edit")

# Update token from the edit page redirect
edit_page_token = extract_url_token(r_create.url) or page_token

# ══════════════════════════════════════════════════════════════════════════════
# STEP 4 — Save full product data (name, price, description, SEO, reference)
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n[4] Saving product details...")

# Fetch the edit page to extract fresh tokens and language IDs
r_edit = session.get(
    f"{ADMIN_BASE}/index.php/sell/catalog/products/{PRODUCT_ID}/edit",
    params={"_token": edit_page_token},
    allow_redirects=True,
)
edit_url_token = extract_url_token(r_edit.url) or edit_page_token

# Extract form _token from edit page
edit_ft_m = re.search(r'name="product\[_token\]"\s+value="([^"]+)"', r_edit.text)
if not edit_ft_m:
    edit_ft_m = re.search(r'data-token="([^"]+)"', r_edit.text)
edit_form_token = edit_ft_m.group(1) if edit_ft_m else edit_url_token

# Detect language IDs (look for en/el in lang JSON blobs)
lang_ids = {"en": 1, "el": 2}  # fallback defaults
lang_hits = re.findall(r'"id"\s*:\s*(\d+)[^}]{0,120}"iso_code"\s*:\s*"([^"]+)"', r_edit.text)
for lid, iso in lang_hits:
    if iso.lower() == "en":
        lang_ids["en"] = int(lid)
    elif iso.lower() in ("el", "gr"):
        lang_ids["el"] = int(lid)
print(f"  Language IDs: EN={lang_ids['en']}, EL={lang_ids['el']}")

en, el = lang_ids["en"], lang_ids["el"]

product_payload = {
    # Names
    f"product[header][name][{en}]": NAME_EN,
    f"product[header][name][{el}]": NAME_EL,
    f"product[header][active]": "1",
    # Pricing
    f"product[pricing][retail_price][price_tax_excluded]": PRICE,
    # Descriptions
    f"product[description][description][{en}]":       DESC_EN,
    f"product[description][description][{el}]":       DESC_EL,
    f"product[description][description_short][{en}]": SHORT_EN,
    f"product[description][description_short][{el}]": SHORT_EL,
    # SEO
    f"product[seo][meta_title][{en}]":       META_TITLE_EN,
    f"product[seo][meta_title][{el}]":       META_TITLE_EL,
    f"product[seo][meta_description][{en}]": META_DESC_EN,
    f"product[seo][meta_description][{el}]": META_DESC_EL,
    f"product[seo][link_rewrite][{en}]":     LINK_EN,
    f"product[seo][link_rewrite][{el}]":     LINK_EL,
    # Reference
    f"product[specifics][reference]": REFERENCE,
    # CSRF
    "product[_token]": edit_form_token,
    "_token":          edit_url_token,
}

r_save = session.post(
    f"{ADMIN_BASE}/index.php/sell/catalog/products/{PRODUCT_ID}/edit",
    params={"_token": edit_url_token},
    data=product_payload,
    headers={"Referer": r_edit.url},
    allow_redirects=True,
)
print(f"  Save response: {r_save.status_code} → {r_save.url[:100]}")

# Check for errors in response
if "error" in r_save.text.lower() and r_save.status_code != 200:
    print("  [WARN] Possible save error. Snippet:", r_save.text[:300])
else:
    print("  Details saved OK.")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 5 — Upload all 15 images
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n[5] Uploading {len(IMAGES)} images to product {PRODUCT_ID}...")

# Refresh from current edit page
r_edit2 = session.get(
    f"{ADMIN_BASE}/index.php/sell/catalog/products/{PRODUCT_ID}/edit",
    params={"_token": edit_url_token},
    allow_redirects=True,
)
img_url_token = extract_url_token(r_edit2.url) or edit_url_token
img_dt_m = (
    re.search(r'data-form-name="product_image"[^>]*data-token="([^"]+)"', r_edit2.text)
    or re.search(r'data-token="([^"]+)"', r_edit2.text)
)
img_data_token = img_dt_m.group(1) if img_dt_m else img_url_token
print(f"  Image data token: {img_data_token[:60]}")

UPLOAD_URL = f"{ADMIN_BASE}/index.php/sell/catalog/products/images/add"
uploaded, errors = [], []

for i, img_path in enumerate(IMAGES, 1):
    fname = os.path.basename(img_path)
    with open(img_path, "rb") as fh:
        raw = fh.read()

    label = fname[:65] + ("..." if len(fname) > 65 else "")
    print(f"  [{i:02d}/{len(IMAGES)}] {label} ({len(raw):,} B)")

    resp = session.post(
        UPLOAD_URL,
        params={"_token": img_url_token},
        files={"product_image[file]": (fname, raw, "image/png")},
        data={
            "product_image[product_id]": str(PRODUCT_ID),
            "product_image[_token]":     img_data_token,
        },
        headers={
            "X-Requested-With": "XMLHttpRequest",
            "Referer":          r_edit2.url,
        },
    )

    body = resp.text.strip()
    if resp.status_code in (200, 201):
        try:
            j = json.loads(body)
            if "image_id" in j:
                cover = " \u2190 COVER" if j.get("is_cover") else ""
                print(f"         OK  image_id={j['image_id']}  pos={j.get('position')}{cover}")
                uploaded.append(j["image_id"])
            else:
                print(f"         WARN: {body[:120]}")
                errors.append(fname)
        except json.JSONDecodeError:
            print(f"         WARN (non-JSON): {body[:120]}")
            errors.append(fname)
    else:
        print(f"         ERROR {resp.status_code}: {body[:120]}")
        errors.append(fname)

# ══════════════════════════════════════════════════════════════════════════════
# Summary
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{'═'*60}")
print(f"  Product ID  : {PRODUCT_ID}")
print(f"  Price       : \u20ac24.90")
print(f"  Reference   : {REFERENCE}")
print(f"  Images      : {len(uploaded)}/{len(IMAGES)} uploaded successfully")
if errors:
    print(f"  Failed imgs : {errors}")
print(f"\n  Admin URL   : {ADMIN_BASE}/index.php/sell/catalog/products/{PRODUCT_ID}/edit")
print(f"  Front URL   : https://www.alegro.gr/{LINK_EL}")
print(f"{'═'*60}")
