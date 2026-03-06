"""
Create a webservice API key then use it to update product 386 via REST API.
"""
import requests, re, sys, json
sys.stdout.reconfigure(encoding='utf-8')

BASE  = 'https://alegro.gr'
ADMIN = BASE + '/admin875fdclzkf27m3shsg9'
PID   = 386

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

# ── Step 1: Get webservice-keys/new page ──────────────────────────────────────
r_ws_list = s.get(ADMIN + '/index.php', params={'controller':'AdminWebservice','token':legacy_tok}, allow_redirects=True)
ws_tok_m = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r_ws_list.url)
ws_tok = ws_tok_m.group(1) if ws_tok_m else cat_token

r_new = s.get(f'{ADMIN}/index.php/configure/advanced/webservice-keys/new',
              params={'_token': ws_tok}, allow_redirects=True)
new_url = r_new.url
new_tok_m = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', new_url)
new_tok = new_tok_m.group(1) if new_tok_m else ws_tok
print(f'New key page: {r_new.status_code}, {len(r_new.text):,} bytes')

# Parse the create form
form_inputs = {}
for m in re.finditer(r'<input[^>]+>', r_new.text, re.I):
    tag = m.group(0)
    nm = re.search(r'\bname="([^"]+)"', tag, re.I)
    vm = re.search(r'\bvalue="([^"]*)"', tag, re.I)
    if nm:
        form_inputs[nm.group(1)] = vm.group(1) if vm else ''

print('Form inputs:')
for k, v in form_inputs.items():
    print(f'  {k} = {repr(v[:80])}')

# Find the form CSRF token
form_csrf_key = [k for k in form_inputs if k.endswith('[_token]')]
form_csrf = form_inputs.get(form_csrf_key[0], '') if form_csrf_key else ''
print(f'Form CSRF key: {form_csrf_key}')

# Find permission checkboxes (permissions[products][GET], [PUT], etc.)
perm_checks = re.findall(
    r'<input[^>]*type="checkbox"[^>]*name="([^"]+)"[^>]*value="([^"]*)"',
    r_new.text, re.I
)
print(f'\nPermission checkboxes ({len(perm_checks)}):')
for name, val in perm_checks[:20]:
    print(f'  {name} = {val}')

# ── Step 2: Generate a fixed API key and create the account ───────────────────
API_KEY = 'ALEGRO9KAPODISTRIAS2026UPDATE01'  # 32 chars, all uppercase alphanumeric

# Build payload for creating webservice key
payload = dict(form_inputs)
payload['_token'] = new_tok

# Set the key
if 'webservice_account[key]' in payload:
    payload['webservice_account[key]'] = API_KEY
elif 'api_access[key]' in payload:
    payload['api_access[key]'] = API_KEY

# Set description
if 'webservice_account[description]' in payload:
    payload['webservice_account[description]'] = 'Temp key for product update'
elif 'api_access[description]' in payload:
    payload['api_access[description]'] = 'Temp key for product update'

# Enable the key
if 'webservice_account[is_enabled]' in form_inputs:
    payload['webservice_account[is_enabled]'] = '1'

# Grant permissions for products (GET, PUT, POST, PATCH, DELETE)
# Add all permission checkboxes for products
for name, val in perm_checks:
    if 'product' in name.lower():
        payload[name] = val  # check all product-related permissions

print(f'\nCreating webservice key with {len(payload)} fields')
print(f'API_KEY: {API_KEY}')

r_create = s.post(
    f'{ADMIN}/index.php/configure/advanced/webservice-keys/new',
    params={'_token': new_tok},
    data=payload,
    headers={'Referer': r_new.url},
    allow_redirects=True,
)
print(f'Create: {r_create.status_code} → {r_create.url[:100]}')

errors_create = re.findall(r'<div[^>]*alert-danger[^>]*>(.*?)</div>', r_create.text, re.I | re.S)
for e in errors_create:
    t = re.sub(r'<[^>]+>', ' ', e).strip()
    t = re.sub(r'\s+', ' ', t)
    if t: print(f'ERROR: {t[:200]}')

success_create = re.search(r'alert-success', r_create.text, re.I)
print(f'Success indicator: {bool(success_create)}')

# ── Step 3: Try to use the key ────────────────────────────────────────────────
print('\n--- Testing API key ---')
r_api = requests.get(f'{BASE}/api/products/{PID}',
                     auth=(API_KEY, ''),
                     params={'output_format': 'JSON'},
                     headers={'Accept': 'application/json'})
print(f'GET /api/products/{PID}: {r_api.status_code}')
print(f'Body[:300]: {r_api.text[:300]}')
