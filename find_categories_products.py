"""Find the 'theatrikes' category and all related hero wig/moustache products."""
import requests, re, sys, json
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
print('Logged in:', 'login' not in r.url)

# Get catalog to get a valid Symfony _token
r2 = s.get(ADMIN + '/index.php', params={'controller':'AdminProducts','token':legacy_tok}, allow_redirects=True)
cat_token_m = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r2.url)
cat_token = cat_token_m.group(1) if cat_token_m else legacy_tok

# ── Search for 'theatrikes' category ──────────────────────────────────────────
print('\n=== CATEGORIES ===')
r_cat = s.get(ADMIN + '/index.php', params={'controller':'AdminCategories','token':legacy_tok}, allow_redirects=True)
cat_page_token = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r_cat.url)
cat_page_token = cat_page_token.group(1) if cat_page_token else legacy_tok
print(f'Category page size: {len(r_cat.text)} bytes')

# Search for theatrikes in the category list HTML
theatr = re.findall(r'.{0,200}(?:theatrik|θεατρ|ΘΕΑΤΡ).{0,200}', r_cat.text, re.I)
for t in theatr[:10]:
    print(t[:300])

# Also try the category API endpoint
r_cat_api = s.get(ADMIN + '/index.php/sell/catalog/categories', params={'_token': cat_token}, allow_redirects=True)
print(f'\nCategories (Symfony) page size: {len(r_cat_api.text)}')
theatr2 = re.findall(r'.{0,100}(?:theatrik|θεατρ|ΘΕΑΤΡ).{0,100}', r_cat_api.text, re.I)
for t in theatr2[:10]:
    print(t[:250])

# Try to find category IDs from the page
cat_ids = re.findall(r'id_category["\s=:]+(\d+)[^"]*(?:theatrik|θεατρ)', r_cat.text, re.I)
print(f'\nCategory IDs with theatrik: {cat_ids}')

# ── Search for products: Diakos, Karaiskakis, Kolokotronis ────────────────────
print('\n=== PRODUCTS ===')
for keyword in ['diakos', 'karaiskakis', 'kolokotronis', 'kapodistrias',
                'διακος', 'καραισκακης', 'κολοκοτρωνης', 'moustache', 'μουστακι']:
    r_search = s.get(ADMIN + '/index.php', params={
        'controller': 'AdminProducts',
        'token': legacy_tok,
        'action': 'search',
        's': keyword,
    }, allow_redirects=True)
    # Find product rows
    rows = re.findall(r'id_product["\s=:]+(\d+)[^"<]{0,200}(?:' + keyword + r')', r_search.text, re.I)
    if rows:
        print(f'  [{keyword}] product IDs: {rows}')

# Try the product search via the catalog page with a search filter
for keyword in ['diakos', 'karaiskakis', 'kolokotroni', 'kapodistria', 'moustache', 'mustache']:
    r_s = s.get(ADMIN + '/index.php/sell/catalog/products', params={
        '_token': cat_token,
        'product[filters][name]': keyword,
    }, allow_redirects=True)
    pids = re.findall(r'/products/(\d+)/edit', r_s.text)
    if pids:
        print(f'  [{keyword}] Symfony search → IDs: {list(set(pids))[:10]}')
