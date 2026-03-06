"""Clear PS9 Smarty + page cache via admin performance page."""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8')

ADMIN = 'https://alegro.gr/admin875fdclzkf27m3shsg9'

s = requests.Session()
s.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36'

r = s.get(ADMIN + '/login')
ft = re.search(r'name="_token"\s+value="([^"]+)"', r.text).group(1)
passwd = 'cultivatesandspreadslove13579' + chr(33)
r = s.post(ADMIN + '/login', data={'email':'damoncollective@gmail.com','passwd':passwd,
           'stay_logged_in':'0','_token':ft,'submitLogin':'1'}, allow_redirects=True)
m = re.search(r'[?&]token=([A-Za-z0-9._\-]+)', r.url)
legacy_tok = m.group(1) if m else ''
r2 = s.get(ADMIN + '/index.php', params={'controller':'AdminProducts','token':legacy_tok}, allow_redirects=True)
cat_token = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r2.url).group(1)
print('Logged in OK')

# Get performance page
r_perf = s.get(f'{ADMIN}/index.php/configure/advanced/performance/',
               params={'_token': cat_token}, allow_redirects=True)
perf_url = r_perf.url
perf_tok_m = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', perf_url)
perf_tok = perf_tok_m.group(1) if perf_tok_m else cat_token
html = r_perf.text
print(f'Performance page: {len(html):,} bytes')

# Find Smarty form
smarty_form_m = re.search(r'<form[^>]+action="([^"]*smarty[^"]*)"[^>]*>(.*?)</form>', html, re.I | re.S)
if smarty_form_m:
    smarty_url = smarty_form_m.group(1)
    if smarty_url.startswith('/'):
        smarty_url = 'https://alegro.gr' + smarty_url
    smarty_body = smarty_form_m.group(2)
    print(f'Smarty form URL: {smarty_url[-60:]}')

    # Collect form inputs
    payload = {}
    for m2 in re.finditer(r'<input[^>]+>', smarty_body, re.I):
        tag = m2.group(0)
        nm = re.search(r'\bname="([^"]+)"', tag, re.I)
        vm = re.search(r'\bvalue="([^"]*)"', tag, re.I)
        tp = re.search(r'\btype="([^"]*)"', tag, re.I)
        if not nm: continue
        t = tp.group(1).lower() if tp else 'text'
        if t != 'submit':
            payload[nm.group(1)] = vm.group(1) if vm else ''

    # Find clear cache submit button name
    submit_m = re.search(r'<button[^>]*name="([^"]+)"[^>]*type="submit"[^>]*>|<input[^>]*type="submit"[^>]*name="([^"]+)"', smarty_body, re.I)
    if submit_m:
        submit_name = submit_m.group(1) or submit_m.group(2)
        payload[submit_name] = '1'
        print(f'Submit field: {submit_name}')
    else:
        # Try common submit names
        payload['submitPerformance'] = '1'

    # Add Smarty cache clear flag
    payload['smarty[cache]'] = '0'  # force clear
    payload['smarty[force_cache]'] = '0'

    print(f'Submitting {len(payload)} fields to clear Smarty cache...')
    r_save = s.post(smarty_url, data=payload, headers={'Referer': perf_url}, allow_redirects=True)
    print(f'Save: {r_save.status_code}')
    success = re.search(r'alert-success', r_save.text, re.I)
    print(f'Success: {bool(success)}')
else:
    print('Smarty form not found — trying direct clear cache route')

# Try the direct clear-cache route in PS9
clear_routes = [
    f'{ADMIN}/index.php/configure/advanced/performance/clear-cache?_token={perf_tok}',
]
for url in clear_routes:
    r_c = s.post(url, headers={'Referer': perf_url}, allow_redirects=True)
    print(f'Clear cache: {r_c.status_code} → {r_c.url[-50:]}')
    if re.search(r'alert-success', r_c.text, re.I):
        print('Cache cleared successfully!')
        break

# Also try the legacy clear_compile
r_cc = s.get(ADMIN + '/index.php',
             params={'controller': 'AdminPerformance', 'token': legacy_tok,
                     'smarty_clear_cache': '1'},
             allow_redirects=True)
print(f'Legacy clear compile: {r_cc.status_code}')

# Also rebuild search index via the legacy method
print('\n--- Rebuilding search index ---')
r_idx = s.get(ADMIN + '/index.php',
              params={'controller': 'AdminProducts', 'token': legacy_tok,
                      'action': 'searchIndexUpdate'},
              allow_redirects=True)
print(f'Index update attempt: {r_idx.status_code} ({len(r_idx.text):,} bytes)')
