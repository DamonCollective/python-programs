"""
Analyze the product_edit bundle to find exactly how Vue.js saves the product form.
Focus on: form submission, categories, feature_id handling.
"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8')

ADMIN = 'https://alegro.gr/admin875fdclzkf27m3shsg9'

s = requests.Session()
s.headers['User-Agent'] = 'Mozilla/5.0'

r = s.get(ADMIN + '/login')
ft = re.search(r'name="_token"\s+value="([^"]+)"', r.text).group(1)
passwd = 'cultivatesandspreadslove13579' + chr(33)
r = s.post(ADMIN + '/login', data={'email':'damoncollective@gmail.com','passwd':passwd,'stay_logged_in':'0','_token':ft,'submitLogin':'1'}, allow_redirects=True)

# Fetch the large product_edit bundle
bundle_url = 'https://alegro.gr/admin875fdclzkf27m3shsg9/themes/new-theme/public/product_edit.bundle.js?9.0.0'
r_bundle = s.get(bundle_url)
bundle = r_bundle.text
print(f'Bundle size: {len(bundle):,} chars')

# Save bundle to file for analysis
with open('C:/Users/Damon/Desktop/product_edit.bundle.js', 'w', encoding='utf-8') as f:
    f.write(bundle)
print('Bundle saved to product_edit.bundle.js')

# Search for category-related code
print('\n--- Searching for product_categories in bundle ---')
for m in re.finditer(r'.{0,100}product_categories.{0,100}', bundle):
    snippet = m.group().strip()
    print(f'  {snippet[:200]}')

print('\n--- Searching for "feature" in bundle ---')
seen = set()
for m in re.finditer(r'.{0,80}feature.{0,80}', bundle, re.I):
    snippet = m.group().strip()[:150]
    # Only show unique snippets with interesting content
    if any(kw in snippet.lower() for kw in ['submit', 'save', 'post', 'send', 'valid', 'required', 'data']):
        key = snippet[:50]
        if key not in seen:
            seen.add(key)
            print(f'  {snippet}')

print('\n--- Looking for form serialization/submission code ---')
for m in re.finditer(r'.{0,50}(?:serialize|FormData|submit|\.post\(|form\.get|\.send\().{0,150}', bundle, re.I):
    snippet = m.group().strip()
    if len(snippet) > 20:
        print(f'  {snippet[:200]}')

print('\n--- Looking for "save" function ---')
seen2 = set()
for m in re.finditer(r'.{0,30}(?:saveProduct|onSave|handleSave|doSave|submitForm).{0,200}', bundle, re.I):
    snippet = m.group().strip()[:200]
    key = snippet[:40]
    if key not in seen2:
        seen2.add(key)
        print(f'  {snippet}')
