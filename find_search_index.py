import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8')

ADMIN = 'https://alegro.gr/admin875fdclzkf27m3shsg9'

s = requests.Session()
s.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36'

r = s.get(ADMIN + '/login')
ft = re.search(r'name="_token"\s+value="([^"]+)"', r.text).group(1)
passwd = 'cultivatesandspreadslove13579' + chr(33)
r = s.post(ADMIN + '/login', data={'email':'damoncollective@gmail.com','passwd':passwd,'stay_logged_in':'0','_token':ft,'submitLogin':'1'}, allow_redirects=True)
m = re.search(r'[?&]token=([A-Za-z0-9._\-]+)', r.url)
legacy_tok = m.group(1) if m else ''
r2 = s.get(ADMIN + '/index.php', params={'controller':'AdminProducts','token':legacy_tok}, allow_redirects=True)
cat_token = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r2.url).group(1)

r_s = s.get(f'{ADMIN}/index.php/configure/shop/search/', params={'_token': cat_token}, allow_redirects=True)
real_tok_m = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r_s.url)
real_tok = real_tok_m.group(1) if real_tok_m else cat_token
print(f'Search page: {len(r_s.text):,} bytes, tok={real_tok[:20]}')
html = r_s.text

# Find all forms
print('\n=== Forms ===')
for m in re.finditer(r'<form[^>]+>', html, re.I):
    tag = m.group()
    nm = re.search(r'name="([^"]+)"', tag, re.I)
    ac = re.search(r'action="([^"]+)"', tag, re.I)
    print(f'  [{nm.group(1) if nm else "?"}] → {ac.group(1)[-60:] if ac else "?"}')

# Find buttons
print('\n=== Buttons ===')
for m in re.finditer(r'<button[^>]*>(.*?)</button>', html, re.I | re.S):
    text = re.sub(r'<[^>]+>', '', m.group(1)).strip()
    if text and len(text) < 100:
        print(f'  {repr(text[:80])}')

# Find index/rebuild links
print('\n=== Index/rebuild links ===')
for m in re.finditer(r'href="([^"]*(?:index|rebuild)[^"]*)"', html, re.I):
    print(f'  {m.group(1)[:120]}')

# Look for the 'indexing' form specifically
idx_area = re.search(r'.{0,200}(?:submitAddindex|Add.*index|Rebuild|Re-build|reindex).{0,300}', html, re.I | re.S)
if idx_area:
    print('\nIndexing area:', repr(idx_area.group()[:400]))
