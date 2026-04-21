"""
Explore feature values endpoint and find a valid feature_id combination.
Also try full form POST without product[details] section.
"""
import requests, re, sys, json
sys.stdout.reconfigure(encoding='utf-8')

ADMIN = 'https://alegro.gr/admin875fdclzkf27m3shsg9'
PID = 386

s = requests.Session()
s.headers['User-Agent'] = 'Mozilla/5.0'

r = s.get(ADMIN + '/login')
ft = re.search(r'name="_token"\s+value="([^"]+)"', r.text).group(1)
passwd = 'cultivatesandspreadslove13579' + chr(33)
r = s.post(ADMIN + '/login', data={'email':'damoncollective@gmail.com','passwd':passwd,'stay_logged_in':'0','_token':ft,'submitLogin':'1'}, allow_redirects=True)
m = re.search(r'[?&]token=([A-Za-z0-9._\-]+)', r.url)
legacy_tok = m.group(1) if m else ''
r2 = s.get(ADMIN + '/index.php', params={'controller':'AdminProducts','token':legacy_tok}, allow_redirects=True)
cat_token = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r2.url).group(1)

# 1. Check feature values endpoint
print('=== Feature values endpoints ===')
for fid in [1, 2]:
    r_fv = s.get(f'{ADMIN}/index.php/sell/catalog/features/values',
                 params={'_token': cat_token, 'feature_id': fid},
                 headers={'Accept': 'application/json, */*'},
                 allow_redirects=True)
    print(f'  feature_id={fid}: {r_fv.status_code} ct={r_fv.headers.get("Content-Type","")[:30]}')
    if r_fv.text[:1] in ('[', '{'):
        data = json.loads(r_fv.text)
        print(f'  → {data[:3] if isinstance(data, list) else data}')
    else:
        print(f'  → {r_fv.text[:100]}')

# 2. Fetch edit page for product 386
r_edit = s.get(f'{ADMIN}/index.php/sell/catalog/products/{PID}/edit',
               params={'_token': cat_token}, allow_redirects=True)
edit_tok = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r_edit.url).group(1)
html = r_edit.text
form_tok = re.search(r'name="product\[_token\]"[^>]*value="([^"]+)"', html).group(1)

# Get all inputs
all_inputs = {}
for m in re.finditer(r'<input[^>]+>', html, re.I):
    tag = m.group(0)
    nm = re.search(r'\bname="([^"]+)"', tag, re.I)
    vm = re.search(r'\bvalue="([^"]*)"', tag, re.I)
    if nm:
        all_inputs[nm.group(1)] = vm.group(1) if vm else ''

print(f'\nProduct 386 inputs: {len(all_inputs)}')
print('Current names:')
for k, v in all_inputs.items():
    if 'name][' in k:
        print(f'  {k} = {v[:60]}')

# 3. Try full form POST without product[details] section
print('\n=== Test: full form minus product[details] ===')
payload_no_details = {k: v for k, v in all_inputs.items() if not k.startswith('product[details]')}
payload_no_details['_token'] = edit_tok

# Add the descriptions
EN, EL = 1, 2
NAME_EN = "Ioannis Kapodistrias Theatrical Wig | Stage Wig | Made in Greece"
NAME_EL = "Περούκα Ιωάννης Καποδίστριας | Θεατρική Ιστορική Περούκα | Ελλάδα"

payload_no_details[f'product[header][name][{EN}]'] = NAME_EN
payload_no_details[f'product[header][name][{EL}]'] = NAME_EL
payload_no_details[f'product[header][type]'] = all_inputs.get('product[header][type]', 'standard')

print(f'Fields: {len(payload_no_details)} (excluded {len(all_inputs) - len(payload_no_details)} product[details] fields)')

r_save = s.post(
    f'{ADMIN}/index.php/sell/catalog/products/{PID}/edit',
    params={'_token': edit_tok},
    data=payload_no_details,
    headers={'Referer': r_edit.url},
    allow_redirects=False,
)
print(f'Status: {r_save.status_code}  Location: {r_save.headers.get("Location", "NONE")}')
fv = re.search(r'data-form-(?:valid|submitted)="(\d+)"', r_save.text)
fv2 = re.findall(r'data-form-(valid|submitted)="(\d+)"', r_save.text)
print(f'Form state: {fv2}')

invalid = re.findall(r'name="([^"]+)"[^>]*class="[^"]*is-invalid', r_save.text, re.I)
print(f'Invalid fields: {invalid[:5]}')

errors = re.findall(r'<div[^>]*alert-danger[^>]*>(.*?)</div>', r_save.text, re.I | re.S)
for e in errors:
    t = re.sub(r'<[^>]+>', ' ', e).strip()
    t = re.sub(r'\s+', ' ', t)
    if t: print(f'ERROR: {t[:200]}')

# 4. Verify
if r_save.status_code == 302 or r_save.headers.get('Location'):
    print('\nREDIRECT → Save likely successful!')
    r_v = s.get(f'{ADMIN}/index.php/sell/catalog/products/{PID}/edit', params={'_token': cat_token}, allow_redirects=True)
    nm = re.search(f'name="product\\[header\\]\\[name\\]\\[{EN}\\]"[^>]*value="([^"]*)"', r_v.text)
    print(f'Verified EN name: {nm.group(1)[:80] if nm else "not found"}')
