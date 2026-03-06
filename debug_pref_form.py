"""Inspect AdminPPreferences form tokens and submit properly."""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8')

ADMIN = 'https://alegro.gr/admin875fdclzkf27m3shsg9'

s = requests.Session()
s.headers['User-Agent'] = 'Mozilla/5.0'

r = s.get(ADMIN + '/login')
ft = re.search(r'name="_token"\s+value="([^"]+)"', r.text).group(1)
passwd = 'cultivatesandspreadslove13579' + chr(33)
r = s.post(ADMIN + '/login', data={'email':'damoncollective@gmail.com','passwd':passwd,
           'stay_logged_in':'0','_token':ft,'submitLogin':'1'}, allow_redirects=True)
m = re.search(r'[?&]token=([A-Za-z0-9._\-]+)', r.url)
legacy_tok = m.group(1) if m else ''
print(f'legacy_tok: {legacy_tok[:30]}')

r_page = s.get(ADMIN + '/index.php',
               params={'controller': 'AdminPPreferences', 'token': legacy_tok},
               allow_redirects=True)
page_url = r_page.url
print(f'Page URL: {page_url[-80:]}')

# Extract token from the redirected URL (PS9 may redirect to Symfony route)
url_tok_m = re.search(r'[?&]token=([A-Za-z0-9._\-]+)', page_url)
url_tok = url_tok_m.group(1) if url_tok_m else legacy_tok
print(f'URL token: {url_tok[:30]}')

html = r_page.text

# Show ALL hidden inputs and token-like inputs
print('\n--- All hidden/token inputs ---')
for m in re.finditer(r'<input[^>]+>', html, re.I):
    tag = m.group(0)
    tp = re.search(r'\btype="([^"]*)"', tag, re.I)
    nm = re.search(r'\bname="([^"]+)"', tag, re.I)
    vm = re.search(r'\bvalue="([^"]*)"', tag, re.I)
    t = tp.group(1).lower() if tp else 'text'
    n = nm.group(1) if nm else ''
    v = vm.group(1) if vm else ''
    if t == 'hidden' or 'token' in n.lower():
        print(f'  [{t}] {n} = {repr(v[:60])}')

# Show form action
print('\n--- Form tags ---')
for m in re.finditer(r'<form[^>]+>', html, re.I):
    print(f'  {m.group()[:200]}')
