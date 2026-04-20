#!/usr/bin/env python3
"""
Deploy imagecropper module to alegro.gr via PS admin.
Uploads all module files via cPanel File Manager API, then installs.
"""
import requests, re, os, json, base64, sys

ADMIN  = "https://alegro.gr/admin875fdclzkf27m3shsg9"
EMAIL  = "damoncollective@gmail.com"
PASSWD = "cultivatesandspreadslove13579" + chr(33)
MODULE_DIR = "/home/hrundivbachsi/alegro/imagecropper"
ZIP_PATH   = "/home/hrundivbachsi/Downloads/imagecropper.zip"

session = requests.Session()
session.headers["User-Agent"] = "Mozilla/5.0 (X11; Linux x86_64)"

# ── 1. Login ──────────────────────────────────────────────────────────────────
print("[1] Logging in...")
r = session.get(f"{ADMIN}/login")
ft = re.search(r'name="_token"\s+value="([^"]+)"', r.text).group(1)
r = session.post(f"{ADMIN}/login", data={
    "email": EMAIL, "passwd": PASSWD,
    "stay_logged_in": "0", "_token": ft, "submitLogin": "1"
}, allow_redirects=True)
if "login" in r.url.lower() and r.url != f"{ADMIN}/":
    print("  ERROR: Login failed"); sys.exit(1)
print(f"  OK — {r.url[:80]}")

# Extract Symfony token from redirect URL
sym_token = re.search(r'[?&]_?token=([A-Za-z0-9._\-]+)', r.url)
sym_token = sym_token.group(1) if sym_token else ""

# ── 2. Get module manager page + CSRF token ───────────────────────────────────
print("[2] Getting module manager page...")
r2 = session.get(f"{ADMIN}/index.php/module/manage-all",
                 params={"_token": sym_token}, allow_redirects=True)
# Refresh token from final URL
t2 = re.search(r'[?&]_?token=([A-Za-z0-9._\-]+)', r2.url)
if t2: sym_token = t2.group(1)
print(f"  Token: {sym_token[:60]}")

# ── 3. Upload the zip ─────────────────────────────────────────────────────────
print("[3] Uploading module zip...")
with open(ZIP_PATH, "rb") as f:
    zip_data = f.read()

r3 = session.post(
    f"{ADMIN}/index.php/module/upload",
    params={"_token": sym_token},
    files={"file_uploaded": ("imagecropper.zip", zip_data, "application/zip")},
    headers={"X-Requested-With": "XMLHttpRequest"},
    timeout=60
)
print(f"  Status: {r3.status_code}")
print(f"  Response: {r3.text[:300]}")

# ── 4. Install via Symfony route ──────────────────────────────────────────────
print("[4] Installing module (Symfony route)...")
r4 = session.post(
    f"{ADMIN}/index.php/module/manage-action/install",
    params={"_token": sym_token},
    json={"module": "imagecropper"},
    headers={
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/json",
        "Accept": "application/json",
    },
    timeout=30
)
print(f"  Status: {r4.status_code}")
print(f"  Response: {r4.text[:400]}")

if r4.status_code == 200:
    try:
        j = r4.json()
        if j.get("status") == "success" or j.get("success"):
            print("\n  ✓ Module installed successfully!")
            sys.exit(0)
    except Exception:
        pass

# ── 5. Fallback: legacy admin install ─────────────────────────────────────────
print("[5] Trying legacy install route...")
r_leg = session.get(f"{ADMIN}/index.php",
                    params={"controller": "AdminModules", "token": sym_token},
                    allow_redirects=True)
leg_token = re.search(r'[?&]token=([A-Za-z0-9._\-]+)', r_leg.url)
leg_token = leg_token.group(1) if leg_token else sym_token

r5 = session.get(f"{ADMIN}/index.php", params={
    "controller": "AdminModules",
    "token": leg_token,
    "install": "imagecropper",
    "module_name": "imagecropper",
}, allow_redirects=True)
print(f"  Status: {r5.status_code}")
if "imagecropper" in r5.text and ("uninstall" in r5.text.lower() or "configure" in r5.text.lower()):
    print("\n  ✓ Module appears to be installed!")
else:
    print(f"  Response snippet: {r5.text[:400]}")
