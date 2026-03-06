"""Quick debug: fetch one product edit page and show how descriptions are stored."""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8')

ADMIN  = 'https://alegro.gr/admin875fdclzkf27m3shsg9'
PASSWD = 'cultivatesandspreadslove13579' + chr(33)
EMAIL  = 'damoncollective@gmail.com'
PID    = 21  # Xena black wig — has a known description

s = requests.Session()
s.headers['User-Agent'] = 'Mozilla/5.0'
r = s.get(ADMIN + '/login')
ft = re.search(r'name="_token"\s+value="([^"]+)"', r.text).group(1)
r = s.post(ADMIN + '/login',
           data={'email': EMAIL, 'passwd': PASSWD,
                 'stay_logged_in': '0', '_token': ft, 'submitLogin': '1'},
           allow_redirects=True)
m = re.search(r'[?&]token=([A-Za-z0-9._\-]+)', r.url)
legacy = m.group(1) if m else ''
r2 = s.get(ADMIN + '/index.php', params={'controller': 'AdminProducts', 'token': legacy}, allow_redirects=True)
cat_tok = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r2.url).group(1)
print(f'cat_tok: {cat_tok[:20]}…')

r_edit = s.get(f'{ADMIN}/index.php/sell/catalog/products/{PID}/edit',
               params={'_token': cat_tok}, allow_redirects=True, timeout=25)
html = r_edit.text
print(f'Final URL: {r_edit.url[-80:]}')
print(f'HTML length: {len(html):,}')

# Search for description-related content
print('\n--- data-form-name ---')
print(re.findall(r'data-form[^"]{0,30}"[^"]{0,40}"', html, re.I)[:5])

print('\n--- textarea name patterns ---')
for m in re.finditer(r'<textarea[^>]{0,200}>', html, re.I):
    print(m.group(0)[:200])

print('\n--- description field search ---')
print('description[1] in html:', 'description][1]' in html)
print('description_short in html:', 'description_short' in html)

# Check for the description content in any format
for pat in ['product\\[description\\]', 'tinymce', 'wysiwyg', 'description.*lang']:
    found = re.findall(pat, html, re.I)[:2]
    if found:
        print(f'{pat}: {found}')

# Look for how description is stored — check 500 chars around "description"
idx = html.find('description][description][1]')
if idx >= 0:
    print(f'\nContext around description[1]:\n{html[max(0,idx-100):idx+300]}')
