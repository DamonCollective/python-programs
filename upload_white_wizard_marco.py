#!/usr/bin/env python3
"""
Upload 3 white wizard images (model Marco) to product 383 on alegro.gr.
Product: Σετ Περούκα και Γενειάδα Λευκού Μάγου
"""

import requests, re, os, sys, json, io
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

ADMIN_BASE = "https://alegro.gr/admin875fdclzkf27m3shsg9"
EMAIL      = "damoncollective@gmail.com"
PASSWORD   = "cultivatesandspreadslove13579" + chr(33)
PRODUCT_ID = 383
MAX_BYTES  = 2_000_000

DOWNLOADS = os.path.expanduser("~/Downloads")
IMAGE_PATHS = [
    os.path.join(DOWNLOADS, "white-wizard-on-model-marco.png"),
    os.path.join(DOWNLOADS, "white-wizard-prophet-wig-and-beard-on-model-marco.png"),
    os.path.join(DOWNLOADS, "white-wizard-prophet-wig-and-beard-on-model-marco-white-bg.png"),
]


def compress_image(path, max_bytes):
    img = Image.open(path).convert("RGBA")
    orig_w, orig_h = img.size
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True, compress_level=9)
    if buf.tell() <= max_bytes:
        return buf.getvalue(), buf.tell()
    scale = 0.95
    while scale >= 0.50:
        new_w, new_h = int(orig_w * scale), int(orig_h * scale)
        resized = img.resize((new_w, new_h), Image.LANCZOS)
        buf = io.BytesIO()
        resized.save(buf, format="PNG", optimize=True, compress_level=9)
        if buf.tell() <= max_bytes:
            print(f"      Resized to {scale*100:.0f}% ({new_w}x{new_h}) → {buf.tell():,} B")
            return buf.getvalue(), buf.tell()
        scale -= 0.05
    rgb = img.convert("RGB")
    quality = 90
    while quality >= 60:
        buf = io.BytesIO()
        rgb.save(buf, format="JPEG", quality=quality, optimize=True)
        if buf.tell() <= max_bytes:
            print(f"      Saved as JPEG quality={quality} → {buf.tell():,} B")
            return buf.getvalue(), buf.tell()
        quality -= 5
    raise RuntimeError(f"Could not compress {path} under {max_bytes} bytes")


session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})

print("[1] Logging in...")
r = session.get(f"{ADMIN_BASE}/login")
ft = re.search(r'name="_token"\s+value="([^"]+)"', r.text).group(1)
r = session.post(f"{ADMIN_BASE}/login", data={
    "email": EMAIL, "passwd": PASSWORD,
    "stay_logged_in": "0", "_token": ft, "submitLogin": "1",
}, allow_redirects=True)
if "login" in r.url:
    print("  [ERROR] Login failed!"); sys.exit(1)
legacy_token = re.search(r'[?&]token=([A-Za-z0-9._\-]+)', r.url)
legacy_token = legacy_token.group(1) if legacy_token else ""
print("  Logged in OK")

print("[2] Fetching catalog token...")
r_cat = session.get(f"{ADMIN_BASE}/index.php",
                    params={"controller": "AdminProducts", "token": legacy_token},
                    allow_redirects=True)
cat_token = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r_cat.url).group(1)

print(f"[3] Fetching edit page for product {PRODUCT_ID}...")
r2 = session.get(
    f"{ADMIN_BASE}/index.php/sell/catalog/products/{PRODUCT_ID}/edit",
    params={"_token": cat_token}, allow_redirects=True,
)
url_token = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r2.url).group(1)
img_dt_m = re.search(r'data-form-name="product_image"[^>]*data-token="([^"]+)"', r2.text) or \
           re.search(r'data-token="([^"]+)"[^>]*data-form-name="product_image"', r2.text)
img_data_token = img_dt_m.group(1) if img_dt_m else url_token
print(f"  Edit page size: {len(r2.text):,} bytes")

UPLOAD_URL = f"{ADMIN_BASE}/index.php/sell/catalog/products/images/add"
uploaded, errors = [], []

print(f"\n[4] Uploading {len(IMAGE_PATHS)} images to product {PRODUCT_ID}...")
for i, img_path in enumerate(IMAGE_PATHS, 1):
    fname = os.path.basename(img_path)
    orig_size = os.path.getsize(img_path)
    print(f"\n  [{i}/{len(IMAGE_PATHS)}] {fname}")
    print(f"      Original: {orig_size:,} B")

    try:
        data, final_size = compress_image(img_path, MAX_BYTES)
    except Exception as e:
        print(f"      [ERROR] {e}"); errors.append(fname); continue

    mime = "image/png"
    upload_fname = fname
    if data[:3] == b'\xff\xd8\xff':
        mime = "image/jpeg"
        upload_fname = fname.replace(".png", ".jpg")

    resp = session.post(
        UPLOAD_URL,
        params={"_token": url_token},
        files={"product_image[file]": (upload_fname, data, mime)},
        data={"product_image[product_id]": str(PRODUCT_ID),
              "product_image[_token]": img_data_token},
        headers={"X-Requested-With": "XMLHttpRequest", "Referer": r2.url},
    )
    body = resp.text.strip()
    if resp.status_code in (200, 201):
        try:
            j = json.loads(body)
            if "image_id" in j:
                cover = " ← COVER" if j.get("is_cover") else ""
                print(f"      OK  image_id={j['image_id']}  pos={j.get('position')}{cover}")
                uploaded.append(j["image_id"])
            else:
                print(f"      WARN: {body[:120]}"); errors.append(fname)
        except json.JSONDecodeError:
            print(f"      WARN (non-JSON): {body[:120]}"); errors.append(fname)
    else:
        print(f"      ERROR {resp.status_code}: {body[:120]}"); errors.append(fname)

print(f"\n{'═'*60}")
print(f"  Uploaded: {len(uploaded)}/{len(IMAGE_PATHS)}  IDs: {uploaded}")
if errors: print(f"  Failed:   {errors}")
print(f"{'═'*60}")
