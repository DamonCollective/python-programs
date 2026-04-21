"""
Create a PS9 webservice API key and use it to update product 386.
The REST API bypasses the problematic product form entirely.
"""
import requests, re, sys, json, secrets
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

# 1. Find the webservice create page
print('\n--- Webservice create page ---')
ws_create_urls = [
    f'/index.php/configure/advanced/webservice/new',
    f'/index.php/configure/advanced/webservice/create',
]
ws_page = None
ws_url  = None
for url in ws_create_urls:
    r_ws = s.get(ADMIN + url, params={'_token': cat_token}, allow_redirects=True)
    print(f'  {url}: {r_ws.status_code} ({len(r_ws.text):,} bytes)')
    if r_ws.status_code == 200 and len(r_ws.text) > 5000:
        ws_page = r_ws.text
        ws_url  = r_ws.url
        break

if not ws_page:
    # Try from the webservice list page
    r_ws_list = s.get(ADMIN + '/index.php', params={'controller':'AdminWebservice','token':legacy_tok}, allow_redirects=True)
    print(f'  AdminWebservice list: {r_ws_list.status_code} {r_ws_list.url[:80]}')
    # Find add new key link
    add_link_m = re.search(r'href="([^"]*(?:webservice|ws)[^"]*(?:new|add|create)[^"]*)"', r_ws_list.text, re.I)
    if not add_link_m:
        # Extract token for webservice page
        ws_tok_m = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r_ws_list.url)
        ws_tok = ws_tok_m.group(1) if ws_tok_m else cat_token
        # Try Symfony route
        r_ws2 = s.get(f'{ADMIN}/index.php/configure/advanced/webservice/new', params={'_token': ws_tok}, allow_redirects=True)
        print(f'  New key page: {r_ws2.status_code} ({len(r_ws2.text):,} bytes) {r_ws2.url[:80]}')
        if r_ws2.status_code == 200 and len(r_ws2.text) > 5000:
            ws_page = r_ws2.text
            ws_url = r_ws2.url
    else:
        print(f'  Add link: {add_link_m.group(1)[:100]}')
        r_ws2 = s.get(add_link_m.group(1), allow_redirects=True)
        ws_page = r_ws2.text
        ws_url = r_ws2.url

if not ws_page:
    print('Could not find webservice create page')
    sys.exit(1)

print(f'\nWebservice create page: {len(ws_page):,} bytes, URL: {ws_url[:100]}')

# 2. Parse the create form
ws_tok_m = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', ws_url)
ws_tok = ws_tok_m.group(1) if ws_tok_m else cat_token

# Get form CSRF token
form_csrf = re.search(r'name="api_access\[_token\]"[^>]*value="([^"]+)"', ws_page)
if not form_csrf:
    form_csrf = re.search(r'name="webservice_account\[_token\]"[^>]*value="([^"]+)"', ws_page)
if not form_csrf:
    # Find any form _token
    form_csrf = re.search(r'name="[^"]*\[_token\]"[^>]*value="([^"]+)"', ws_page)

print(f'Form CSRF: {form_csrf.group(1)[:40] if form_csrf else "not found"}')
print(f'Page token: {ws_tok[:40]}')

# Show all form inputs
all_ws_inputs = {}
for m in re.finditer(r'<input[^>]+>', ws_page, re.I):
    tag = m.group(0)
    nm = re.search(r'\bname="([^"]+)"', tag, re.I)
    vm = re.search(r'\bvalue="([^"]*)"', tag, re.I)
    if nm:
        all_ws_inputs[nm.group(1)] = vm.group(1) if vm else ''
        print(f'  {nm.group(1)} = {repr(vm.group(1) if vm else "")[:60]}')

# Show select elements
selects = re.findall(r'<select[^>]*name="([^"]+)"[^>]*>', ws_page, re.I)
print(f'Select fields: {selects[:10]}')

# Show checkboxes
checkboxes = re.findall(r'<input[^>]*type="checkbox"[^>]*name="([^"]+)"[^>]*value="([^"]*)"', ws_page, re.I)
print(f'Checkboxes (first 10): {checkboxes[:10]}')
