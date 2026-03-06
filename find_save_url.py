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
print('Logged in:', 'login' not in r.url)

# Fetch JS bundle
js_url = ADMIN + '/themes/new-theme/public/create_product.bundle.js?9.0.0'
print('Fetching JS bundle...')
rj = s.get(js_url)
js = rj.text
print(f'Bundle size: {len(js):,} chars')

# Search for /sell/catalog/products routes
routes = re.findall(r'["/]sell/catalog/products[^"\'`\s]{0,150}', js)
unique_routes = sorted(set(r2 for r2 in routes if 'node_modules' not in r2))
print(f'\nProduct routes in bundle ({len(unique_routes)} unique):')
for route in unique_routes[:30]:
    print(' ', route[:140])

# Search for save/submit actions
print('\nSave/submit patterns:')
for keyword in ['save', 'submit', 'create', 'store']:
    matches = re.findall(r'.{0,60}' + keyword + r'.{0,60}', js, re.I)
    for m2 in matches:
        if 'url' in m2.lower() or 'route' in m2.lower() or '/sell/' in m2 or 'product' in m2.lower():
            print(f'  [{keyword}]', m2[:140])
            break
