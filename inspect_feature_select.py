"""Inspect the feature_id select element and test various submission strategies."""
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
form_tok = re.search(r'name="product\[_token\]"[^>]*value="([^"]+)"', html).group(1)

# Find the feature_id select element
feat_select_m = re.search(
    r'<select[^>]*name="product\[details\]\[features\]\[feature_id\]"[^>]*>(.*?)</select>',
    html, re.I | re.S
)
if feat_select_m:
    print('feature_id SELECT HTML:')
    print(feat_select_m.group(0)[:500])
else:
    print('feature_id SELECT not found in HTML')
    # Look for it differently
    feat_area = re.search(r'.{0,200}feature_id.{0,500}', html, re.I | re.S)
    if feat_area:
        print('feature_id area:', feat_area.group()[:500])

# Get all inputs
all_inputs = {}
for m in re.finditer(r'<input[^>]+>', html, re.I):
    tag = m.group(0)
    nm = re.search(r'\bname="([^"]+)"', tag, re.I)
    vm = re.search(r'\bvalue="([^"]*)"', tag, re.I)
    if nm:
        all_inputs[nm.group(1)] = vm.group(1) if vm else ''

print(f'\nTotal inputs: {len(all_inputs)}')

# Test: submit form with feature_id using DIFFERENT value combinations
# and track which one gives form-valid=1

test_cases = [
    ('Not submitted (absent)', None),
    ('Empty string', ''),
    ('Zero string', '0'),
    ('One (Composition)', '1'),
]

print('\n=== Testing feature_id values ===')
for label, feat_val in test_cases:
    payload = {k: v for k, v in all_inputs.items() if not k.startswith('product[details][features]')}
    payload['_token'] = edit_tok

    if feat_val is not None:
        payload['product[details][features][feature_id]'] = feat_val
    # (if None → field absent)

    r_test = s.post(
        f'{ADMIN}/index.php/sell/catalog/products/{PID}/edit',
        params={'_token': edit_tok},
        data=payload,
        headers={'Referer': r_edit.url},
        allow_redirects=False,
    )

    fv = re.search(r'data-form-valid="(\d+)"', r_test.text)
    fs = re.search(r'data-form-submitted="(\d+)"', r_test.text)
    inv = re.findall(r'name="([^"]+)"[^>]*class="[^"]*is-invalid', r_test.text, re.I)
    loc = r_test.headers.get('Location', 'NONE')

    valid = fv.group(1) if fv else '?'
    submitted = fs.group(1) if fs else '?'
    print(f'  [{label:35s}] valid={valid} submitted={submitted} invalid={inv[:3]} loc={loc[:30]}')

# Test: submit ONLY product[header] and product[description] and product[seo] fields
print('\n=== Test: only header+description+seo fields ===')
payload_desc = {}
for k, v in all_inputs.items():
    if (k.startswith('product[header]') or
        k.startswith('product[description]') or
        k.startswith('product[seo]') or
        k == 'product[_token]'):
        payload_desc[k] = v

payload_desc['_token'] = edit_tok
# Add English name (product is currently Greek only, lang 1=EL based on earlier test)
payload_desc['product[header][name][1]'] = 'Ioannis Kapodistrias Theatrical Wig | Stage Wig | Made in Greece'
payload_desc['product[header][type]'] = all_inputs.get('product[header][type]', 'standard')

print(f'Fields: {len(payload_desc)}')
r_desc = s.post(
    f'{ADMIN}/index.php/sell/catalog/products/{PID}/edit',
    params={'_token': edit_tok},
    data=payload_desc,
    headers={'Referer': r_edit.url},
    allow_redirects=False,
)
fv = re.search(r'data-form-valid="(\d+)"', r_desc.text)
fs = re.search(r'data-form-submitted="(\d+)"', r_desc.text)
inv = re.findall(r'name="([^"]+)"[^>]*class="[^"]*is-invalid', r_desc.text, re.I)
loc = r_desc.headers.get('Location', 'NONE')
print(f'  valid={fv.group(1) if fv else "?"} submitted={fs.group(1) if fs else "?"} invalid={inv[:5]} loc={loc[:40]}')
