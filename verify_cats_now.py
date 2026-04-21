"""Quick verification: did the PATCH approach actually save category 12 to product 265?"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8')

ADMIN = 'https://alegro.gr/admin875fdclzkf27m3shsg9'

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

def get_cats(html):
    cats = {}
    for m in re.finditer(r'<input[^>]*name="product\[description\]\[categories\]\[product_categories\]\[(\d+)\]\[id\]"[^>]*value="(\d+)"', html, re.I):
        cats[int(m.group(1))] = m.group(2)
    for m in re.finditer(r'<input[^>]*value="(\d+)"[^>]*name="product\[description\]\[categories\]\[product_categories\]\[(\d+)\]\[id\]"', html, re.I):
        cats[int(m.group(2))] = m.group(1)
    return cats

for pid in [265, 266, 267, 268, 269, 270, 386]:
    r_v = s.get(f'{ADMIN}/index.php/sell/catalog/products/{pid}/edit',
                params={'_token': cat_token}, allow_redirects=True)
    cats = get_cats(r_v.text)
    has12 = '12' in cats.values()
    mark = '✓' if has12 else '✗'
    print(f'  {mark} Product {pid}: {list(cats.values())}')
