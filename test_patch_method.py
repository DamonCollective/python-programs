"""
Test sending _method=PATCH in the POST body (like the PS9 JS does).
The JS creates a 'shadow form' with only CHANGED fields + _method=PATCH + product[_token].
"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8')

ADMIN = 'https://alegro.gr/admin875fdclzkf27m3shsg9'
PID = 265

s = requests.Session()
s.headers['User-Agent'] = 'Mozilla/5.0'

# Login
r = s.get(ADMIN + '/login')
ft = re.search(r'name="_token"\s+value="([^"]+)"', r.text).group(1)
passwd = 'cultivatesandspreadslove13579' + chr(33)
r = s.post(ADMIN + '/login', data={'email':'damoncollective@gmail.com','passwd':passwd,'stay_logged_in':'0','_token':ft,'submitLogin':'1'}, allow_redirects=True)
m = re.search(r'[?&]token=([A-Za-z0-9._\-]+)', r.url)
legacy_tok = m.group(1) if m else ''
r2 = s.get(ADMIN + '/index.php', params={'controller':'AdminProducts','token':legacy_tok}, allow_redirects=True)
cat_token = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r2.url).group(1)
print('Logged in OK')

r_edit = s.get(f'{ADMIN}/index.php/sell/catalog/products/{PID}/edit',
               params={'_token': cat_token}, allow_redirects=True)
edit_tok = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r_edit.url).group(1)
html = r_edit.text

# Get the product form CSRF token
form_tok_m = re.search(r'name="product\[_token\]"[^>]*value="([^"]+)"', html, re.I)
form_tok = form_tok_m.group(1) if form_tok_m else edit_tok
print(f'form_tok: {form_tok[:40]}')

# Get existing categories
existing = {}
for m in re.finditer(r'<input[^>]*name="product\[description\]\[categories\]\[product_categories\]\[(\d+)\]\[id\]"[^>]*value="(\d+)"', html, re.I):
    existing[int(m.group(1))] = m.group(2)
print(f'Existing cats: {existing}')
next_idx = max(existing.keys(), default=-1) + 1

# Mimic what the PS9 JavaScript sends:
# Only the CHANGED fields: the new category + product[_token] + _method
# This is what createShadowForm does
payload = {
    '_method': 'PATCH',
    'product[_token]': form_tok,
    # New category at next_idx
    f'product[description][categories][product_categories][{next_idx}][id]': '12',
    f'product[description][categories][product_categories][{next_idx}][name]': 'Theatrical',
    f'product[description][categories][product_categories][{next_idx}][display_name]': 'Theatrical',
}

print(f'\nPayload ({len(payload)} fields):')
for k, v in payload.items():
    print(f'  {k} = {v}')

# Test 1: Basic PATCH via _method field (mimic JS shadow form)
print('\n--- Test 1: _method=PATCH in body ---')
r1 = s.post(
    f'{ADMIN}/index.php/sell/catalog/products/{PID}/edit',
    params={'_token': edit_tok},
    data=payload,
    headers={'Referer': r_edit.url},
    allow_redirects=False,
)
print(f'Status: {r1.status_code}')
print(f'Location: {r1.headers.get("Location", "NONE")}')
print(f'Content-Type: {r1.headers.get("Content-Type", "")}')
print(f'Body size: {len(r1.text):,}')
print(f'Body[:200]: {r1.text[:200]}')

# Check for JSON
if r1.headers.get('Content-Type', '').startswith('application/json'):
    try:
        import json
        data = r1.json()
        print(f'JSON response: {data}')
    except:
        print(f'JSON parse failed: {r1.text[:200]}')

# Check form validity
form_valid = re.search(r'data-form-valid="(\d+)"', r1.text)
form_subm = re.search(r'data-form-submitted="(\d+)"', r1.text)
print(f'form-valid={form_valid.group(1) if form_valid else "?"}  form-submitted={form_subm.group(1) if form_subm else "?"}')

# Test 2: PATCH with existing categories + new one (submitting ALL cat data)
print('\n--- Test 2: All categories in PATCH ---')
payload2 = {
    '_method': 'PATCH',
    'product[_token]': form_tok,
}
# Include ALL existing categories
for idx, cat_id in existing.items():
    # Get name too
    name_m = re.search(f'name="product\\[description\\]\\[categories\\]\\[product_categories\\]\\[{idx}\\]\\[name\\]"[^>]*value="([^"]*)"', html, re.I)
    dn_m = re.search(f'name="product\\[description\\]\\[categories\\]\\[product_categories\\]\\[{idx}\\]\\[display_name\\]"[^>]*value="([^"]*)"', html, re.I)
    base = f'product[description][categories][product_categories][{idx}]'
    payload2[f'{base}[id]'] = cat_id
    payload2[f'{base}[name]'] = name_m.group(1) if name_m else ''
    payload2[f'{base}[display_name]'] = dn_m.group(1) if dn_m else ''
# Add new Theatrical
base_new = f'product[description][categories][product_categories][{next_idx}]'
payload2[f'{base_new}[id]'] = '12'
payload2[f'{base_new}[name]'] = 'Theatrical'
payload2[f'{base_new}[display_name]'] = 'Theatrical'

r2 = s.post(
    f'{ADMIN}/index.php/sell/catalog/products/{PID}/edit',
    params={'_token': edit_tok},
    data=payload2,
    headers={'Referer': r_edit.url},
    allow_redirects=False,
)
print(f'Status: {r2.status_code}')
print(f'Location: {r2.headers.get("Location", "NONE")}')
print(f'Body size: {len(r2.text):,}')
form_valid = re.search(r'data-form-valid="(\d+)"', r2.text)
print(f'form-valid={form_valid.group(1) if form_valid else "?"}')

# Verify current state
print('\n--- Checking current categories (fresh fetch) ---')
r_check = s.get(f'{ADMIN}/index.php/sell/catalog/products/{PID}/edit',
                params={'_token': cat_token}, allow_redirects=True)
cats = {}
for m in re.finditer(r'<input[^>]*name="product\[description\]\[categories\]\[product_categories\]\[(\d+)\]\[id\]"[^>]*value="(\d+)"', r_check.text, re.I):
    cats[int(m.group(1))] = m.group(2)
print(f'Categories: {cats}')
print(f'Has Theatrical: {"12" in cats.values()}')
