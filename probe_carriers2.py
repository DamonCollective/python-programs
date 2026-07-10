"""Find ICC Courier's ID and dump the wizard edit form fields."""
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

r = s.get(ADMIN + '/login')
ft = re.search(r'name="_token"\s+value="([^"]+)"', r.text).group(1)
r = s.post(ADMIN + '/login',
           data={'email': EMAIL, 'passwd': PASSWD,
                 'stay_logged_in': '0', '_token': ft, 'submitLogin': '1'},
           allow_redirects=True)
m = re.search(r'[?&]token=([A-Za-z0-9._\-]+)', r.url)
legacy_tok = m.group(1) if m else ''

# Get carrier list via legacy controller
r_list = s.get(ADMIN + '/index.php',
               params={'controller': 'AdminCarriers', 'token': legacy_tok},
               allow_redirects=True)
html = r_list.text

# Find the wizard token from the page links
wiz_tok_m = re.search(r'controller=AdminCarrierWizard&amp;token=([A-Za-z0-9._\-]+)', html)
wiz_tok = wiz_tok_m.group(1) if wiz_tok_m else legacy_tok
print(f'Wizard token: {wiz_tok[:30]}...')

# Find ICC Courier with its edit link / ID
# Pattern: id_carrier appears near the carrier name in edit/delete links
icc_ctx = re.findall(r'.{0,200}ICC Courier.{0,200}', html, re.S | re.I)
for ctx in icc_ctx[:3]:
    print('ICC context:', ctx[:300])
    print('---')

# Extract all id_carrier values near ICC Courier
for ctx in icc_ctx:
    ids = re.findall(r'id_carrier[=\s"]+(\d+)', ctx, re.I)
    if ids:
        print(f'ICC Courier id_carrier candidates: {ids}')

# Also find all edit/delete links with id_carrier
edit_links = re.findall(r'href="[^"]*AdminCarrierWizard[^"]*id_carrier[=\s]*(\d+)[^"]*"', html, re.I)
del_links = re.findall(r'id_carrier[=&]+(\d+)[^"]*delete', html, re.I)
all_carrier_ids = re.findall(r'id_carrier[%3D=]+(\d+)', html, re.I)
print(f'Edit wizard links carrier IDs: {edit_links}')
print(f'Delete links carrier IDs: {del_links}')
print(f'All id_carrier values on page: {list(set(all_carrier_ids))}')
