"""Find category tree and product names via PS9 APIs."""
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

r2 = s.get(ADMIN + '/index.php', params={'controller':'AdminProducts','token':legacy_tok}, allow_redirects=True)
cat_token = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r2.url).group(1)

# ── Try PS9 category tree endpoint ────────────────────────────────────────────
print('=== Category tree endpoints ===')
endpoints = [
    f'/index.php/sell/catalog/categories/tree?_token={cat_token}',
    f'/index.php/sell/catalog/categories/search?_token={cat_token}&query=theatrik',
    f'/index.php/sell/catalog/categories/search?_token={cat_token}&query=%CE%B8%CE%B5%CE%B1%CF%84%CF%81',
]
for ep in endpoints:
    r_ep = s.get(ADMIN + ep, allow_redirects=True)
    print(f'  {ep[:60]}: {r_ep.status_code} size={len(r_ep.text)}')
    if r_ep.status_code == 200 and len(r_ep.text) < 5000:
        print(f'    Response: {r_ep.text[:500]}')

# ── Get the product edit page for 268 and extract the full category tree JSON ─
print('\n=== Category tree from product 268 edit page ===')
r_edit = s.get(f'{ADMIN}/index.php/sell/catalog/products/268/edit',
               params={'_token': cat_token}, allow_redirects=True)
edit_tok = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r_edit.url).group(1)

# Find categoryTree or similar JS variable
tree_vars = re.findall(r'(?:categoryTree|categories|categoriesUrl|categoryUrl)[^=]{0,5}=\s*["\']([^"\']+)["\']', r_edit.text, re.I)
print(f'Category tree vars: {tree_vars[:5]}')

# Find any URL with 'categor' in it
cat_urls = re.findall(r'(?:https?://[^\s"\'<>]{0,100}|/admin[^\s"\'<>]{0,100})categor[^\s"\'<>]{0,100}', r_edit.text, re.I)
for u in list(set(cat_urls))[:10]:
    print(f'  Cat URL: {u[:150]}')

# Find any data attribute with category
cat_data = re.findall(r'data-categories[^"]{0,10}="([^"]+)"', r_edit.text, re.I)
print(f'data-categories: {cat_data[:3]}')

# ── Fetch the full category admin page and look for theatrik in raw HTML ───────
print('\n=== AdminCategories full search ===')
r_all_cats = s.get(ADMIN + '/index.php', params={
    'controller': 'AdminCategories',
    'token': legacy_tok,
    'submitFiltercategory': '1',
    'categoryFilter_name': '\u03b8\u03b5\u03b1\u03c4\u03c1',  # θεατρ
}, allow_redirects=True)
print(f'Filter response size: {len(r_all_cats.text)}')
hits = re.findall(r'.{0,100}(?:\u03b8\u03b5\u03b1\u03c4\u03c1|\u03b8\u03b5\u03b1\u03c4).{0,100}', r_all_cats.text)
for h in hits[:10]:
    print(h[:250])

# ── Check if 'theatrikes' category exists at all ─────────────────────────────
print('\n=== All category names (first 50) ===')
# Extract from category admin page - look for table rows
all_cat_names = re.findall(r'<td[^>]*>\s*([^\n<]{3,50})\s*</td>', r_all_cats.text)
for name in all_cat_names[:50]:
    name = name.strip()
    if name and not name.startswith('<') and len(name) > 2:
        print(f'  {name}')
