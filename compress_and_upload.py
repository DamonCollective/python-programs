#!/usr/bin/env python3
"""
Compress oversized images and upload them to product 386 on alegro.gr.
"""

import requests
import re
import os
import sys
import json
import io
from pathlib import Path
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

ADMIN_BASE = "https://alegro.gr/admin875fdclzkf27m3shsg9"
EMAIL      = "damoncollective@gmail.com"
PASSWORD   = "cultivatesandspreadslove13579" + chr(33)
PRODUCT_ID = 386
MAX_BYTES  = 2_000_000   # stay under 2 MB limit

# The 6 images that were too large
DOWNLOADS = str(Path.home() / "Downloads")
FAILED_IMAGES = [
    "Kapodistrias-Wig-Made-in-Greece-Alegro-Ioannis-Kapodistrias-perouka-film-2026-reenactment-wig-John1-enface.png",
    "Kapodistrias-Wig-Made-in-Greece-Alegro-Ioannis-Kapodistrias-perouka-film-2026-reenactment-wig-John2-3-4.png",
    "Kapodistrias-Wig-Made-in-Greece-Alegro-Ioannis-Kapodistrias-perouka-film-2026-reenactment-wig-doll-head (1).png",
    "Kapodistrias-Wig-Made-in-Greece-Alegro-Ioannis-Kapodistrias-perouka-film-2026-reenactment-wig-doll-head (2).png",
    "Kapodistrias-Wig-Made-in-Greece-Alegro-Ioannis-Kapodistrias-perouka-film-2026-reenactment-wig-doll-head (4).png",
    "Kapodistrias-Wig-Made-in-Greece-Alegro-Ioannis-Kapodistrias-perouka-film-2026-reenactment-wig-doll-head (7).png",
]
IMAGE_PATHS = [os.path.join(DOWNLOADS, f) for f in FAILED_IMAGES]


def compress_image(path, max_bytes):
    """
    Try PNG max compression first; if still too large, scale down
    in 5% steps until under max_bytes. Returns (bytes, final_size).
    """
    img = Image.open(path).convert("RGBA")
    orig_w, orig_h = img.size

    # Try max PNG compression first (no resize)
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True, compress_level=9)
    if buf.tell() <= max_bytes:
        return buf.getvalue(), buf.tell()

    # Scale down in 5% steps
    scale = 0.95
    while scale >= 0.50:
        new_w = int(orig_w * scale)
        new_h = int(orig_h * scale)
        resized = img.resize((new_w, new_h), Image.LANCZOS)
        buf = io.BytesIO()
        resized.save(buf, format="PNG", optimize=True, compress_level=9)
        size = buf.tell()
        if size <= max_bytes:
            print(f"      Resized to {scale*100:.0f}%  ({new_w}x{new_h}) → {size:,} B")
            return buf.getvalue(), size
        scale -= 0.05

    # Last resort: save as JPEG at 90% quality
    rgb = img.convert("RGB")
    buf = io.BytesIO()
    quality = 90
    while quality >= 60:
        buf = io.BytesIO()
        rgb.save(buf, format="JPEG", quality=quality, optimize=True)
        if buf.tell() <= max_bytes:
            print(f"      Saved as JPEG quality={quality} → {buf.tell():,} B")
            return buf.getvalue(), buf.tell()
        quality -= 5

    raise RuntimeError(f"Could not compress {path} under {max_bytes} bytes")


# ── Session ────────────────────────────────────────────────────────────────────
session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})

def extract_url_token(url):
    m = re.search(r'[?&]_?token=([A-Za-z0-9._\-]+)', url)
    return m.group(1) if m else None

# ── Login ──────────────────────────────────────────────────────────────────────
print("[1] Logging in...")
r = session.get(f"{ADMIN_BASE}/login")
ft = re.search(r'name="_token"\s+value="([^"]+)"', r.text).group(1)
r = session.post(f"{ADMIN_BASE}/login", data={
    "email": EMAIL, "passwd": PASSWORD,
    "stay_logged_in": "0", "_token": ft, "submitLogin": "1",
}, allow_redirects=True)
if "login" in r.url:
    print("  [ERROR] Login failed!")
    sys.exit(1)
legacy_token = re.search(r'[?&]token=([A-Za-z0-9._\-]+)', r.url)
legacy_token = legacy_token.group(1) if legacy_token else ""
print(f"  Logged in OK")

# ── Chain through catalog to get a valid Symfony _token ────────────────────────
print("[2] Fetching catalog to get proper Symfony token...")
r_cat = session.get(f"{ADMIN_BASE}/index.php",
                    params={"controller": "AdminProducts", "token": legacy_token},
                    allow_redirects=True)
cat_token = extract_url_token(r_cat.url) or legacy_token
print(f"  Catalog token: {cat_token[:60]}")

# ── Fetch edit page with the proper token ──────────────────────────────────────
print(f"[3] Fetching edit page for product {PRODUCT_ID}...")
r2 = session.get(
    f"{ADMIN_BASE}/index.php/sell/catalog/products/{PRODUCT_ID}/edit",
    params={"_token": cat_token},
    allow_redirects=True,
)
url_token = extract_url_token(r2.url) or cat_token
print(f"  Edit page size: {len(r2.text):,} bytes")

# Extract the specific image-form CSRF token
img_dt_m = re.search(
    r'data-form-name="product_image"[^>]*data-token="([^"]+)"', r2.text
)
if not img_dt_m:
    # Fallback: try reversed attribute order
    img_dt_m = re.search(
        r'data-token="([^"]+)"[^>]*data-form-name="product_image"', r2.text
    )
img_data_token = img_dt_m.group(1) if img_dt_m else url_token
print(f"  URL token:        {url_token[:60]}")
print(f"  Image data token: {img_data_token[:60]}")

# ── Compress and upload ────────────────────────────────────────────────────────
UPLOAD_URL = f"{ADMIN_BASE}/index.php/sell/catalog/products/images/add"
uploaded, errors = [], []

print(f"\n[3] Compressing and uploading {len(IMAGE_PATHS)} images...")
for i, img_path in enumerate(IMAGE_PATHS, 1):
    fname = os.path.basename(img_path)
    orig_size = os.path.getsize(img_path)
    print(f"\n  [{i}/{len(IMAGE_PATHS)}] {fname[:70]}")
    print(f"      Original: {orig_size:,} B")

    try:
        data, final_size = compress_image(img_path, MAX_BYTES)
    except Exception as e:
        print(f"      [ERROR] Compression failed: {e}")
        errors.append(fname)
        continue

    # Use .jpg extension if we ended up with JPEG data
    mime = "image/png"
    upload_fname = fname
    if data[:3] == b'\xff\xd8\xff':   # JPEG magic bytes
        mime = "image/jpeg"
        upload_fname = fname.replace(".png", ".jpg")

    resp = session.post(
        UPLOAD_URL,
        params={"_token": url_token},
        files={"product_image[file]": (upload_fname, data, mime)},
        data={
            "product_image[product_id]": str(PRODUCT_ID),
            "product_image[_token]":     img_data_token,
        },
        headers={
            "X-Requested-With": "XMLHttpRequest",
            "Referer":          r2.url,
        },
    )

    body = resp.text.strip()
    if resp.status_code in (200, 201):
        try:
            j = json.loads(body)
            if "image_id" in j:
                cover = " \u2190 COVER" if j.get("is_cover") else ""
                print(f"      OK  image_id={j['image_id']}  pos={j.get('position')}{cover}")
                uploaded.append(j["image_id"])
            else:
                print(f"      WARN: {body[:120]}")
                errors.append(fname)
        except json.JSONDecodeError:
            print(f"      WARN (non-JSON): {body[:120]}")
            errors.append(fname)
    else:
        print(f"      ERROR {resp.status_code}: {body[:120]}")
        errors.append(fname)

print(f"\n{'═'*60}")
print(f"  Uploaded: {len(uploaded)}/{len(IMAGE_PATHS)}")
print(f"  IDs:      {uploaded}")
if errors:
    print(f"  Failed:   {errors}")
print(f"\n  Admin URL: {ADMIN_BASE}/index.php/sell/catalog/products/{PRODUCT_ID}/edit")
print(f"{'═'*60}")
