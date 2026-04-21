import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8')

ADMIN = 'https://alegro.gr/admin875fdclzkf27m3shsg9'
PRODUCT_ID = 386

s = requests.Session()
s.headers['User-Agent'] = 'Mozilla/5.0'

# Login
r = s.get(ADMIN + '/login')
ft = re.search(r'name="_token"\s+value="([^"]+)"', r.text).group(1)
passwd = 'cultivatesandspreadslove13579' + chr(33)
r = s.post(ADMIN + '/login', data={'email':'damoncollective@gmail.com','passwd':passwd,'stay_logged_in':'0','_token':ft,'submitLogin':'1'}, allow_redirects=True)

# Go through catalog to get proper Symfony _token
m = re.search(r'[?&]token=([A-Za-z0-9._\-]+)', r.url)
legacy_token = m.group(1) if m else ''

# Fetch catalog for a proper _token
r2 = s.get(ADMIN + '/index.php', params={'controller':'AdminProducts','token':legacy_token}, allow_redirects=True)
# extract _token from catalog URL
cat_token_m = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r2.url)
cat_token = cat_token_m.group(1) if cat_token_m else legacy_token
print('Catalog token:', cat_token[:60])
print('Catalog page size:', len(r2.text))

# Now fetch edit page with catalog token
r3 = s.get(f'{ADMIN}/index.php/sell/catalog/products/{PRODUCT_ID}/edit',
           params={'_token': cat_token}, allow_redirects=True)
edit_token = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r3.url)
edit_token = edit_token.group(1) if edit_token else cat_token
print('Edit page size:', len(r3.text))
print('Edit URL token:', edit_token[:60])

# Save a snippet of the edit page for inspection
with open('edit_page_snippet.txt', 'w', encoding='utf-8') as f:
    # Look for image-related content
    f.write("=== FULL PAGE (first 5000 chars) ===\n")
    f.write(r3.text[:5000])
    f.write("\n\n=== LAST 2000 chars ===\n")
    f.write(r3.text[-2000:])

print('Saved edit page snippet to edit_page_snippet.txt')

# Search for various token patterns
print('\n--- Token patterns in edit page ---')
patterns_to_search = [
    r'_token[^"]{0,10}[":][^"]{0,5}"([^"]{20,200})"',
    r'"token"\s*:\s*"([^"]{20,200})"',
    r'token%22%3A%22([^%"]{20,200})',
    r'token=([A-Za-z0-9._\-]{30,})',
]
for p in patterns_to_search:
    hits = re.findall(p, r3.text)
    if hits:
        print(f'  Pattern {p[:40]}:')
        for h in hits[:3]:
            print(f'    {h[:80]}')

# Search for product image related JS
print('\n--- Image upload vars in page ---')
img_vars = re.findall(r'.{0,50}(?:image|upload|dropzone).{0,150}', r3.text, re.I)
for v in img_vars[:10]:
    if 'token' in v.lower() or 'url' in v.lower():
        print(v[:250])
