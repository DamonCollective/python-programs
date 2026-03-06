"""Remove 'on sale' badge from product 386."""
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

r_edit = s.get(f'{ADMIN}/index.php/sell/catalog/products/{PID}/edit',
               params={'_token': cat_token}, allow_redirects=True)
edit_tok = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r_edit.url).group(1)
html = r_edit.text

# Simple input collection (same approach as update_386_final.py)
all_inputs = {}
for m in re.finditer(r'<input[^>]+>', html, re.I):
    tag = m.group(0)
    nm = re.search(r'\bname="([^"]+)"', tag, re.I)
    vm = re.search(r'\bvalue="([^"]*)"', tag, re.I)
    if nm:
        all_inputs[nm.group(1)] = vm.group(1) if vm else ''

for sel_m in re.finditer(r'<select([^>]*)>(.*?)</select>', html, re.I | re.S):
    attrs, body = sel_m.group(1), sel_m.group(2)
    nm = re.search(r'\bname="([^"]+)"', attrs, re.I)
    if not nm or 'paginator' in nm.group(1): continue
    selected = re.search(r'<option[^>]+selected[^>]*value="([^"]*)"', body, re.I)
    if not selected:
        selected = re.search(r'<option[^>]*value="([^"]*)"', body, re.I)
    all_inputs[nm.group(1)] = selected.group(1) if selected else ''

print(f'Current on_sale = {repr(all_inputs.get("product[pricing][on_sale]", "?"))}')

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

# THE FIX: for Symfony checkboxes, omitting the field = unchecked (false)
payload.pop('product[pricing][on_sale]', None)
payload['_token'] = edit_tok

r_save = s.post(
    f'{ADMIN}/index.php/sell/catalog/products/{PID}/edit',
    params={'_token': edit_tok},
    data=payload,
    headers={'Referer': r_edit.url},
    allow_redirects=True,
)
fv = re.search(r'data-form-valid="(\d+)"', r_save.text)
print(f'Save: {r_save.status_code}  form-valid={fv.group(1) if fv else "?"}')

errors = re.findall(r'<div[^>]*alert-danger[^>]*>(.*?)</div>', r_save.text, re.I | re.S)
for e in errors:
    t = re.sub(r'<[^>]+>', ' ', e).strip()
    t = re.sub(r'\s+', ' ', t)
    if t: print(f'ERROR: {t[:200]}')

# Verify
r_v = s.get(f'{ADMIN}/index.php/sell/catalog/products/{PID}/edit',
            params={'_token': cat_token}, allow_redirects=True)
all_v = {}
for m in re.finditer(r'<input[^>]+>', r_v.text, re.I):
    nm = re.search(r'\bname="([^"]+)"', m.group(0), re.I)
    vm = re.search(r'\bvalue="([^"]*)"', m.group(0), re.I)
    if nm: all_v[nm.group(1)] = vm.group(1) if vm else ''

# Correct verification: check if checkbox has 'checked' attribute
checked = re.search(r'name="product\[pricing\]\[on_sale\]"[^>]*checked', r_v.text, re.I)
print(f'on_sale still checked: {bool(checked)}')
if not checked and fv and fv.group(1) == '1':
    print('SUCCESS: "με εκπτωση" badge removed from product 386.')
