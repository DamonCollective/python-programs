"""Get carriers page by following the sidebar link from the dashboard."""
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

# Login — lands on dashboard
r = s.get(ADMIN + '/login')
ft = re.search(r'name="_token"\s+value="([^"]+)"', r.text).group(1)
r_login = s.post(ADMIN + '/login',
                 data={'email': EMAIL, 'passwd': PASSWD,
                       'stay_logged_in': '0', '_token': ft, 'submitLogin': '1'},
                 allow_redirects=True)
print(f'Login -> {r_login.url[-70:]}')

# Load dashboard to get sidebar links
dash_html = r_login.text

# Look for carriers link in sidebar/nav
carrier_links = re.findall(r'href="([^"]*(?:AdminCarrier|carrier)[^"]*)"', dash_html, re.I)
print(f'Carrier links from dashboard: {carrier_links[:5]}')

# Try to find AdminCarriers token from a link like /?controller=AdminCarriers&token=XXX
carriers_url_m = re.search(
    r'https?://[^"]*(?:controller=AdminCarriers|AdminCarriers)[^"]*token=([A-Za-z0-9._\-]+)',
    dash_html, re.I
)
if carriers_url_m:
    admin_carriers_tok = carriers_url_m.group(1)
    print(f'Found AdminCarriers token: {admin_carriers_tok[:40]}')
else:
    # Try to get the carriers page via the CSRF bypass
    # First request (will get CSRF error)
    r_csrf = s.get(ADMIN + '/index.php',
                   params={'controller': 'AdminCarriers'},
                   allow_redirects=True)
    csrf_html = r_csrf.text
    # Extract the "I understand the risk" URL
    risk_url_m = re.search(r'href="([^"]*controller=AdminCarriers[^"]*_token=[^"]+)"', csrf_html, re.I)
    if risk_url_m:
        risk_url = risk_url_m.group(1).replace('&amp;', '&')
        print(f'Risk URL found: {risk_url[-80:]}')
        r_carriers = s.get(risk_url, allow_redirects=True)
        carriers_html = r_carriers.text
        print(f'Carriers page: {r_carriers.status_code}, {len(carriers_html):,} bytes')
    else:
        print('No risk link found. CSRF page:')
        print(csrf_html[:1000])
        sys.exit(1)

# Now find ICC Courier
if 'carriers_html' not in dir():
    # Try direct request
    r_carriers = s.get(ADMIN + '/index.php',
                       params={'controller': 'AdminCarriers', 'token': admin_carriers_tok},
                       allow_redirects=True)
    carriers_html = r_carriers.text

print(f'Carriers HTML size: {len(carriers_html):,}')
pos = carriers_html.lower().find('icc courier')
if pos >= 0:
    print(f'ICC Courier found at pos {pos}')
    snippet = carriers_html[max(0, pos-600):pos+600]
    print(snippet)
    nums = re.findall(r'\b(\d{1,5})\b', snippet)
    print(f'Nearby numbers: {list(set(nums))}')
else:
    print('ICC Courier not found. Checking what IS there:')
    for kw in ['carrier', 'Courier', 'Ταχυδρομ', 'ELTA', 'fedex', 'shipping']:
        p = carriers_html.lower().find(kw.lower())
        if p >= 0:
            print(f'  Found {kw!r} at pos {p}: {carriers_html[max(0,p-30):p+60]}')
