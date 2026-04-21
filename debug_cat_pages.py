"""Debug: check what pages look like for each product, then try category API."""
import requests, re, sys, json
sys.stdout.reconfigure(encoding='utf-8')

ADMIN = 'https://alegro.gr/admin875fdclzkf27m3shsg9'
PRODUCTS = [265, 266, 267, 268, 269, 270, 386]
THEATRICAL_ID = 12

s = requests.Session()
s.headers['User-Agent'] = 'Mozilla/5.0'

# Login
r = s.get(ADMIN + '/login')
ft = re.search(r'name="_token"\s+value="([^"]+)"', r.text).group(1)
passwd = 'cultivatesandspreadslove13579' + chr(33)
r = s.post(ADMIN + '/login', data={'email':'damoncollective@gmail.com','passwd':passwd,'stay_logged_in':'0','_token':ft,'submitLogin':'1'}, allow_redirects=True)
m = re.search(r'[?&]token=([A-Za-z0-9._\-]+)', r.url)
legacy_tok = m.group(1) if m else ''

# Get catalog token
r2 = s.get(ADMIN + '/index.php', params={'controller':'AdminProducts','token':legacy_tok}, allow_redirects=True)
cat_token = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r2.url).group(1)
print(f'Cat token: {cat_token[:60]}')

# Check page sizes and category data for each product
for pid in PRODUCTS:
    r_edit = s.get(f'{ADMIN}/index.php/sell/catalog/products/{pid}/edit',
                   params={'_token': cat_token}, allow_redirects=True)
    cats = re.findall(
        r'name="product\[description\]\[categories\]\[product_categories\]\[(\d+)\]\[id\]"\s+value="(\d+)"',
        r_edit.text
    )
    print(f'  Product {pid}: size={len(r_edit.text):,}  categories={cats}')

# ── Try the category update via the specific PS9 endpoint ──────────────────────
# PS9 might have a dedicated endpoint for adding category to a product
print('\n=== Trying PS9 category update endpoints ===')
# Fetch product 386 edit page to get its current token
r_386 = s.get(f'{ADMIN}/index.php/sell/catalog/products/386/edit',
              params={'_token': cat_token}, allow_redirects=True)
tok_386 = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r_386.url).group(1)

# Look for any 'categor' related API routes in the page
cat_api_urls = re.findall(r'(?:/admin[^\s"\'<>]{0,150}categor[^\s"\'<>]{0,100})', r_386.text, re.I)
for u in sorted(set(cat_api_urls))[:15]:
    print(f'  {u[:180]}')

# Also look for the categories-list endpoint that the Vue component uses
cat_list_url = re.search(r'categories/list[^"\']{0,150}', r_386.text, re.I)
if cat_list_url:
    print(f'\nCategories list URL: {cat_list_url.group()[:200]}')
