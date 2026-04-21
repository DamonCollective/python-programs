"""
Add Theatrical (category 12) to all hero products.
Fix: exclude product[details][features][...] fields (the 'add feature' widget
     with feature_id=0 triggers validation failure and blocks the entire save).
"""
import requests, re, sys
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
r = s.post(ADMIN + '/login',
           data={'email':'damoncollective@gmail.com','passwd':passwd,
                 'stay_logged_in':'0','_token':ft,'submitLogin':'1'},
           allow_redirects=True)
m = re.search(r'[?&]token=([A-Za-z0-9._\-]+)', r.url)
legacy_tok = m.group(1) if m else ''
r2 = s.get(ADMIN + '/index.php',
           params={'controller':'AdminProducts','token':legacy_tok},
           allow_redirects=True)
cat_token = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r2.url).group(1)
print('Logged in OK\n')


def get_all_inputs(html):
    inputs = {}
    for m in re.finditer(r'<input[^>]+>', html, re.I):
        tag = m.group(0)
        name_m = re.search(r'\bname="([^"]+)"', tag, re.I)
        val_m  = re.search(r'\bvalue="([^"]*)"', tag, re.I)
        if name_m:
            inputs[name_m.group(1)] = val_m.group(1) if val_m else ''
    return inputs


def get_categories_flexible(html):
    cats = {}
    for m in re.finditer(
        r'<input[^>]*name="product\[description\]\[categories\]\[product_categories\]\[(\d+)\]\[id\]"[^>]*value="(\d+)"',
        html, re.I
    ):
        cats[int(m.group(1))] = m.group(2)
    for m in re.finditer(
        r'<input[^>]*value="(\d+)"[^>]*name="product\[description\]\[categories\]\[product_categories\]\[(\d+)\]\[id\]"',
        html, re.I
    ):
        cats[int(m.group(2))] = m.group(1)
    return cats


# Fields that cause form validation errors when empty/zero — exclude them:
# product[details][features][...] is the "Add Feature" widget; feature_id=0 → invalid
FIELDS_TO_EXCLUDE = {
    'product[details][features][feature_id]',
    'product[details][features][feature_value_id]',
    'product[details][features][custom_value][1]',
    'product[details][features][custom_value][2]',
}


# ── Phase 1: Show current state ────────────────────────────────────────────────
print('=== Phase 1: Current categories ===')
for pid in PRODUCTS:
    r_e = s.get(f'{ADMIN}/index.php/sell/catalog/products/{pid}/edit',
                params={'_token': cat_token}, allow_redirects=True)
    cats = get_categories_flexible(r_e.text)
    mark = '✓' if str(THEATRICAL_ID) in cats.values() else '✗'
    print(f'  {mark} Product {pid}: {list(cats.values())}')

# ── Phase 2: Add Theatrical ────────────────────────────────────────────────────
print('\n=== Phase 2: Adding Theatrical ===')
for pid in PRODUCTS:
    r_edit = s.get(f'{ADMIN}/index.php/sell/catalog/products/{pid}/edit',
                   params={'_token': cat_token}, allow_redirects=True)
    edit_tok = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r_edit.url).group(1)

    existing = get_categories_flexible(r_edit.text)
    if str(THEATRICAL_ID) in existing.values():
        print(f'  Product {pid}: already has Theatrical — skip')
        continue

    next_idx = max(existing.keys(), default=-1) + 1

    # All page inputs, minus the broken feature-add widget fields
    payload = {k: v for k, v in get_all_inputs(r_edit.text).items()
               if k not in FIELDS_TO_EXCLUDE}

    # Add Theatrical category
    base = f'product[description][categories][product_categories][{next_idx}]'
    payload[base + '[id]']           = str(THEATRICAL_ID)
    payload[base + '[name]']         = THEATRICAL_NAME
    payload[base + '[display_name]'] = THEATRICAL_NAME

    # URL-level CSRF
    payload['_token'] = edit_tok

    prod_name = payload.get('product[header][name][1]', f'Product {pid}')
    print(f'  Product {pid} ({prod_name[:45]}):')
    print(f'    fields={len(payload)}, existing cats={list(existing.values())} + [12]')

    r_save = s.post(
        f'{ADMIN}/index.php/sell/catalog/products/{pid}/edit',
        params={'_token': edit_tok},
        data=payload,
        headers={'Referer': r_edit.url},
        allow_redirects=False,
    )
    loc = r_save.headers.get('Location', 'NONE')
    print(f'    Save: {r_save.status_code} Location={loc[:60]}')

    # Check form validity in response
    form_valid = re.search(r'data-form-valid="(\d+)"', r_save.text)
    form_subm  = re.search(r'data-form-submitted="(\d+)"', r_save.text)
    if form_valid:
        print(f'    form-valid={form_valid.group(1)}, form-submitted={form_subm.group(1) if form_subm else "?"}')

    # Show any errors
    errors = re.findall(r'<div[^>]*alert-danger[^>]*>(.*?)</div>', r_save.text, re.I | re.S)
    for e in errors:
        text = re.sub(r'<[^>]+>', ' ', e).strip()
        text = re.sub(r'\s+', ' ', text)
        if text:
            print(f'    ERROR: {text[:250]}')

    # Identify any is-invalid fields in response
    invalid_fields = re.findall(r'name="([^"]+)"[^>]*class="[^"]*is-invalid', r_save.text, re.I)
    if invalid_fields:
        print(f'    Invalid fields: {invalid_fields[:5]}')

# ── Phase 3: Final verification ────────────────────────────────────────────────
print('\n=== Phase 3: Final verification ===')
all_ok = True
for pid in PRODUCTS:
    r_v = s.get(f'{ADMIN}/index.php/sell/catalog/products/{pid}/edit',
                params={'_token': cat_token}, allow_redirects=True)
    cats = get_categories_flexible(r_v.text)
    has = str(THEATRICAL_ID) in cats.values()
    mark = '✓' if has else '✗'
    print(f'  {mark} Product {pid}: {list(cats.values())}')
    if not has:
        all_ok = False

print()
if all_ok:
    print('SUCCESS: All products now have Theatrical (12) category.')
else:
    print('PARTIAL: Some products still missing Theatrical category.')
