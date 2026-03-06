"""
Add category 12 (Theatrical/θεατρικες) to all hero wig & moustache products.

Hero products:
  265, 266  → Karaiskakis / Kolokotronis wig+moustache pair
  267, 268  → Diakos wig+moustache pair
  269, 270  → remaining hero pair
  386       → Kapodistrias wig (newly created)
"""
import requests, re, sys, json
sys.stdout.reconfigure(encoding='utf-8')

ADMIN = 'https://alegro.gr/admin875fdclzkf27m3shsg9'
THEATRICAL_ID   = 12
THEATRICAL_NAME = 'Theatrical'
PRODUCTS = [265, 266, 267, 268, 269, 270, 386]

s = requests.Session()
s.headers['User-Agent'] = 'Mozilla/5.0'

# ── Login ──────────────────────────────────────────────────────────────────────
r = s.get(ADMIN + '/login')
ft = re.search(r'name="_token"\s+value="([^"]+)"', r.text).group(1)
passwd = 'cultivatesandspreadslove13579' + chr(33)
r = s.post(ADMIN + '/login', data={'email':'damoncollective@gmail.com','passwd':passwd,'stay_logged_in':'0','_token':ft,'submitLogin':'1'}, allow_redirects=True)
m = re.search(r'[?&]token=([A-Za-z0-9._\-]+)', r.url)
legacy_tok = m.group(1) if m else ''

# Get a valid Symfony _token
r2 = s.get(ADMIN + '/index.php', params={'controller':'AdminProducts','token':legacy_tok}, allow_redirects=True)
cat_token = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r2.url).group(1)
print('Logged in OK\n')


def get_current_categories(html):
    """Extract current categories list from product edit page hidden inputs."""
    cats = {}
    # Match: product[description][categories][product_categories][N][field] = value
    entries = re.findall(
        r'name="product\[description\]\[categories\]\[product_categories\]\[(\d+)\]\[(\w+)\]"\s+value="([^"]*)"',
        html
    )
    for idx, field, val in entries:
        idx = int(idx)
        if idx not in cats:
            cats[idx] = {}
        cats[idx][field] = val.replace('&amp;', '&')
    return cats


def build_category_payload(cats_dict):
    """Build form fields for categories."""
    payload = {}
    for idx, cat in cats_dict.items():
        for field, val in cat.items():
            payload[f'product[description][categories][product_categories][{idx}][{field}]'] = val
    return payload


results = []

for pid in PRODUCTS:
    print(f'─── Product {pid} ───────────────────────────────')

    # Fetch edit page (properly chained token)
    r_edit = s.get(f'{ADMIN}/index.php/sell/catalog/products/{pid}/edit',
                   params={'_token': cat_token}, allow_redirects=True)
    edit_tok = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r_edit.url).group(1)

    # Extract CSRF token for the product form
    ft_m = (
        re.search(r'name="product\[_token\]"\s+value="([^"]+)"', r_edit.text)
        or re.search(r'data-form-name="product"[^>]*data-token="([^"]+)"', r_edit.text)
        or re.search(r'var token = \'([^\']+)\'', r_edit.text)
    )
    form_tok = ft_m.group(1) if ft_m else edit_tok

    # Get product name for logging
    title_m = re.search(r'<title>\s*([^•<]{3,80})\s*•', r_edit.text)
    prod_name = title_m.group(1).strip() if title_m else f'Product {pid}'

    # Get existing categories
    existing_cats = get_current_categories(r_edit.text)
    existing_ids = {cat.get('id') for cat in existing_cats.values()}
    print(f'  Name   : {prod_name}')
    print(f'  Current categories: {[(v.get("id"), v.get("name")) for v in existing_cats.values()]}')

    # Check if Theatrical already assigned
    if str(THEATRICAL_ID) in existing_ids:
        print(f'  [OK] Already has Theatrical (12) — skipping\n')
        results.append({'pid': pid, 'status': 'already_set'})
        continue

    # Add Theatrical as a new category
    next_idx = max(existing_cats.keys(), default=-1) + 1
    existing_cats[next_idx] = {
        'id':           str(THEATRICAL_ID),
        'name':         THEATRICAL_NAME,
        'display_name': THEATRICAL_NAME,
    }
    print(f'  Adding Theatrical at index {next_idx}')

    # Build payload: categories + CSRF tokens only
    payload = build_category_payload(existing_cats)
    payload['product[_token]'] = form_tok
    payload['_token']          = edit_tok

    # Also set default_category if the product has none set
    dc_m = re.search(r'name="product\[description\]\[categories\]\[default_category\]\[value\]"\s+value="(\d+)"', r_edit.text)
    if dc_m:
        payload['product[description][categories][default_category][value]'] = dc_m.group(1)
    else:
        payload['product[description][categories][default_category][value]'] = str(THEATRICAL_ID)

    # Submit
    r_save = s.post(
        f'{ADMIN}/index.php/sell/catalog/products/{pid}/edit',
        params={'_token': edit_tok},
        data=payload,
        headers={'Referer': r_edit.url},
        allow_redirects=True,
    )
    print(f'  Save  : {r_save.status_code} → {r_save.url[:90]}')

    # Verify by re-fetching and checking
    r_verify = s.get(f'{ADMIN}/index.php/sell/catalog/products/{pid}/edit',
                     params={'_token': cat_token}, allow_redirects=True)
    updated = get_current_categories(r_verify.text)
    updated_ids = {cat.get('id') for cat in updated.values()}
    success = str(THEATRICAL_ID) in updated_ids
    print(f'  Verify: Theatrical in categories → {success}')
    print(f'  Final categories: {[(v.get("id"), v.get("name")) for v in updated.values()]}')
    results.append({'pid': pid, 'status': 'set' if success else 'FAILED'})
    print()

# ── Summary ────────────────────────────────────────────────────────────────────
print('═' * 55)
print('SUMMARY')
for res in results:
    mark = '✓' if res['status'] in ('set', 'already_set') else '✗'
    print(f'  {mark} Product {res["pid"]}  →  {res["status"]}')
print('═' * 55)
