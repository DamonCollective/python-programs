"""Probe the PS9 admin to find where carriers are listed and what ICC Courier looks like."""
import requests, re, sys
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
sys.stdout.reconfigure(encoding='utf-8')

ADMIN  = 'https://alegro.gr/admin875fdclzkf27m3shsg9'
EMAIL  = 'damoncollective@gmail.com'
PASSWD = 'cultivatesandspreadslove13579' + chr(33)

s = requests.Session()
s.headers['User-Agent'] = 'Mozilla/5.0'
s.verify = False

# --- LOGIN ---
r = s.get(ADMIN + '/login')
ft = re.search(r'name="_token"\s+value="([^"]+)"', r.text).group(1)
r = s.post(ADMIN + '/login',
           data={'email': EMAIL, 'passwd': PASSWD,
                 'stay_logged_in': '0', '_token': ft, 'submitLogin': '1'},
           allow_redirects=True)
m = re.search(r'[?&]token=([A-Za-z0-9._\-]+)', r.url)
legacy_tok = m.group(1) if m else ''
r2 = s.get(ADMIN + '/index.php',
           params={'controller': 'AdminCarriers', 'token': legacy_tok},
           allow_redirects=True)
tok_m = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r2.url)
if not tok_m:
    tok_m = re.search(r'_token["\s=:]+([A-Za-z0-9._\-]{20,})', r2.text)
cat_token = tok_m.group(1) if tok_m else ''
print(f'Logged in. URL: {r2.url[-80:]}')
print(f'Token: {cat_token[:30]}')

# Try several carrier URL patterns
urls_to_try = [
    ('/index.php/configure/shipping/carriers/', 'Carriers v1'),
    ('/index.php/shipping/carriers/', 'Carriers v2'),
    ('/index.php?controller=AdminCarriers', 'Carriers legacy'),
]
for path, label in urls_to_try:
    url = ADMIN + path
    r_c = s.get(url, params={'_token': cat_token}, allow_redirects=True, timeout=15)
    html = r_c.text
    print(f'\n{label}: {r_c.status_code} ({len(html):,} bytes) -> {r_c.url[-60:]}')

    # Look for carrier IDs in various patterns
    ids1 = re.findall(r'/shipping/carriers/(\d+)', html)
    ids2 = re.findall(r'carrier[_\-]id["\s=:]+(\d+)', html, re.I)
    ids3 = re.findall(r'"id_carrier"\s*:\s*(\d+)', html)
    ids4 = re.findall(r'carriers/(\d+)', html)
    print(f'  ID patterns found: ids1={list(set(ids1))[:10]} ids2={list(set(ids2))[:10]} ids3={list(set(ids3))[:10]} ids4={list(set(ids4))[:10]}')

    # Look for "icc" or "courier" text
    icc_ctx = []
    for m2 in re.finditer(r'.{0,60}(?:icc|courier).{0,60}', html, re.I):
        icc_ctx.append(m2.group(0).strip())
    if icc_ctx:
        print(f'  ICC/courier mentions: {icc_ctx[:5]}')

    # Show all links that look like carrier edit links
    edit_links = re.findall(r'href="([^"]*carrier[^"]*)"', html, re.I)
    if edit_links:
        print(f'  Carrier links: {edit_links[:10]}')

    # Dump first 2000 chars if small page
    if len(html) < 5000:
        print(f'  FULL HTML: {html[:2000]}')
