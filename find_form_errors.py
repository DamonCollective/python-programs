"""Find exactly what form errors are preventing category save."""
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

r_edit = s.get(f'{ADMIN}/index.php/sell/catalog/products/{PID}/edit',
               params={'_token': cat_token}, allow_redirects=True)
edit_tok = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r_edit.url).group(1)
html = r_edit.text

# Build payload with all inputs
payload = {}
for m in re.finditer(r'<input[^>]+>', html, re.I):
    tag = m.group(0)
    name_m = re.search(r'\bname="([^"]+)"', tag, re.I)
    val_m  = re.search(r'\bvalue="([^"]*)"', tag, re.I)
    if name_m:
        payload[name_m.group(1)] = val_m.group(1) if val_m else ''
payload['_token'] = edit_tok

# Add Theatrical category
existing_cats = {}
for m in re.finditer(r'<input[^>]*name="product\[description\]\[categories\]\[product_categories\]\[(\d+)\]\[id\]"[^>]*value="(\d+)"', html, re.I):
    existing_cats[int(m.group(1))] = m.group(2)
next_idx = max(existing_cats.keys(), default=-1) + 1
base = f'product[description][categories][product_categories][{next_idx}]'
payload[base + '[id]'] = '12'
payload[base + '[name]'] = 'Theatrical'
payload[base + '[display_name]'] = 'Theatrical'

# POST
r_post = s.post(f'{ADMIN}/index.php/sell/catalog/products/{PID}/edit',
                params={'_token': edit_tok}, data=payload,
                headers={'Referer': r_edit.url}, allow_redirects=False)
resp = r_post.text
print(f'Status: {r_post.status_code}, size: {len(resp):,}')

# Find data-form attributes
form_attrs = re.search(r'data-form-[^>]{0,300}', resp, re.I)
if form_attrs:
    print(f'Form attrs: {form_attrs.group()[:300]}')

# Find alert-success content
for m in re.finditer(r'<div[^>]*alert-success[^>]*>(.*?)</div>', resp, re.I | re.S):
    text = re.sub(r'<[^>]+>', ' ', m.group(1)).strip()
    text = re.sub(r'\s+', ' ', text)
    if text:
        print(f'SUCCESS: {text[:200]}')

# Find alert-danger content
for m in re.finditer(r'<div[^>]*alert-danger[^>]*>(.*?)</div>', resp, re.I | re.S):
    text = re.sub(r'<[^>]+>', ' ', m.group(1)).strip()
    text = re.sub(r'\s+', ' ', text)
    if text:
        print(f'DANGER: {text[:300]}')

# Find any error messages in nested structures
print('\n--- Error messages (broader search) ---')
error_texts = re.findall(r'(?:error|invalid|required|constraint)[^<]{0,300}', resp, re.I)
for t in error_texts[:15]:
    t = t.strip()
    if len(t) > 10:
        print(f'  {t[:200]}')

# Find the data-alerts-error attribute value
alerts_err = re.search(r'data-alerts-error="(\d+)"', resp)
alerts_suc = re.search(r'data-alerts-success="(\d+)"', resp)
alerts_war = re.search(r'data-alerts-warning="(\d+)"', resp)
print(f'\ndata-alerts: error={alerts_err.group(1) if alerts_err else "?"}, success={alerts_suc.group(1) if alerts_suc else "?"}, warning={alerts_war.group(1) if alerts_war else "?"}')

# Find any JSON error data in the page
json_errors = re.findall(r'"errors":\s*\[([^\]]{0,500})\]', resp, re.I)
for je in json_errors[:5]:
    print(f'JSON errors: {je[:200]}')

# Look for the section/tab that has the error
print('\n--- Tab/section with error ---')
tab_errors = re.findall(r'(?:tab|section|panel)[^>]{0,100}(?:error|invalid|danger)[^\n]{0,200}', resp, re.I)
for te in tab_errors[:5]:
    print(f'  {te[:200]}')

# Check if the categories section specifically has an error
cat_section = re.search(r'product_categories.{0,2000}', resp, re.I | re.S)
if cat_section:
    snippet = cat_section.group()[:500]
    print(f'\nCategories section snippet:\n{snippet}')

# Dump first 3000 chars of response to a file for inspection
with open('C:/Users/Damon/Desktop/save_response.html', 'w', encoding='utf-8') as f:
    f.write(resp)
print(f'\nFull response saved to save_response.html ({len(resp):,} bytes)')

# Find what part has data-form-valid=0
fv_idx = resp.find('data-form-valid')
if fv_idx >= 0:
    snippet = resp[max(0, fv_idx-100):fv_idx+200]
    print(f'\nAround data-form-valid:\n{snippet}')
