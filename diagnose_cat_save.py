"""Diagnose what errors PS9 returns when we try to save categories."""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8')

ADMIN = 'https://alegro.gr/admin875fdclzkf27m3shsg9'
THEATRICAL_ID   = 12
THEATRICAL_NAME = 'Theatrical'
PID = 265  # Just test one product

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

# Fetch edit page
r_edit = s.get(f'{ADMIN}/index.php/sell/catalog/products/{PID}/edit',
               params={'_token': cat_token}, allow_redirects=True)
edit_tok = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r_edit.url).group(1)
print(f'Edit page size: {len(r_edit.text):,}')

# Extract ALL inputs
all_inputs = {}
for m in re.finditer(r'<input[^>]+>', r_edit.text, re.I):
    tag = m.group(0)
    name_m = re.search(r'\bname="([^"]+)"', tag, re.I)
    val_m  = re.search(r'\bvalue="([^"]*)"', tag, re.I)
    if name_m:
        all_inputs[name_m.group(1)] = val_m.group(1) if val_m else ''

# Also textareas
for m in re.finditer(r'<textarea[^>]*name="([^"]+)"[^>]*>(.*?)</textarea>', r_edit.text, re.I | re.S):
    all_inputs[m.group(1)] = m.group(2)

# Also selects
for m in re.finditer(r'<select[^>]*name="([^"]+)"[^>]*>(.*?)</select>', r_edit.text, re.I | re.S):
    sel_name = m.group(1)
    # Find selected option value
    sel_val_m = re.search(r'<option[^>]*selected[^>]*value="([^"]*)"', m.group(2), re.I)
    if not sel_val_m:
        sel_val_m = re.search(r'<option[^>]*value="([^"]*)"', m.group(2), re.I)
    all_inputs[sel_name] = sel_val_m.group(1) if sel_val_m else ''

print(f'\nTotal form inputs found: {len(all_inputs)}')
print('\nAll input names:')
for k, v in sorted(all_inputs.items()):
    print(f'  {k} = {repr(v[:80])}')

# Show category-related inputs
print('\n--- Category inputs ---')
for k, v in sorted(all_inputs.items()):
    if 'categor' in k.lower():
        print(f'  {k} = {repr(v)}')

# Get existing categories
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

existing = get_categories_flexible(r_edit.text)
print(f'\nExisting categories: {existing}')

next_idx = max(existing.keys(), default=-1) + 1

# Build payload: ALL inputs + new category
payload = dict(all_inputs)

# Override/add category
base = f'product[description][categories][product_categories][{next_idx}]'
payload[base + '[id]']           = str(THEATRICAL_ID)
payload[base + '[name]']         = THEATRICAL_NAME
payload[base + '[display_name]'] = THEATRICAL_NAME
payload['product[description][categories][default_category][value]'] = \
    all_inputs.get('product[description][categories][default_category][value]', str(THEATRICAL_ID))

# Make sure CSRF tokens are right
js_tok_m = re.search(r"var token = '([^']+)'", r_edit.text)
js_tok = js_tok_m.group(1) if js_tok_m else edit_tok
payload['product[_token]'] = js_tok
payload['_token']          = edit_tok

print(f'\nSending {len(payload)} fields total')
print(f'product[_token] = {js_tok[:40]}')
print(f'_token          = {edit_tok[:40]}')

r_save = s.post(
    f'{ADMIN}/index.php/sell/catalog/products/{PID}/edit',
    params={'_token': edit_tok},
    data=payload,
    headers={'Referer': r_edit.url},
    allow_redirects=True,
)
print(f'\nSave response: {r_save.status_code} → {r_save.url[:100]}')
print(f'Response size: {len(r_save.text):,}')

# Extract full error content (including nested tags)
errors = re.findall(r'<div[^>]*alert-danger[^>]*>(.*?)</div>', r_save.text, re.I | re.S)
if errors:
    print(f'\nAlert-danger divs ({len(errors)}):')
    for i, e in enumerate(errors):
        # Strip tags to get text
        text = re.sub(r'<[^>]+>', ' ', e).strip()
        text = re.sub(r'\s+', ' ', text)
        print(f'  Error {i+1}: {text[:300]}')
else:
    print('\nNo alert-danger divs found.')

# Look for any validation messages
val_errors = re.findall(r'<span[^>]*class="[^"]*(?:error|invalid|help-block)[^"]*"[^>]*>(.*?)</span>', r_save.text, re.I | re.S)
if val_errors:
    print(f'\nValidation errors:')
    for e in val_errors[:10]:
        text = re.sub(r'<[^>]+>', ' ', e).strip()
        if text.strip():
            print(f'  {text[:200]}')

# Look for success indicators
if 'alert-success' in r_save.text or 'success' in r_save.url:
    print('\n[SUCCESS] Product saved successfully!')
elif 'alert-danger' in r_save.text:
    print('\n[ERROR] Save failed with errors above')
    # Dump a section of the response around alert-danger
    idx = r_save.text.find('alert-danger')
    if idx >= 0:
        snippet = r_save.text[max(0, idx-200):idx+500]
        print('\nHTML snippet around error:')
        print(snippet[:800])
