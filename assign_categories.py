"""
Find 'theatrikes' category and assign all hero wigs & moustaches to it.
Also prints product names for all identified products.
"""
import requests, re, sys, json
sys.stdout.reconfigure(encoding='utf-8')

ADMIN = 'https://alegro.gr/admin875fdclzkf27m3shsg9'

s = requests.Session()
s.headers['User-Agent'] = 'Mozilla/5.0'

# ── Login ──────────────────────────────────────────────────────────────────────
r = s.get(ADMIN + '/login')
ft = re.search(r'name="_token"\s+value="([^"]+)"', r.text).group(1)
passwd = 'cultivatesandspreadslove13579' + chr(33)
r = s.post(ADMIN + '/login', data={'email':'damoncollective@gmail.com','passwd':passwd,'stay_logged_in':'0','_token':ft,'submitLogin':'1'}, allow_redirects=True)
m = re.search(r'[?&]token=([A-Za-z0-9._\-]+)', r.url)
legacy_tok = m.group(1) if m else ''

r2 = s.get(ADMIN + '/index.php', params={'controller':'AdminProducts','token':legacy_tok}, allow_redirects=True)
cat_token = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r2.url).group(1)

# ── Get full category tree ─────────────────────────────────────────────────────
print('=== Full category tree ===')
r_tree = s.get(f'{ADMIN}/index.php/sell/catalog/categories/tree', params={'_token': cat_token})
tree = r_tree.json()

def flatten_tree(nodes, depth=0):
    result = []
    for node in nodes:
        result.append({'id': node['id'], 'name': node['name'], 'depth': depth})
        if node.get('children'):
            result.extend(flatten_tree(node['children'], depth+1))
    return result

flat = flatten_tree(tree if isinstance(tree, list) else [tree])
for cat in flat:
    indent = '  ' * cat['depth']
    print(f"  {indent}[{cat['id']}] {cat['name']}")

# ── Find theatrikes category ───────────────────────────────────────────────────
theatrikes_id = None
for cat in flat:
    name = cat['name'].lower()
    if 'theatrik' in name or '\u03b8\u03b5\u03b1\u03c4\u03c1' in name:
        print(f"\n>>> Found: [{cat['id']}] {cat['name']}")
        theatrikes_id = cat['id']
        break

if theatrikes_id is None:
    print('\n[!] Category "θεατρικες" NOT found in tree.')
    print('    Available categories:')
    for cat in flat:
        print(f"      [{cat['id']}] {cat['name']}")
    print('\nPlease enter the category ID manually (or 0 to create it):')
    theatrikes_id = int(input('Category ID: ').strip())

print(f'\nUsing category ID: {theatrikes_id}')

# ── Get product names and current categories for all hero products ────────────
# Known hero products from search results
HERO_PRODUCTS = [265, 266, 267, 268, 269, 270, 325, 326, 327, 334, 335, 349, 351, 386]

print('\n=== Getting product names ===')
product_info = {}
for pid in HERO_PRODUCTS:
    r_p = s.get(f'{ADMIN}/index.php/sell/catalog/products/{pid}/edit',
                params={'_token': cat_token}, allow_redirects=True)
    edit_tok_m = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r_p.url)
    edit_tok = edit_tok_m.group(1) if edit_tok_m else cat_token

    # Try to get the product name from various locations
    name_en = None
    # Try input value
    n = re.search(r'name="product\[header\]\[name\]\[1\]"[^>]*value="([^"]+)"', r_p.text)
    if n: name_en = n.group(1)
    # Try data attribute
    if not name_en:
        n = re.search(r'"name"\s*:\s*\{"1"\s*:\s*"([^"]{3,120})"', r_p.text)
        if n: name_en = n.group(1)
    # Try JSON data blob
    if not name_en:
        n = re.search(r'"1"\s*:\s*"([^"]{5,120})"', r_p.text)
        if n: name_en = n.group(1)

    product_info[pid] = {
        'name': name_en or f'Product {pid}',
        'edit_tok': edit_tok,
        'page_size': len(r_p.text),
    }
    print(f"  [{pid}] {product_info[pid]['name'][:80]}  (page={product_info[pid]['page_size']:,})")

# ── Assign theatrikes category to all hero products ────────────────────────────
print(f'\n=== Assigning category {theatrikes_id} to all hero products ===')

for pid in HERO_PRODUCTS:
    info = product_info[pid]
    r_edit = s.get(f'{ADMIN}/index.php/sell/catalog/products/{pid}/edit',
                   params={'_token': cat_token}, allow_redirects=True)
    edit_tok = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r_edit.url).group(1)

    # Extract form CSRF token for the product form
    ft_m = re.search(r'name="product\[_token\]"\s+value="([^"]+)"', r_edit.text)
    if not ft_m:
        ft_m = re.search(r'data-form-name="product"[^>]*data-token="([^"]+)"', r_edit.text)
    form_tok = ft_m.group(1) if ft_m else edit_tok

    # Get current categories checked in the form
    existing_cats = re.findall(r'name="product\[categories\]\[product_categories\]\[(\d+)\]"', r_edit.text)

    # Build payload: keep existing categories + add theatrikes
    all_cats = set([str(c) for c in existing_cats] + [str(theatrikes_id)])
    payload = {
        'product[_token]': form_tok,
        '_token': edit_tok,
    }
    for cat_id in all_cats:
        payload[f'product[categories][product_categories][{cat_id}]'] = '1'
    # Set theatrikes as default category too if no default set
    payload['product[categories][default_category][value]'] = str(theatrikes_id)

    r_save = s.post(
        f'{ADMIN}/index.php/sell/catalog/products/{pid}/edit',
        params={'_token': edit_tok},
        data=payload,
        headers={'Referer': r_edit.url},
        allow_redirects=True,
    )
    status_ok = r_save.status_code == 200 and 'error' not in r_save.url
    print(f"  [{pid}] {r_save.status_code} → {'OK' if status_ok else 'CHECK'}")

print('\n=== Done ===')
print(f'All {len(HERO_PRODUCTS)} products processed.')
print(f'Category ID used: {theatrikes_id}')
