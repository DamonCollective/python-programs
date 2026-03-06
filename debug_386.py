"""Debug product 386 - find all select elements and their selected values."""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8')

ADMIN = 'https://alegro.gr/admin875fdclzkf27m3shsg9'
PID = 386

s = requests.Session()
s.headers['User-Agent'] = 'Mozilla/5.0'

r = s.get(ADMIN + '/login')
ft = re.search(r'name="_token"\s+value="([^"]+)"', r.text).group(1)
passwd = 'cultivatesandspreadslove13579' + chr(33)
r = s.post(ADMIN + '/login', data={'email':'damoncollective@gmail.com','passwd':passwd,'stay_logged_in':'0','_token':ft,'submitLogin':'1'}, allow_redirects=True)
m = re.search(r'[?&]token=([A-Za-z0-9._\-]+)', r.url)
legacy_tok = m.group(1) if m else ''
r2 = s.get(ADMIN + '/index.php', params={'controller':'AdminProducts','token':legacy_tok}, allow_redirects=True)
cat_token = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r2.url).group(1)

r_edit = s.get(f'{ADMIN}/index.php/sell/catalog/products/{PID}/edit',
               params={'_token': cat_token}, allow_redirects=True)
edit_tok = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r_edit.url).group(1)
html = r_edit.text

# Find all select elements with their selected options
print('=== SELECT elements ===')
for sel_m in re.finditer(r'<select([^>]*)>(.*?)</select>', html, re.I | re.S):
    attrs = sel_m.group(1)
    body = sel_m.group(2)
    name_m = re.search(r'\bname="([^"]+)"', attrs, re.I)
    if not name_m:
        continue
    name = name_m.group(1)
    # Find selected option
    selected_m = re.search(r'<option[^>]+selected[^>]*value="([^"]*)"', body, re.I)
    if not selected_m:
        # First option is default
        first_m = re.search(r'<option[^>]*value="([^"]*)"', body, re.I)
        val = first_m.group(1) if first_m else '?'
        print(f'  {name} = {repr(val)} (no selected, first option)')
    else:
        print(f'  {name} = {repr(selected_m.group(1))} (selected)')

# Find redirect_type area
print('\n=== redirect context ===')
redir_m = re.search(r'.{0,100}redirect.{0,500}', html, re.I | re.S)
if redir_m:
    print(redir_m.group()[:600])
