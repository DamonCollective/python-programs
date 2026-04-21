import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8')

ADMIN = 'https://alegro.gr/admin875fdclzkf27m3shsg9'
PRODUCT_ID = 386

s = requests.Session()
s.headers['User-Agent'] = 'Mozilla/5.0'

r = s.get(ADMIN + '/login')
ft = re.search(r'name="_token"\s+value="([^"]+)"', r.text).group(1)
passwd = 'cultivatesandspreadslove13579' + chr(33)
r = s.post(ADMIN + '/login', data={'email':'damoncollective@gmail.com','passwd':passwd,'stay_logged_in':'0','_token':ft,'submitLogin':'1'}, allow_redirects=True)
m = re.search(r'[?&]_?token=([A-Za-z0-9._\-]+)', r.url)
url_token = m.group(1) if m else ''

r2 = s.get(f'{ADMIN}/index.php/sell/catalog/products/{PRODUCT_ID}/edit', params={'_token': url_token}, allow_redirects=True)
url_token = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r2.url).group(1)
print('URL token:', url_token[:60])

# Find ALL data-token occurrences with context
all_dt = re.findall(r'.{0,80}data-token="([^"]+)".{0,80}', r2.text)
print(f'\nAll data-token occurrences ({len(all_dt)}):')
for i, match in enumerate(all_dt):
    # match is (context) - but since we captured the token, let's redo
    pass

all_dt2 = [(m.start(), m.group(1), r2.text[max(0,m.start()-100):m.start()+150])
           for m in re.finditer(r'data-token="([^"]+)"', r2.text)]
for pos, token, ctx in all_dt2[:20]:
    print(f'\n  pos={pos}  token={token[:60]}')
    print(f'  ctx: {ctx[:200].strip()}')
