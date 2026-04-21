"""
Find the actual save endpoint PS9 uses (it may be AJAX-only).
Check the JS bundle files and API routes.
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

print(f'Edit page: {len(html):,} bytes')

# 1. Find all JS script sources
scripts = re.findall(r'<script[^>]*src="([^"]+)"', html, re.I)
print(f'\nLoaded scripts ({len(scripts)}):')
for s_url in scripts:
    print(f'  {s_url[:120]}')

# 2. Find any product-form or save-related routes in the HTML
print('\n--- Save-related patterns ---')
save_patterns = re.findall(r'(?:saveUrl|save_url|formAction|form_action|submitUrl|submit_url|ajaxSave)[^\n"\']{0,200}', html, re.I)
for p in save_patterns[:5]:
    print(f'  {p[:200]}')

# 3. Find data- attributes on the product form
form_match = re.search(r'<form[^>]*name="product"[^>]*>', html, re.I)
if form_match:
    print(f'\nProduct form tag:\n  {form_match.group()[:500]}')

# 4. Look for specific PS9 product save URL patterns
ps9_save = re.findall(r'/products/\d+/(?:save|update|patch)[^\s"\'<>]{0,100}', html, re.I)
print(f'\nPS9 product save URLs: {ps9_save[:10]}')

# 5. Try the save with XHR headers to see if it returns JSON
print('\n--- Testing save with XHR headers ---')
all_inputs = {}
for m in re.finditer(r'<input[^>]+>', html, re.I):
    tag = m.group(0)
    name_m = re.search(r'\bname="([^"]+)"', tag, re.I)
    val_m  = re.search(r'\bvalue="([^"]*)"', tag, re.I)
    if name_m:
        all_inputs[name_m.group(1)] = val_m.group(1) if val_m else ''

r_xhr = s.post(
    f'{ADMIN}/index.php/sell/catalog/products/{PID}/edit',
    params={'_token': edit_tok},
    data=all_inputs,
    headers={
        'Referer': r_edit.url,
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
    },
    allow_redirects=False,
)
print(f'XHR response: {r_xhr.status_code}')
print(f'Content-Type: {r_xhr.headers.get("Content-Type", "unknown")}')
print(f'Location: {r_xhr.headers.get("Location", "none")}')
print(f'Body[:300]: {r_xhr.text[:300]}')

# 6. Look for product modules/plugins endpoint
print('\n--- Checking if PS9 has a specific categories endpoint ---')
cat_endpoints = [
    f'/index.php/sell/catalog/products/{PID}/categories',
    f'/index.php/sell/catalog/products/{PID}/update-categories',
    f'/index.php/sell/catalog/products/categories/update',
]
for ep in cat_endpoints:
    r_ep = s.get(ADMIN + ep, params={'_token': cat_token}, allow_redirects=False)
    print(f'  GET {ep}: {r_ep.status_code} Location={r_ep.headers.get("Location","")[:60]}')

# 7. Check if there's a product JSON route
print('\n--- Product JSON endpoints ---')
json_eps = [
    f'/index.php/sell/catalog/products/{PID}',
    f'/api/products/{PID}',
    f'/index.php/api/products/{PID}',
]
for ep in json_eps:
    r_ep = s.get(ADMIN + ep, params={'_token': cat_token, 'output_format': 'JSON'},
                 headers={'Accept': 'application/json'}, allow_redirects=True)
    ct = r_ep.headers.get('Content-Type', '')
    print(f'  GET {ep}: {r_ep.status_code} ct={ct[:40]} body[:100]={r_ep.text[:100]}')
