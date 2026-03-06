"""Fix product 386 visibility: set from 'none' to 'both' (catalog + search)."""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8')

ADMIN = 'https://alegro.gr/admin875fdclzkf27m3shsg9'
PID = 386

s = requests.Session()
s.headers['User-Agent'] = 'Mozilla/5.0'

r = s.get(ADMIN + '/login')
ft = re.search(r'name="_token"\s+value="([^"]+)"', r.text).group(1)
passwd = 'cultivatesandspreadslove13579' + chr(33)
r = s.post(ADMIN + '/login', data={'email':'damoncollective@gmail.com','passwd':passwd,
           'stay_logged_in':'0','_token':ft,'submitLogin':'1'}, allow_redirects=True)
m = re.search(r'[?&]token=([A-Za-z0-9._\-]+)', r.url)
legacy_tok = m.group(1) if m else ''
r2 = s.get(ADMIN + '/index.php', params={'controller':'AdminProducts','token':legacy_tok}, allow_redirects=True)
cat_token = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r2.url).group(1)
print('Logged in OK')

r_edit = s.get(f'{ADMIN}/index.php/sell/catalog/products/{PID}/edit',
               params={'_token': cat_token}, allow_redirects=True)
edit_tok = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r_edit.url).group(1)
html = r_edit.text

# Collect all inputs
all_inputs = {}
for m in re.finditer(r'<input[^>]+>', html, re.I):
    tag = m.group(0)
    nm = re.search(r'\bname="([^"]+)"', tag, re.I)
    vm = re.search(r'\bvalue="([^"]*)"', tag, re.I)
    tp = re.search(r'\btype="([^"]*)"', tag, re.I)
    if not nm: continue
    t = tp.group(1).lower() if tp else 'text'
    if t == 'checkbox':
        if 'checked' in tag.lower():
            all_inputs[nm.group(1)] = vm.group(1) if vm else 'on'
    elif t == 'radio':
        if 'checked' in tag.lower():
            all_inputs[nm.group(1)] = vm.group(1) if vm else ''
    else:
        all_inputs[nm.group(1)] = vm.group(1) if vm else ''

# Collect selects (using selected option or first option)
for sel_m in re.finditer(r'<select([^>]*)>(.*?)</select>', html, re.I | re.S):
    attrs, body = sel_m.group(1), sel_m.group(2)
    nm = re.search(r'\bname="([^"]+)"', attrs, re.I)
    if not nm or 'paginator' in nm.group(1): continue
    selected = re.search(r'<option[^>]+selected[^>]*value="([^"]*)"', body, re.I)
    if not selected:
        selected = re.search(r'<option[^>]*value="([^"]*)"', body, re.I)
    all_inputs[nm.group(1)] = selected.group(1) if selected else ''

print(f'Current visibility: {repr(all_inputs.get("product[options][visibility][visibility]", "NOT FOUND"))}')
print(f'Current online_only: {repr(all_inputs.get("product[options][visibility][online_only]", "NOT FOUND"))}')
print(f'Current active: {repr(all_inputs.get("product[header][active]", "NOT FOUND"))}')

# Build payload excluding known-broken fields
EXCLUDE = {
    'product[details][features][feature_value_id]',
    'product[details][features][custom_value][1]',
    'product[details][features][custom_value][2]',
    'product[pricing][priority_management][use_custom_priority]',
    'product[pricing][priority_management][priorities][0]',
    'product[pricing][priority_management][priorities][1]',
    'product[pricing][priority_management][priorities][2]',
    'product[pricing][priority_management][priorities][3]',
}
payload = {k: v for k, v in all_inputs.items() if k not in EXCLUDE}
payload['product[details][features][feature_id]'] = '0'

# THE FIX: set visibility to 'both' (catalog + search)
payload['product[options][visibility][visibility]'] = 'both'
# Also ensure online_only is off (not hidden from non-online customers)
payload['product[options][visibility][online_only]'] = '0'

payload['_token'] = edit_tok

print(f'\nSetting visibility → "both", online_only → "0"')
print(f'Payload: {len(payload)} fields')

r_save = s.post(
    f'{ADMIN}/index.php/sell/catalog/products/{PID}/edit',
    params={'_token': edit_tok},
    data=payload,
    headers={'Referer': r_edit.url},
    allow_redirects=True,
)
print(f'\nSave: {r_save.status_code}')
fv = re.search(r'data-form-valid="(\d+)"', r_save.text)
fs = re.search(r'data-form-submitted="(\d+)"', r_save.text)
print(f'form-valid={fv.group(1) if fv else "?"}  form-submitted={fs.group(1) if fs else "?"}')

errors = re.findall(r'<div[^>]*alert-danger[^>]*>(.*?)</div>', r_save.text, re.I | re.S)
for e in errors:
    t = re.sub(r'<[^>]+>', ' ', e).strip()
    t = re.sub(r'\s+', ' ', t)
    if t: print(f'ERROR: {t[:200]}')

# Verify
print('\n--- Verification ---')
r_v = s.get(f'{ADMIN}/index.php/sell/catalog/products/{PID}/edit',
            params={'_token': cat_token}, allow_redirects=True)

# Check visibility select
vis_sel_m = re.search(r'<select([^>]*)name="product\[options\]\[visibility\]\[visibility\]"[^>]*>(.*?)</select>',
                       r_v.text, re.I | re.S)
if vis_sel_m:
    body = vis_sel_m.group(2)
    selected = re.search(r'<option[^>]+selected[^>]*value="([^"]*)"', body, re.I)
    if not selected:
        selected = re.search(r'<option[^>]*value="([^"]*)"', body, re.I)
    print(f'visibility = {repr(selected.group(1) if selected else "?")}')
else:
    print('visibility select not found')

if fv and fv.group(1) == '1':
    print('\nSUCCESS: Product 386 is now visible in catalog and search.')
