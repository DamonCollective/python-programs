"""
Update global in-stock delivery time to '1-2 days' / '1-2 ημέρες'
via the 'stock' sub-form of AdminPPreferences (PS9 Symfony route).
"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8')

ADMIN = 'https://alegro.gr/admin875fdclzkf27m3shsg9'

DELIVERY_EN = 'Delivery in 1-2 days'
DELIVERY_EL = 'Παράδοση σε 1 - 2 ημέρες'

s = requests.Session()
s.headers['User-Agent'] = 'Mozilla/5.0'

# Login
r = s.get(ADMIN + '/login')
ft = re.search(r'name="_token"\s+value="([^"]+)"', r.text).group(1)
passwd = 'cultivatesandspreadslove13579' + chr(33)
r = s.post(ADMIN + '/login', data={'email':'damoncollective@gmail.com','passwd':passwd,
           'stay_logged_in':'0','_token':ft,'submitLogin':'1'}, allow_redirects=True)
m = re.search(r'[?&]token=([A-Za-z0-9._\-]+)', r.url)
legacy_tok = m.group(1) if m else ''
print('Logged in OK')

# Fetch Product Preferences page
r_page = s.get(ADMIN + '/index.php',
               params={'controller': 'AdminPPreferences', 'token': legacy_tok},
               allow_redirects=True)
html = r_page.text
print(f'Page: {r_page.status_code} ({len(html):,} bytes)')

# Extract the 'stock' form action URL
stock_form_m = re.search(r'<form[^>]+name="stock"[^>]*action="([^"]+)"', html, re.I)
if not stock_form_m:
    print('ERROR: stock form not found')
    sys.exit(1)
stock_action = stock_form_m.group(1)
if stock_action.startswith('/'):
    stock_action = 'https://alegro.gr' + stock_action
print(f'Stock form action: {stock_action[-80:]}')

# Collect inputs within the stock form
stock_form_body_m = re.search(r'<form[^>]+name="stock"[^>]*>(.*?)</form>', html, re.I | re.S)
if not stock_form_body_m:
    print('ERROR: stock form body not found')
    sys.exit(1)
stock_html = stock_form_body_m.group(1)

payload = {}
for m in re.finditer(r'<input[^>]+>', stock_html, re.I):
    tag = m.group(0)
    nm = re.search(r'\bname="([^"]+)"', tag, re.I)
    vm = re.search(r'\bvalue="([^"]*)"', tag, re.I)
    tp = re.search(r'\btype="([^"]*)"', tag, re.I)
    if not nm:
        continue
    t = tp.group(1).lower() if tp else 'text'
    if t == 'checkbox':
        if 'checked' in tag.lower():
            payload[nm.group(1)] = vm.group(1) if vm else 'on'
    elif t == 'radio':
        if 'checked' in tag.lower():
            payload[nm.group(1)] = vm.group(1) if vm else ''
    else:
        payload[nm.group(1)] = vm.group(1) if vm else ''

for ta_m in re.finditer(r'<textarea[^>]*name="([^"]+)"[^>]*>(.*?)</textarea>', stock_html, re.I | re.S):
    payload[ta_m.group(1)] = ta_m.group(2)

print('\nCurrent values:')
print(f'  stock[delivery_time][1]     = {repr(payload.get("stock[delivery_time][1]", "NOT FOUND"))}')
print(f'  stock[delivery_time][2]     = {repr(payload.get("stock[delivery_time][2]", "NOT FOUND"))}')
print(f'  stock[oos_delivery_time][1] = {repr(payload.get("stock[oos_delivery_time][1]", "NOT FOUND"))}')
print(f'  stock[oos_delivery_time][2] = {repr(payload.get("stock[oos_delivery_time][2]", "NOT FOUND"))}')

# Update delivery time
payload['stock[delivery_time][1]'] = DELIVERY_EN
payload['stock[delivery_time][2]'] = DELIVERY_EL

print(f'\nSubmitting {len(payload)} fields to stock form...')

r_save = s.post(
    stock_action,
    data=payload,
    headers={'Referer': r_page.url},
    allow_redirects=True,
)
print(f'Save: {r_save.status_code} → {r_save.url[-70:]}')

errors = re.findall(r'<div[^>]*class="[^"]*alert-danger[^"]*"[^>]*>(.*?)</div>', r_save.text, re.I | re.S)
for e in errors:
    t = re.sub(r'<[^>]+>', ' ', e).strip()
    t = re.sub(r'\s+', ' ', t)
    if t: print(f'ERROR: {t[:200]}')

success = re.search(r'alert-success', r_save.text, re.I)
print(f'Success banner: {bool(success)}')

# Verify
print('\n--- Verification ---')
r_v = s.get(ADMIN + '/index.php',
            params={'controller': 'AdminPPreferences', 'token': legacy_tok},
            allow_redirects=True)

v1 = re.search(r'name="stock\[delivery_time\]\[1\]"[^>]*value="([^"]*)"', r_v.text, re.I)
v2 = re.search(r'name="stock\[delivery_time\]\[2\]"[^>]*value="([^"]*)"', r_v.text, re.I)
print(f'  delivery_time[1] = {repr(v1.group(1) if v1 else "not found")}')
print(f'  delivery_time[2] = {repr(v2.group(1) if v2 else "not found")}')

en_ok = v1 and DELIVERY_EN in v1.group(1)
el_ok = v2 and DELIVERY_EL in v2.group(1)
print(f'\nEN saved: {en_ok}')
print(f'EL saved: {el_ok}')
if en_ok and el_ok:
    print('\nSUCCESS: Global in-stock delivery time → "1-2 days" / "1-2 ημέρες" for all products.')
