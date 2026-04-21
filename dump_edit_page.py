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
print('Page size:', len(r2.text))
print('URL token:', url_token[:80])

# Look for image-related tokens - various possible formats
print('\n--- image upload related ---')
img_section = re.findall(r'.{0,200}image.{0,200}', r2.text, re.I)
for s2 in img_section:
    if 'token' in s2.lower() or 'upload' in s2.lower() or 'form' in s2.lower():
        print(s2[:250])
        print('---')

# Look for any <div or component that has both 'image' and some token-like attr
print('\n--- divs with image ---')
divs = re.findall(r'<[a-z][^>]{0,500}image[^>]{0,500}>', r2.text, re.I)
for d in divs[:10]:
    print(d[:300])

# Try to find how image upload form is referenced
print('\n--- image/add url in page ---')
add_refs = re.findall(r'.{0,100}/images/add.{0,100}', r2.text, re.I)
for a in add_refs:
    print(a[:250])
