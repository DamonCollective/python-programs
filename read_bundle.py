"""Read the product JS bundle to find the save endpoint and form submission logic."""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8')

ADMIN = 'https://alegro.gr/admin875fdclzkf27m3shsg9'
PID = 265

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

# Fetch the create_product bundle
bundle_url = f'https://alegro.gr/admin875fdclzkf27m3shsg9/themes/new-theme/public/create_product.bundle.js?9.0.0'
r_bundle = s.get(bundle_url)
bundle = r_bundle.text
print(f'create_product bundle: {len(bundle):,} chars')

# Search for save-related terms
print('\n--- "save" occurrences (context) ---')
for m in re.finditer(r'.{0,50}save.{0,50}', bundle, re.I):
    snippet = m.group().strip()
    if any(kw in snippet.lower() for kw in ['url', 'post', 'fetch', 'axios', 'xhr', 'submit', 'action']):
        print(f'  {snippet[:150]}')

print('\n--- POST/fetch patterns ---')
post_pats = re.findall(r'(?:fetch|axios\.post|XMLHttpRequest|\.post\()[^\n]{0,200}', bundle, re.I)
for p in post_pats[:15]:
    print(f'  {p[:200]}')

print('\n--- Category-related patterns ---')
cat_pats = re.findall(r'.{0,50}categor.{0,100}', bundle, re.I)
seen = set()
for p in cat_pats[:20]:
    key = p[:60]
    if key not in seen:
        seen.add(key)
        print(f'  {p[:200]}')

print('\n--- URL patterns in bundle ---')
urls = re.findall(r'["\'/](?:sell|catalog|products|api)[/\w\-{}]+["\']', bundle, re.I)
seen_urls = set()
for u in urls:
    if u not in seen_urls:
        seen_urls.add(u)
        print(f'  {u[:150]}')

# Also check product_edit bundle
bundle2_url = f'https://alegro.gr/admin875fdclzkf27m3shsg9/themes/new-theme/public/product_edit.bundle.js?9.0.0'
r_bundle2 = s.get(bundle2_url)
bundle2 = r_bundle2.text
print(f'\nproduct_edit bundle: {len(bundle2):,} chars')

print('\n--- POST/fetch in product_edit ---')
post_pats2 = re.findall(r'(?:fetch|axios\.post|\.post\()[^\n]{0,200}', bundle2, re.I)
for p in post_pats2[:10]:
    print(f'  {p[:200]}')

print('\n--- Save endpoint in product_edit ---')
save_pats = re.findall(r'.{0,80}(?:save|submit|update|put)[^\n]{0,120}', bundle2, re.I)
seen2 = set()
for p in save_pats[:15]:
    key = p.strip()[:60]
    if key not in seen2 and any(kw in p.lower() for kw in ['url', 'route', 'path', 'fetch', 'post']):
        seen2.add(key)
        print(f'  {p.strip()[:200]}')
