"""Deep diagnostic: what does the save response actually contain?"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8')

ADMIN = 'https://alegro.gr/admin875fdclzkf27m3shsg9'
THEATRICAL_ID   = 12
THEATRICAL_NAME = 'Theatrical'
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

# Fetch edit page
r_edit = s.get(f'{ADMIN}/index.php/sell/catalog/products/{PID}/edit',
               params={'_token': cat_token}, allow_redirects=True)
edit_tok = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r_edit.url).group(1)
print(f'Edit page: {len(r_edit.text):,} bytes, tok={edit_tok[:40]}')

existing = get_categories_flexible(r_edit.text)
next_idx = max(existing.keys(), default=-1) + 1
print(f'Existing cats: {existing}')

# Build payload
payload = get_all_inputs(r_edit.text)
base = f'product[description][categories][product_categories][{next_idx}]'
payload[base + '[id]']           = str(THEATRICAL_ID)
payload[base + '[name]']         = THEATRICAL_NAME
payload[base + '[display_name]'] = THEATRICAL_NAME
payload['_token'] = edit_tok

print(f'Payload size: {len(payload)} fields')
print(f'product[_token] = {payload.get("product[_token]", "MISSING")[:60]}')
print(f'_token = {edit_tok[:40]}')

# Show the new category fields we're adding
for k, v in payload.items():
    if 'product_categories][3]' in k:
        print(f'  New field: {k} = {v}')

# Save WITHOUT redirects to see the raw redirect
r_save_raw = s.post(
    f'{ADMIN}/index.php/sell/catalog/products/{PID}/edit',
    params={'_token': edit_tok},
    data=payload,
    headers={'Referer': r_edit.url},
    allow_redirects=False,
)
print(f'\nRaw save: status={r_save_raw.status_code}')
print(f'Location: {r_save_raw.headers.get("Location", "none")}')
print(f'Body size: {len(r_save_raw.text):,}')

# Now with redirects
r_save = s.post(
    f'{ADMIN}/index.php/sell/catalog/products/{PID}/edit',
    params={'_token': edit_tok},
    data=payload,
    headers={'Referer': r_edit.url},
    allow_redirects=True,
)
print(f'\nWith redirects: {r_save.status_code} → {r_save.url}')
print(f'Response size: {len(r_save.text):,}')

# Check for any flash messages (success or error)
flash_msgs = re.findall(r'<div[^>]*(?:alert-success|alert-danger|alert-warning)[^>]*>(.*?)</div>', r_save.text, re.I | re.S)
print(f'\nFlash messages ({len(flash_msgs)}):')
for msg in flash_msgs:
    text = re.sub(r'<[^>]+>', ' ', msg).strip()
    text = re.sub(r'\s+', ' ', text)
    if text:
        print(f'  [{text[:300]}]')

# Check what categories the response page shows
cats_in_response = get_categories_flexible(r_save.text)
print(f'\nCategories in save response: {cats_in_response}')

# Now re-fetch fresh
r_fresh = s.get(f'{ADMIN}/index.php/sell/catalog/products/{PID}/edit',
                params={'_token': cat_token}, allow_redirects=True)
cats_fresh = get_categories_flexible(r_fresh.text)
print(f'Categories in fresh re-fetch: {cats_fresh}')

# Look for any AJAX/API endpoints in the page related to categories
print('\n--- Looking for PS9 API endpoints ---')
api_patterns = re.findall(r'(?:fetch|axios|api_url|route)[^\n]{0,200}categor[^\n]{0,100}', r_edit.text, re.I)
for p in api_patterns[:5]:
    print(f'  {p[:200]}')

# Look for the form action
form_actions = re.findall(r'<form[^>]*action="([^"]*)"[^>]*>', r_edit.text, re.I)
print(f'\nForm actions: {form_actions[:5]}')

# Look for the form that contains product[_token]
form_m = re.search(r'(<form[^>]*>(?:(?!<form).)*?product\[_token\](?:(?!</form>).)*?</form>)', r_edit.text, re.I | re.S)
if form_m:
    form_html = form_m.group(1)[:500]
    print(f'\nForm containing product[_token]:\n{form_html}')
else:
    # Find any form tag
    forms = re.findall(r'<form[^>]{0,300}>', r_edit.text, re.I)
    print(f'\nAll form tags ({len(forms)}):')
    for f in forms[:5]:
        print(f'  {f[:200]}')
