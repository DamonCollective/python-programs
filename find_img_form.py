import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8')

ADMIN = 'https://alegro.gr/admin875fdclzkf27m3shsg9'
PRODUCT_ID = 386

s = requests.Session()
s.headers['User-Agent'] = 'Mozilla/5.0'

r = s.get(ADMIN + '/login')
ft = re.search(r'name="_token"\s+value="([^"]+)"', r.text).group(1)
passwd = 'cultivatesandspreadslove13579' + chr(33)
r = s.post(ADMIN + '/login', data={'email':'damoncollective@gmail.com','passwd':passwd,'stay_logged_in':'0','_token':ft,'submitLogin':'1'}, allow_redirects=True)

# Get catalog token
m = re.search(r'[?&]token=([A-Za-z0-9._\-]+)', r.url)
legacy_tok = m.group(1) if m else ''
r2 = s.get(ADMIN + '/index.php', params={'controller':'AdminProducts','token':legacy_tok}, allow_redirects=True)
cat_token_m = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r2.url)
cat_token = cat_token_m.group(1) if cat_token_m else legacy_tok

# Get edit page
r3 = s.get(f'{ADMIN}/index.php/sell/catalog/products/{PRODUCT_ID}/edit',
           params={'_token': cat_token}, allow_redirects=True)
html = r3.text
url_token = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r3.url).group(1)

# Extract the JS legacy token (var token = '...')
js_token_m = re.search(r"var token = '([^']+)'", html)
js_token = js_token_m.group(1) if js_token_m else None
print('URL token (Symfony _token):', url_token[:80])
print('JS legacy token (var token):', (js_token or 'NOT FOUND')[:80])

# Search for product_image in the page
print('\n--- product_image occurrences ---')
pi_hits = [(m.start(), html[max(0,m.start()-50):m.start()+300])
           for m in re.finditer(r'product_image', html, re.I)]
print(f'Found {len(pi_hits)} occurrences')
for pos, ctx in pi_hits[:5]:
    print(f'\n  pos={pos}:')
    print(f'  {ctx[:300]}')

# Try to find image upload form CSRF token
print('\n--- Image form token search ---')
# Pattern: data-form-name="product_image" with data-token (in any order)
img_form = re.search(r'(?:data-form-name="product_image"[^>]*data-token|data-token[^>]*data-form-name="product_image")="([^"]+)"', html)
if img_form:
    print('Image form token (pattern 1):', img_form.group(1)[:80])
else:
    print('Pattern 1: not found')

# Try JSON embedded data
json_hits = re.findall(r'"product_image"[^}]{0,300}"_token"\s*:\s*"([^"]+)"', html)
print('JSON token hits:', [t[:60] for t in json_hits[:3]])

# Search in script tags
scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.S | re.I)
print(f'Script blocks: {len(scripts)}')
for i, sc in enumerate(scripts):
    if 'image' in sc.lower() and ('token' in sc.lower() or 'upload' in sc.lower()):
        print(f'\nScript {i} (image+token):')
        print(sc[:500])
