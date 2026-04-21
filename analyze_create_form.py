import requests
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

ADMIN = 'https://alegro.gr/admin875fdclzkf27m3shsg9'
s = requests.Session()
s.headers['User-Agent'] = 'Mozilla/5.0'

# Login
r = s.get(ADMIN + '/login')
ft = re.search(r'name="_token"\s+value="([^"]+)"', r.text).group(1)
passwd = 'cultivatesandspreadslove13579' + chr(33)
r = s.post(ADMIN + '/login', data={
    'email': 'damoncollective@gmail.com',
    'passwd': passwd,
    'stay_logged_in': '0',
    '_token': ft,
    'submitLogin': '1',
}, allow_redirects=True)
m = re.search(r'[?&]token=([A-Za-z0-9._\-]+)', r.url)
legacy_token = m.group(1) if m else ''

# Get catalog to find create URL
r2 = s.get(ADMIN + '/index.php', params={'controller': 'AdminProducts', 'token': legacy_token}, allow_redirects=True)
create_token = re.search(r'/products/create\?_token=([A-Za-z0-9._\-]+)', r2.text).group(1)

# Fetch create page
r3 = s.get(ADMIN + '/index.php/sell/catalog/products/create', params={'_token': create_token}, allow_redirects=True)
html = r3.text
url_token = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r3.url)
url_token = url_token.group(1) if url_token else create_token
print('Page URL:', r3.url[:100])

# All <form> tags
forms = re.findall(r'<form[^>]{0,500}>', html, re.I)
print(f'\nForms ({len(forms)}):')
for f in forms:
    print(' ', f[:200])

# All <input> fields
inputs = re.findall(r'<input[^>]{0,300}>', html, re.I)
print(f'\nInputs ({len(inputs)}):')
for inp in inputs[:30]:
    name = re.search(r'name="([^"]+)"', inp)
    val = re.search(r'value="([^"]*)"', inp)
    typ = re.search(r'type="([^"]+)"', inp)
    if name:
        print(f'  {typ.group(1) if typ else "?"}: {name.group(1)} = {val.group(1)[:60] if val else "(none)"}')

# All data-* attributes on divs/components
data_attrs = re.findall(r'<[a-z][^>]*\s(data-[a-z][^>]{0,400})>', html, re.I)
print(f'\nData attributes (first 20):')
for da in data_attrs[:20]:
    print(' ', da[:200])

# JavaScript vars that contain route/URL info
print('\nJS route vars:')
js_vars = re.findall(r'(?:router|routes|url|baseUrl|apiUrl)[^;]{0,300}', html, re.I)
for jv in js_vars[:5]:
    if '/sell/' in jv or 'product' in jv.lower():
        print(' ', jv[:250])
