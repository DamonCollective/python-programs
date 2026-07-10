"""Dump raw HTML around ICC Courier to find carrier ID."""
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

r_list = s.get(ADMIN + '/index.php',
               params={'controller': 'AdminCarriers', 'token': legacy_tok},
               allow_redirects=True)
html = r_list.text

# Find ICC Courier position in raw HTML and dump surrounding 1000 chars
pos = html.lower().find('icc courier')
if pos >= 0:
    snippet = html[max(0, pos-500):pos+500]
    print('=== RAW HTML around ICC Courier ===')
    print(snippet)
else:
    print('ICC Courier not found in HTML')
    # Try to find any carrier-related content
    pos2 = html.find('AdminCarrierWizard')
    if pos2 >= 0:
        print('AdminCarrierWizard found at:', pos2)
        print(html[pos2:pos2+500])
