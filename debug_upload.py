"""Debug script - trace every step to find correct tokens for image upload."""
import requests, re, sys, json
sys.stdout.reconfigure(encoding='utf-8')

ADMIN = 'https://alegro.gr/admin875fdclzkf27m3shsg9'
PRODUCT_ID = 386
MAX_BYTES = 2_000_000

from pathlib import Path
from PIL import Image
import io, os

DOWNLOADS = str(Path.home() / "Downloads")

# The 6 images that failed
FAILED = [
    "Kapodistrias-Wig-Made-in-Greece-Alegro-Ioannis-Kapodistrias-perouka-film-2026-reenactment-wig-John1-enface.png",
    "Kapodistrias-Wig-Made-in-Greece-Alegro-Ioannis-Kapodistrias-perouka-film-2026-reenactment-wig-John2-3-4.png",
    "Kapodistrias-Wig-Made-in-Greece-Alegro-Ioannis-Kapodistrias-perouka-film-2026-reenactment-wig-doll-head (1).png",
    "Kapodistrias-Wig-Made-in-Greece-Alegro-Ioannis-Kapodistrias-perouka-film-2026-reenactment-wig-doll-head (2).png",
    "Kapodistrias-Wig-Made-in-Greece-Alegro-Ioannis-Kapodistrias-perouka-film-2026-reenactment-wig-doll-head (4).png",
    "Kapodistrias-Wig-Made-in-Greece-Alegro-Ioannis-Kapodistrias-perouka-film-2026-reenactment-wig-doll-head (7).png",
]

s = requests.Session()
s.headers['User-Agent'] = 'Mozilla/5.0'

# ── Login ──────────────────────────────────────────────────────────────────────
r = s.get(ADMIN + '/login')
ft = re.search(r'name="_token"\s+value="([^"]+)"', r.text).group(1)
passwd = 'cultivatesandspreadslove13579' + chr(33)
r = s.post(ADMIN + '/login', data={'email':'damoncollective@gmail.com','passwd':passwd,'stay_logged_in':'0','_token':ft,'submitLogin':'1'}, allow_redirects=True)
print(f'Login redirect: {r.url}')
m = re.search(r'[?&]token=([A-Za-z0-9._\-]+)', r.url)
legacy_tok = m.group(1) if m else ''
print(f'Legacy token: {legacy_tok[:60]}')

# ── Catalog ────────────────────────────────────────────────────────────────────
r2 = s.get(ADMIN + '/index.php', params={'controller':'AdminProducts','token':legacy_tok}, allow_redirects=True)
print(f'Catalog URL: {r2.url[:100]}  size={len(r2.text)}')
cat_token_m = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r2.url)
cat_token = cat_token_m.group(1) if cat_token_m else legacy_tok
print(f'Catalog _token: {cat_token[:80]}')

# ── Edit page ─────────────────────────────────────────────────────────────────
r3 = s.get(f'{ADMIN}/index.php/sell/catalog/products/{PRODUCT_ID}/edit', params={'_token': cat_token}, allow_redirects=True)
print(f'Edit URL: {r3.url[:120]}  size={len(r3.text)}')
url_tok = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r3.url)
url_tok = url_tok.group(1) if url_tok else cat_token
print(f'Edit URL token: {url_tok[:80]}')

# ── Extract image form token ───────────────────────────────────────────────────
img_dt = re.search(r'data-form-name="product_image"[^>]*data-token="([^"]+)"', r3.text)
if not img_dt:
    img_dt = re.search(r'data-token="([^"]+)"[^>]*data-form-name="product_image"', r3.text)
if img_dt:
    img_tok = img_dt.group(1)
    print(f'Image form token: {img_tok[:80]}')
else:
    print('Image form token: NOT FOUND — using URL token as fallback')
    img_tok = url_tok
    # Print first 500 chars of page to diagnose
    print(f'Page content (first 500): {r3.text[:500]}')

# ── Compress helper ────────────────────────────────────────────────────────────
def compress(path):
    img = Image.open(path).convert("RGBA")
    w, h = img.size
    scale = 0.95
    while scale >= 0.50:
        nw, nh = int(w*scale), int(h*scale)
        buf = io.BytesIO()
        img.resize((nw, nh), Image.LANCZOS).save(buf, "PNG", optimize=True, compress_level=9)
        if buf.tell() <= MAX_BYTES:
            print(f'  Compressed to {scale*100:.0f}% → {buf.tell():,} B')
            return buf.getvalue(), "image/png", os.path.basename(path)
        scale -= 0.05
    # JPEG fallback
    rgb = img.convert("RGB")
    for q in range(90, 55, -5):
        buf = io.BytesIO()
        rgb.save(buf, "JPEG", quality=q, optimize=True)
        if buf.tell() <= MAX_BYTES:
            print(f'  JPEG q={q} → {buf.tell():,} B')
            return buf.getvalue(), "image/jpeg", os.path.basename(path).replace(".png", ".jpg")
    raise RuntimeError("Can't compress")

# ── Upload ────────────────────────────────────────────────────────────────────
UPLOAD_URL = f'{ADMIN}/index.php/sell/catalog/products/images/add'
ok, fail = [], []

for fname in FAILED:
    path = os.path.join(DOWNLOADS, fname)
    orig = os.path.getsize(path)
    print(f'\n[{fname[:60]}] orig={orig:,}')
    try:
        data, mime, upload_name = compress(path)
    except Exception as e:
        print(f'  COMPRESS ERROR: {e}')
        fail.append(fname)
        continue

    resp = s.post(
        UPLOAD_URL,
        params={'_token': url_tok},
        files={'product_image[file]': (upload_name, data, mime)},
        data={'product_image[product_id]': str(PRODUCT_ID), 'product_image[_token]': img_tok},
        headers={'X-Requested-With': 'XMLHttpRequest', 'Referer': r3.url},
    )
    body = resp.text.strip()
    print(f'  Upload: {resp.status_code} → {body[:150]}')
    try:
        j = json.loads(body)
        if 'image_id' in j:
            ok.append(j['image_id'])
        else:
            fail.append(fname)
    except:
        fail.append(fname)

print(f'\n{"="*50}')
print(f'Uploaded: {len(ok)}/{len(FAILED)}  IDs: {ok}')
if fail:
    print(f'Failed: {fail}')
