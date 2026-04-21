"""
Assign products to Theatrical category by editing the CATEGORY (not the product).
Also try the legacy AdminProducts controller to see if it still accepts form POSTs.
"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8')

ADMIN = 'https://alegro.gr/admin875fdclzkf27m3shsg9'
THEATRICAL_ID = 12
PRODUCTS = [265, 266, 267, 268, 269, 270, 386]

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
print(f'Logged in OK, cat_token={cat_token[:40]}')

# 1. Try category edit page to see if we can add products from there
print('\n--- Category 12 (Theatrical) edit page ---')
r_cat = s.get(f'{ADMIN}/index.php/sell/catalog/categories/{THEATRICAL_ID}/edit',
              params={'_token': cat_token}, allow_redirects=True)
print(f'Status: {r_cat.status_code}, size: {len(r_cat.text):,}')
print(f'URL: {r_cat.url[:100]}')

# Look for product-related inputs in category edit page
cat_inputs = re.findall(r'<input[^>]*name="[^"]*product[^"]*"[^>]*>', r_cat.text, re.I)
print(f'Product inputs in cat edit: {cat_inputs[:3]}')

# 2. Look at what routes are available for products
print('\n--- PS9 category routes ---')
# Try listing products from category perspective
r_cat_prods = s.get(f'{ADMIN}/index.php/sell/catalog/categories/{THEATRICAL_ID}',
                    params={'_token': cat_token}, allow_redirects=True)
print(f'Cat {THEATRICAL_ID}: {r_cat_prods.status_code} → {r_cat_prods.url[:80]}')

# 3. Look for the actual feature_id select options to find a valid value
print('\n--- Feature select options (product 265) ---')
r_edit = s.get(f'{ADMIN}/index.php/sell/catalog/products/265/edit',
               params={'_token': cat_token}, allow_redirects=True)
edit_tok = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r_edit.url).group(1)
html = r_edit.text

# Find the feature selector
feature_select_m = re.search(
    r'<select[^>]*name="product\[details\]\[features\]\[feature_id\]"[^>]*>(.*?)</select>',
    html, re.I | re.S
)
if feature_select_m:
    opts = re.findall(r'<option[^>]*value="([^"]*)"[^>]*>([^<]*)</option>', feature_select_m.group(1), re.I)
    print(f'Feature options: {opts[:10]}')
else:
    print('Feature select not found')

# 4. Look at the PS9 AdminCategories endpoint (the legacy one)
print('\n--- Legacy AdminCategories endpoint ---')
r_admin_cats = s.get(ADMIN + '/index.php', params={
    'controller': 'AdminCategories',
    'token': legacy_tok,
}, allow_redirects=True)
print(f'Status: {r_admin_cats.status_code}, URL: {r_admin_cats.url[:100]}, size: {len(r_admin_cats.text):,}')

# 5. Try the PS9 product quick-save or partial-save if it exists
print('\n--- Looking for quick save / partial save endpoints ---')
# Try fetching product via PS9 internal API with JSON
json_endpoints = [
    f'/index.php/sell/catalog/products/{265}/edit?partial=categories&_token={cat_token}',
    f'/index.php/sell/catalog/products/{265}/categories?_token={cat_token}',
]
for ep in json_endpoints:
    r_ep = s.get(ADMIN + ep, headers={'Accept': 'application/json, */*'}, allow_redirects=True)
    print(f'  {ep[:70]}: {r_ep.status_code} ct={r_ep.headers.get("Content-Type","")[:30]}')
    if r_ep.status_code == 200 and len(r_ep.text) < 2000:
        print(f'  Body: {r_ep.text[:200]}')

# 6. Check for a special PS9 "switch" endpoint (like enable/disable)
print('\n--- Looking for product category switch/toggle endpoints ---')
# In PS9, products list has toggle for active. Maybe similar for categories?
r_prods = s.get(f'{ADMIN}/index.php/sell/catalog/products',
                params={'_token': cat_token}, allow_redirects=True)
# Extract AJAX endpoints from the products list page
ajax_urls = re.findall(r'(?:url|route|endpoint)[^"\']{0,10}["\']([^"\']*product[^"\']*)["\']', r_prods.text, re.I)
for u in list(set(ajax_urls))[:10]:
    print(f'  {u[:150]}')

# 7. Try direct PATCH/PUT to product
print('\n--- Testing PATCH/PUT to product endpoint ---')
# PS9 might support REST verbs
patch_payload = {
    'product[description][categories][product_categories][0][id]': '2',
    'product[description][categories][product_categories][0][name]': 'Home',
    'product[description][categories][product_categories][0][display_name]': 'Home',
    'product[description][categories][product_categories][1][id]': '11',
    'product[description][categories][product_categories][1][name]': "Men's",
    'product[description][categories][product_categories][1][display_name]': "Men's",
    'product[description][categories][product_categories][2][id]': '20',
    'product[description][categories][product_categories][2][name]': 'Christmas',
    'product[description][categories][product_categories][2][display_name]': 'Christmas',
    'product[description][categories][product_categories][3][id]': '12',
    'product[description][categories][product_categories][3][name]': 'Theatrical',
    'product[description][categories][product_categories][3][display_name]': 'Theatrical',
    '_token': edit_tok,
    'product[_token]': re.search(r'name="product\[_token\]"[^>]*value="([^"]+)"', html).group(1),
    '_method': 'PATCH',
}
r_patch = s.post(f'{ADMIN}/index.php/sell/catalog/products/265/edit',
                 params={'_token': edit_tok},
                 data=patch_payload,
                 headers={'X-HTTP-Method-Override': 'PATCH', 'Referer': r_edit.url},
                 allow_redirects=False)
print(f'PATCH override: {r_patch.status_code} Location={r_patch.headers.get("Location", "none")[:60]}')
fv = re.search(r'data-form-valid="(\d+)"', r_patch.text)
print(f'form-valid: {fv.group(1) if fv else "?"}')
