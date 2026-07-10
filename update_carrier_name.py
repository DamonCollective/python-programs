"""
Change carrier name from ICC Courier to Geniki Taxydromiki (carrier ID=8).
Uses AdminCarrierWizard (legacy PS9 carrier editor).
"""
import requests, re, sys
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
sys.stdout.reconfigure(encoding='utf-8')

ADMIN      = 'https://alegro.gr/admin875fdclzkf27m3shsg9'
EMAIL      = 'damoncollective@gmail.com'
PASSWD     = 'cultivatesandspreadslove13579' + chr(33)
CARRIER_ID = 8

NAME_NEW_EN = 'Geniki Taxydromiki'
NAME_NEW_EL = 'Geniki Taxydromiki'   # carrier[name] is a single (non-lang) field in PS

s = requests.Session()
s.headers['User-Agent'] = 'Mozilla/5.0'
s.verify = False

# --- LOGIN ---
print('Logging in...')
r = s.get(ADMIN + '/login')
ft = re.search(r'name="_token"\s+value="([^"]+)"', r.text).group(1)
r_login = s.post(ADMIN + '/login',
                 data={'email': EMAIL, 'passwd': PASSWD,
                       'stay_logged_in': '0', '_token': ft, 'submitLogin': '1'},
                 allow_redirects=True)
dash_html = r_login.text

# Extract AdminCarriers token from sidebar link
carriers_tok_m = re.search(
    r'controller=AdminCarriers&(?:amp;)?token=([A-Za-z0-9._\-]+)',
    dash_html, re.I
)
if not carriers_tok_m:
    print('ERROR: Could not find AdminCarriers token in dashboard.')
    sys.exit(1)
carriers_tok = carriers_tok_m.group(1)
print(f'AdminCarriers token: {carriers_tok[:40]}...')

# --- GET CARRIERS LIST to get Wizard token ---
r_list = s.get(ADMIN + '/index.php',
               params={'controller': 'AdminCarriers', 'token': carriers_tok},
               allow_redirects=True)
carriers_html = r_list.text
print(f'Carriers list: {r_list.status_code}, {len(carriers_html):,} bytes')

# Extract wizard token for carrier 8
wiz_tok_m = re.search(
    r'controller=AdminCarrierWizard&(?:amp;)?id_carrier=8&(?:amp;)?token=([A-Za-z0-9._\-]+)',
    carriers_html, re.I
)
if not wiz_tok_m:
    print('ERROR: Could not find wizard token for carrier 8.')
    sys.exit(1)
wiz_tok = wiz_tok_m.group(1)
print(f'Wizard token: {wiz_tok[:40]}...')

# --- OPEN WIZARD EDIT PAGE ---
print(f'\nOpening wizard for carrier {CARRIER_ID}...')
r_wiz = s.get(ADMIN + '/index.php',
              params={'controller': 'AdminCarrierWizard',
                      'id_carrier': CARRIER_ID,
                      'token': wiz_tok},
              allow_redirects=True)
wiz_html = r_wiz.text
print(f'Wizard page: {r_wiz.status_code}, {len(wiz_html):,} bytes')

# Extract all form fields
all_inputs = {}
for m in re.finditer(r'<input([^>]+)>', wiz_html, re.I):
    attrs = m.group(1)
    nm = re.search(r'\bname="([^"]+)"', attrs, re.I)
    vm = re.search(r'\bvalue="([^"]*)"', attrs, re.I)
    tp = re.search(r'\btype="([^"]+)"', attrs, re.I)
    if nm:
        t = (tp.group(1) if tp else 'text').lower()
        if t == 'checkbox':
            if 'checked' in attrs.lower():
                all_inputs[nm.group(1)] = vm.group(1) if vm else '1'
        elif t == 'radio':
            if 'checked' in attrs.lower():
                all_inputs[nm.group(1)] = vm.group(1) if vm else ''
        else:
            all_inputs[nm.group(1)] = vm.group(1) if vm else ''

for sel_m in re.finditer(r'<select([^>]*)>(.*?)</select>', wiz_html, re.I | re.S):
    attrs, body = sel_m.group(1), sel_m.group(2)
    nm = re.search(r'\bname="([^"]+)"', attrs, re.I)
    if not nm:
        continue
    sel = (re.search(r'<option[^>]+selected[^>]*value="([^"]*)"', body, re.I) or
           re.search(r'<option[^>]*value="([^"]*)"', body, re.I))
    all_inputs[nm.group(1)] = sel.group(1) if sel else ''

for ta_m in re.finditer(r'<textarea([^>]*)>(.*?)</textarea>', wiz_html, re.I | re.S):
    attrs, body = ta_m.group(1), ta_m.group(2)
    nm = re.search(r'\bname="([^"]+)"', attrs, re.I)
    if nm:
        all_inputs[nm.group(1)] = body.strip()

print(f'Found {len(all_inputs)} form fields.')

# Show current name / delay fields
print('\nCurrent name/delay fields:')
for k, v in sorted(all_inputs.items()):
    if any(x in k.lower() for x in ['name', 'delay']):
        print(f'  {k} = {v!r}')

# --- MAKE THE CHANGE ---
payload = dict(all_inputs)

old_name = payload.get('name', payload.get('carrier[name]', '?'))
payload['name'] = NAME_NEW_EN
payload.pop('carrier[name]', None)
print(f'\nChanging name: {old_name!r} -> {NAME_NEW_EN!r}')

# Also update delay fields if they mention ICC Courier
for k in list(payload):
    if 'delay' in k.lower():
        v = payload[k]
        new_v = re.sub(r'(?i)\bICC\s*Courier\b', NAME_NEW_EN, v)
        if new_v != v:
            payload[k] = new_v
            print(f'Updating delay {k}: {v!r} -> {new_v!r}')

# The wizard needs submitCarrier to save
payload['submitCarrier'] = '1'
payload['token'] = wiz_tok

# --- SAVE ---
print('\nSaving...')
r_save = s.post(ADMIN + '/index.php',
                params={'controller': 'AdminCarrierWizard', 'token': wiz_tok},
                data=payload,
                headers={'Referer': r_wiz.url},
                allow_redirects=True,
                timeout=20)

print(f'Response: {r_save.status_code}, {len(r_save.text):,} bytes')
print(f'URL: {r_save.url[-80:]}')

# Check result
save_html = r_save.text
if 'alert-success' in save_html or 'conf_carrier_saved' in save_html.lower():
    print('SUCCESS: Carrier saved.')
elif 'alert-danger' in save_html or 'error' in save_html.lower():
    errs = re.findall(r'alert-danger[^>]*>(.*?)</div', save_html, re.S | re.I)
    print('Possible errors:', [re.sub(r'<[^>]+>', '', e).strip()[:100] for e in errs[:3]])
else:
    # Check if the name now appears on the page
    new_name_found = NAME_NEW_EN.lower() in save_html.lower()
    old_name_found = 'icc courier' in save_html.lower()
    print(f'New name on page: {new_name_found}, Old name still there: {old_name_found}')

# Verify by re-reading the carrier
print('\nVerifying...')
r_verify = s.get(ADMIN + '/index.php',
                 params={'controller': 'AdminCarriers', 'token': carriers_tok},
                 allow_redirects=True)
verify_html = r_verify.text
geniki_found = 'Geniki Taxydromiki' in verify_html
icc_found = 'ICC Courier' in verify_html
print(f'Carriers list: Geniki Taxydromiki found={geniki_found}, ICC Courier still there={icc_found}')
