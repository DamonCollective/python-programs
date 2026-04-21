"""
1. Verify current categories on all hero products (using correct flexible regex).
2. If Theatrical (12) is missing, add it via proper form submission.
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
r2 = s.get(ADMIN + '/index.php', params={'controller':'AdminProducts','token':legacy_tok}, allow_redirects=True)
cat_token = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r2.url).group(1)
print('Logged in OK\n')


def get_categories_flexible(html):
    """Extract category IDs using flexible regex (handles any attr order)."""
    # Use general pattern: find input tags whose name contains the category path, then get id value
    # Pattern: <input ... name="product[description][categories][product_categories][N][id]" ... value="V" ...>
    cats = {}
    for m in re.finditer(
        r'<input[^>]*name="product\[description\]\[categories\]\[product_categories\]\[(\d+)\]\[id\]"[^>]*value="(\d+)"',
        html, re.I
    ):
        cats[int(m.group(1))] = m.group(2)
    # Also try reversed: value before name
    for m in re.finditer(
        r'<input[^>]*value="(\d+)"[^>]*name="product\[description\]\[categories\]\[product_categories\]\[(\d+)\]\[id\]"',
        html, re.I
    ):
        cats[int(m.group(2))] = m.group(1)
    return cats


def get_all_inputs(html):
    """Extract ALL hidden inputs from the page for full form submission."""
    inputs = {}
    for m in re.finditer(r'<input[^>]+>', html, re.I):
        tag = m.group(0)
        name_m = re.search(r'\bname="([^"]+)"', tag, re.I)
        val_m  = re.search(r'\bvalue="([^"]*)"', tag, re.I)
        if name_m:
            inputs[name_m.group(1)] = val_m.group(1) if val_m else ''
    return inputs


# ── Phase 1: Check current state ───────────────────────────────────────────────
print('=== Phase 1: Current category state ===')
for pid in PRODUCTS:
    r_edit = s.get(f'{ADMIN}/index.php/sell/catalog/products/{pid}/edit',
                   params={'_token': cat_token}, allow_redirects=True)
    cats = get_categories_flexible(r_edit.text)
    cat_ids = list(cats.values())
    has_theatrical = str(THEATRICAL_ID) in cat_ids
    mark = '✓' if has_theatrical else '✗'
    print(f'  {mark} Product {pid}: categories = {cat_ids}  (theatrical={has_theatrical})')

# ── Phase 2: Add Theatrical via complete form submission ───────────────────────
print('\n=== Phase 2: Adding Theatrical category ===')

for pid in PRODUCTS:
    r_edit = s.get(f'{ADMIN}/index.php/sell/catalog/products/{pid}/edit',
                   params={'_token': cat_token}, allow_redirects=True)
    edit_tok = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r_edit.url).group(1)

    # Get all existing categories
    existing = get_categories_flexible(r_edit.text)
    existing_ids = list(existing.values())

    if str(THEATRICAL_ID) in existing_ids:
        print(f'  Product {pid}: already has Theatrical — skip')
        continue

    # Get the next available index
    next_idx = max(existing.keys(), default=-1) + 1

    # Get ALL input names+values from page (for minimum required fields)
    all_inputs = get_all_inputs(r_edit.text)

    # Extract the JS token for product form
    js_tok_m = re.search(r"var token = '([^']+)'", r_edit.text)
    js_tok = js_tok_m.group(1) if js_tok_m else edit_tok

    # Get product name(s) - needed for valid submit
    name_fields = {k: v for k, v in all_inputs.items() if 'name' in k.lower() and 'product[header]' in k}

    # Build payload: existing hidden inputs + new category + CSRF
    payload = {}

    # Add existing category fields (from hidden inputs)
    cat_keys = [k for k in all_inputs if 'product_categories' in k]
    for k in cat_keys:
        payload[k] = all_inputs[k]

    # Add Theatrical category
    base = f'product[description][categories][product_categories][{next_idx}]'
    payload[base + '[id]']           = str(THEATRICAL_ID)
    payload[base + '[name]']         = THEATRICAL_NAME
    payload[base + '[display_name]'] = THEATRICAL_NAME

    # Default category
    payload['product[description][categories][default_category][value]'] = str(THEATRICAL_ID)

    # Product header - name (required field, get from page or use placeholder)
    name_1 = all_inputs.get('product[header][name][1]', 'Product')
    name_2 = all_inputs.get('product[header][name][2]', 'Product')
    if not name_1:  # empty value from hidden input
        name_1 = f'Product {pid}'
    if not name_2:
        name_2 = f'Product {pid}'
    payload['product[header][name][1]'] = name_1
    payload['product[header][name][2]'] = name_2
    payload['product[header][type]']    = all_inputs.get('product[header][type]', 'standard')

    # CSRF
    payload['product[_token]'] = js_tok
    payload['_token']          = edit_tok

    print(f'  Product {pid}: sending {len(payload)} fields, cats at indices {list(existing.keys()) + [next_idx]}')
    print(f'    name[1]={name_1[:40]}')

    r_save = s.post(
        f'{ADMIN}/index.php/sell/catalog/products/{pid}/edit',
        params={'_token': edit_tok},
        data=payload,
        headers={'Referer': r_edit.url},
        allow_redirects=True,
    )
    print(f'    Save: {r_save.status_code} → {r_save.url[:80]}')

    # Check response for errors
    errors = re.findall(r'alert-danger[^>]*>[^<]{0,200}', r_save.text, re.I)
    if errors:
        for e in errors[:3]:
            print(f'    ERROR: {e[:150]}')

# ── Phase 3: Final verification ────────────────────────────────────────────────
print('\n=== Phase 3: Final verification ===')
for pid in PRODUCTS:
    r_v = s.get(f'{ADMIN}/index.php/sell/catalog/products/{pid}/edit',
                params={'_token': cat_token}, allow_redirects=True)
    cats = get_categories_flexible(r_v.text)
    cat_ids = list(cats.values())
    has_theatrical = str(THEATRICAL_ID) in cat_ids
    mark = '✓' if has_theatrical else '✗'
    print(f'  {mark} Product {pid}: categories = {cat_ids}')
