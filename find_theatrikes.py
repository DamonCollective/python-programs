"""Find θεατρικες category ID and get product names for all hero items."""
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

# Get catalog token via catalog page
r2 = s.get(ADMIN + '/index.php', params={'controller':'AdminProducts','token':legacy_tok}, allow_redirects=True)
cat_token = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r2.url).group(1)

# ── Fetch the category list (AdminCategories) ─────────────────────────────────
print('=== Searching for θεατρικες category ===')
r_cats = s.get(ADMIN + '/index.php', params={'controller':'AdminCategories','token':legacy_tok}, allow_redirects=True)

# Try to find category IDs for any theatre/theatrical category
# Search in the HTML for category names
cat_rows = re.findall(
    r'(?:id_category|cat_id)["\s=:]+(\d+)[^<]{0,500}|'
    r'<tr[^>]*id="tr_(\d+)"[^>]*>[^<]{0,1000}',
    r_cats.text, re.S
)

# Better: search for the word theatrik in context with numbers
theater_ctx = re.findall(r'.{0,300}(?:theatrik|θεατρ|ΘΕΑΤΡ|Theatrik).{0,300}', r_cats.text, re.I)
for ctx in theater_ctx[:5]:
    # Extract nearby numbers that could be IDs
    nums = re.findall(r'\b(\d{1,4})\b', ctx)
    print(f'Context: {ctx[:200]}')
    print(f'  Nearby numbers: {nums}')
    print()

# ── Use the category tree API endpoint ────────────────────────────────────────
print('\n=== Category tree API ===')
r_tree = s.get(ADMIN + '/index.php/sell/catalog/categories', params={'_token': cat_token}, allow_redirects=True)
tree_token = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r_tree.url).group(1)

# Look for theatrik in category tree page
tree_hits = re.findall(r'.{0,150}(?:theatrik|θεατρ|Theatrik).{0,150}', r_tree.text, re.I)
for h in tree_hits[:5]:
    print(h[:300])

# ── Load product 268 edit page and look at its category tree ─────────────────
print('\n=== Category tree from product 268 edit page ===')
r_edit = s.get(f'{ADMIN}/index.php/sell/catalog/products/268/edit',
               params={'_token': cat_token}, allow_redirects=True)
edit_tok = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r_edit.url).group(1)

# Find θεατρ in the product edit page category section
theatr_hits = re.findall(r'.{0,200}(?:theatrik|θεατρ|Theatrik).{0,200}', r_edit.text, re.I)
for h in theatr_hits[:10]:
    print(h[:300])
    print('---')

# ── Also get product names for all hero products ──────────────────────────────
print('\n=== Product names for hero wigs & moustaches ===')
for pid in [265, 266, 267, 268, 269, 270, 325, 326, 327, 334, 335, 349, 351, 386]:
    r_p = s.get(f'{ADMIN}/index.php/sell/catalog/products/{pid}/edit',
                params={'_token': cat_token}, allow_redirects=True)
    # Extract product name from page title or input
    name_m = (
        re.search(r'<title>([^<]{3,80})\s*[•·|]\s*Alegro', r_p.text)
        or re.search(r'name="product\[header\]\[name\]\[1\]"\s+value="([^"]+)"', r_p.text)
        or re.search(r'"name"\s*:\s*\{"1"\s*:\s*"([^"]{5,100})"', r_p.text)
    )
    name = name_m.group(1).strip() if name_m else '(no name found)'
    print(f'  Product {pid}: {name[:80]}')
