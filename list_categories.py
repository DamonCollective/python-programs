import requests, re, sys, urllib3
urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

ADMIN = 'https://alegro.gr/admin875fdclzkf27m3shsg9'
s = requests.Session()
s.verify = False
s.headers['User-Agent'] = 'Mozilla/5.0'

r = s.get(ADMIN + '/login')
ft = re.search(r'name="_token"\s+value="([^"]+)"', r.text).group(1)
passwd = 'cultivatesandspreadslove13579' + chr(33)
r = s.post(ADMIN + '/login', data={
    'email': 'damoncollective@gmail.com',
    'passwd': passwd,
    'stay_logged_in': '0',
    '_token': ft,
    'submitLogin': '1',
}, allow_redirects=True)
m = re.search(r'[?&]token=([A-Za-z0-9._\-]+)', r.url)
tok = m.group(1)
print('Logged in, token:', tok[:12] + '...')

r2 = s.get(ADMIN + '/index.php', params={'controller': 'AdminCategories', 'token': tok}, allow_redirects=True)
print('Categories page size:', len(r2.text))

# Extract from table links
rows = re.findall(r'href="[^"]*id_category=(\d+)[^"]*">([^<]{1,80})</a>', r2.text)
seen = set()
print('\nALL CATEGORIES:')
for cid, name in rows:
    key = (cid, name.strip())
    if key not in seen:
        seen.add(key)
        print(f'  id={cid:>4}  {name.strip()}')

if not seen:
    # try alternate pattern
    rows2 = re.findall(r'<td[^>]*class="[^"]*title[^"]*"[^>]*>(.*?)</td>', r2.text, re.S)
    print('Alt rows:', rows2[:20])
