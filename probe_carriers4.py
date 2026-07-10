"""Find ICC Courier ID using correct token flow."""
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

# Login
r = s.get(ADMIN + '/login')
ft = re.search(r'name="_token"\s+value="([^"]+)"', r.text).group(1)
r = s.post(ADMIN + '/login',
           data={'email': EMAIL, 'passwd': PASSWD,
                 'stay_logged_in': '0', '_token': ft, 'submitLogin': '1'},
           allow_redirects=True)
m = re.search(r'[?&]token=([A-Za-z0-9._\-]+)', r.url)
legacy_tok = m.group(1) if m else ''

# Get carriers page with token= (legacy style) to get _token
r2 = s.get(ADMIN + '/index.php',
           params={'controller': 'AdminCarriers', 'token': legacy_tok},
           allow_redirects=True)

# Extract _token from URL or from page
tok_m = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r2.url)
if not tok_m:
    tok_m = re.search(r'["\']_token["\']\s*:\s*["\']([A-Za-z0-9._\-]+)["\']', r2.text)
    if not tok_m:
        tok_m = re.search(r'_token[="\s]+([A-Za-z0-9._\-]{30,})', r2.text)
cat_token = tok_m.group(1) if tok_m else ''
print(f'_token (cat): {cat_token[:40]}')

# Also extract the AdminCarriers legacy token from the page
carriers_tok_m = re.search(r'controller=AdminCarriers&(?:amp;)?token=([A-Za-z0-9._\-]+)', r2.text)
carriers_tok = carriers_tok_m.group(1) if carriers_tok_m else legacy_tok
print(f'AdminCarriers token: {carriers_tok[:40]}')

# Fetch carriers list with the legacy token for AdminCarriers
r_list = s.get(ADMIN + '/index.php',
               params={'controller': 'AdminCarriers', 'token': carriers_tok},
               allow_redirects=True)
html = r_list.text
print(f'Carriers list: {r_list.status_code}, {len(html):,} bytes')

pos = html.lower().find('icc courier')
if pos >= 0:
    snippet = html[max(0, pos-800):pos+800]
    print('\n=== ICC Courier context (raw) ===')
    print(snippet)
    print('=== END ===')

    # Try to extract all numeric IDs near ICC Courier
    ids = re.findall(r'\b(\d{1,5})\b', snippet)
    print(f'Numeric IDs near ICC Courier: {ids}')
else:
    print('ICC Courier NOT found')
    # Dump first 3000 chars to see what we got
    print('Page start:')
    print(html[:3000])
