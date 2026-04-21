"""Find the PS9 page where global delivery time is configured."""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8')

ADMIN = 'https://alegro.gr/admin875fdclzkf27m3shsg9'

s = requests.Session()
s.headers['User-Agent'] = 'Mozilla/5.0'

r = s.get(ADMIN + '/login')
ft = re.search(r'name="_token"\s+value="([^"]+)"', r.text).group(1)
passwd = 'cultivatesandspreadslove13579' + chr(33)
r = s.post(ADMIN + '/login', data={'email':'damoncollective@gmail.com','passwd':passwd,
           'stay_logged_in':'0','_token':ft,'submitLogin':'1'}, allow_redirects=True)
m = re.search(r'[?&]token=([A-Za-z0-9._\-]+)', r.url)
legacy_tok = m.group(1) if m else ''
print('Logged in OK')

# Try legacy controller routes
legacy_pages = [
    'AdminOrderPreferences',
    'AdminPPreferences',
    'AdminShipping',
    'AdminDelivery',
]
for ctrl in legacy_pages:
    r_p = s.get(ADMIN + '/index.php', params={'controller': ctrl, 'token': legacy_tok}, allow_redirects=True)
    final_url = r_p.url
    # Get the new _token from redirect
    tok_m = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', final_url)
    new_tok = tok_m.group(1) if tok_m else ''
    print(f'{ctrl}: {r_p.status_code} ({len(r_p.text):,}b) url={final_url[-60:]}')
    if r_p.status_code == 200 and 'delivery' in r_p.text.lower() and len(r_p.text) > 5000:
        print(f'  → Contains "delivery"!')
        # Find delivery inputs
        for m2 in re.finditer(r'<(?:input|textarea)[^>]*name="([^"]+)"', r_p.text, re.I):
            if 'delivery' in m2.group(1).lower() or 'PS_DELIVERY' in m2.group(1):
                print(f'    FIELD: {m2.group(1)}')

# Try Symfony routes for shop params
r2 = s.get(ADMIN + '/index.php', params={'controller':'AdminProducts','token':legacy_tok}, allow_redirects=True)
cat_token = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r2.url).group(1)

symfony_paths = [
    '/index.php/configure/shop-parameters/general/',
    '/index.php/configure/shop-parameters/order-settings/general',
    '/index.php/configure/shop-parameters/order-settings/',
    '/index.php/configure/shop-parameters/product-preferences/general',
    '/index.php/configure/shop-parameters/product-preferences/',
    '/index.php/configure/advanced/parameters/',
]
for path in symfony_paths:
    r_p = s.get(ADMIN + path, params={'_token': cat_token}, allow_redirects=True)
    print(f'{path}: {r_p.status_code} ({len(r_p.text):,}b)')
    if r_p.status_code == 200 and 'delivery' in r_p.text.lower() and len(r_p.text) > 5000:
        print(f'  → Contains "delivery"! URL: {r_p.url[-80:]}')
