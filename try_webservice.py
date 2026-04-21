"""
Try PS9 webservice API to update product categories.
First check if webservice is enabled and find the key.
"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8')

ADMIN = 'https://alegro.gr/admin875fdclzkf27m3shsg9'
BASE  = 'https://alegro.gr'

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
print('Logged in OK')

# Check webservice page
print('\n--- Checking webservice admin page ---')
r_ws = s.get(ADMIN + '/index.php', params={
    'controller': 'AdminWebservice',
    'token': legacy_tok,
}, allow_redirects=True)
print(f'Webservice page: {r_ws.status_code}, size={len(r_ws.text):,}')

# Look for existing API keys
api_keys = re.findall(r'(?:key|api.?key)[^"\']{0,5}["\']([A-Z0-9]{20,40})["\']', r_ws.text, re.I)
print(f'API keys found: {api_keys[:5]}')

# Also look in table rows
keys_in_table = re.findall(r'<td[^>]*>([A-Z0-9]{20,40})</td>', r_ws.text)
print(f'Keys in table: {keys_in_table[:5]}')

# Check webservice availability
print('\n--- Testing webservice endpoints ---')
endpoints = [
    '/api/',
    '/api/products/265?output_format=JSON',
    '/api/categories?output_format=JSON',
]
for ep in endpoints:
    r_ep = requests.get(BASE + ep, allow_redirects=True)
    print(f'  {ep}: {r_ep.status_code} size={len(r_ep.text)} body[:150]={r_ep.text[:150]}')

# Look for webservice key in the page
ws_key_m = re.search(r'(?:ws_key|webservice[_\s]key)[^"\'=]{0,10}["\']?([A-Z0-9]{20,40})', r_ws.text, re.I)
if ws_key_m:
    print(f'\nWebservice key: {ws_key_m.group(1)}')

# Try to find webservice in PS config
print('\n--- Checking PS9 configuration ---')
r_config = s.get(ADMIN + '/index.php', params={
    'controller': 'AdminWebservice',
    'token': legacy_tok,
    'action': 'list',
}, allow_redirects=True)
config_keys = re.findall(r'<input[^>]*name="[^"]*key[^"]*"[^>]*value="([A-Z0-9]{20,40})"', r_config.text, re.I)
print(f'Config page keys: {config_keys[:5]}')

# Try webservice with session cookies (authenticated session)
print('\n--- Testing API with session auth ---')
for ep in ['/api/', '/api/products/265']:
    r_ep = s.get(BASE + ep,
                 params={'output_format': 'JSON'},
                 headers={'Accept': 'application/json'},
                 allow_redirects=True)
    print(f'  {ep}: {r_ep.status_code} body[:200]={r_ep.text[:200]}')
