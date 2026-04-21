#!/usr/bin/env python3
"""
Set related products for Cecilia and Xena wig groups.

Each product in a group gets all other members of that group as related products.

Cecilia (bob wig, 7 colors): 46 47 48 49 50 51 52
Xena (long wig, 13 colors):  21 22 23 24 63 65 66 67 68 69 70 71 72
"""
import requests, re, sys, html as html_mod
sys.stdout.reconfigure(encoding='utf-8')

ADMIN  = 'https://alegro.gr/admin875fdclzkf27m3shsg9'
EMAIL  = 'damoncollective@gmail.com'
PASSWD = 'cultivatesandspreadslove13579' + chr(33)

CECILIA_IDS = [46, 47, 48, 49, 50, 51, 52]
XENA_IDS    = [21, 22, 23, 24, 63, 65, 66, 67, 68, 69, 70, 71, 72]

EXCLUDE = {
    'product[details][features][feature_value_id]',
    'product[details][features][custom_value][1]',
    'product[details][features][custom_value][2]',
    'product[pricing][priority_management][use_custom_priority]',
    'product[pricing][priority_management][priorities][0]',
    'product[pricing][priority_management][priorities][1]',
    'product[pricing][priority_management][priorities][2]',
    'product[pricing][priority_management][priorities][3]',
    'product[pricing][on_sale]',
    'product[options][visibility][visibility]',
    'product[options][visibility][online_only]',
}

# ── Login ─────────────────────────────────────────────────────────────────────
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
print('Logged in.\n')


def scrape_form(html):
    """Return dict of all input/select values from an edit page."""
    inputs = {}
    for im in re.finditer(r'<input[^>]+>', html, re.I):
        tag = im.group(0)
        nm = re.search(r'\bname="([^"]+)"', tag, re.I)
        vm = re.search(r'\bvalue="([^"]*)"', tag, re.I)
        if nm:
            inputs[nm.group(1)] = vm.group(1) if vm else ''
    for sm in re.finditer(r'<select([^>]*)>(.*?)</select>', html, re.I | re.S):
        attrs, body = sm.group(1), sm.group(2)
        nm = re.search(r'\bname="([^"]+)"', attrs, re.I)
        if not nm or 'paginator' in nm.group(1):
            continue
        sel = (re.search(r'<option[^>]+selected[^>]*value="([^"]*)"', body, re.I) or
               re.search(r'<option[^>]*value="([^"]*)"', body, re.I))
        inputs[nm.group(1)] = sel.group(1) if sel else ''
    return inputs


def search_products(query, edit_tok):
    """Call PS9 search endpoint and return list of {id, name, image} dicts."""
    r = s.get(
        f'{ADMIN}/index.php/sell/catalog/products/search/en',
        params={'query': query, '_token': edit_tok},
        timeout=15,
    )
    try:
        return r.json()
    except Exception:
        print(f'  [warn] search("{query}") returned non-JSON: {r.text[:200]}')
        return []


def strip_related(payload):
    """Remove any existing related_products keys from payload."""
    to_del = [k for k in payload if 'related_products' in k]
    for k in to_del:
        del payload[k]


# ── Build lookup: pid → {name, image} ─────────────────────────────────────────
# We need an edit_tok for the search; grab one from the first product in each group.
print('Building product lookup via search...')

# Grab a token from product 46 (first Cecilia)
r_tmp = s.get(f'{ADMIN}/index.php/sell/catalog/products/46/edit',
              params={'_token': cat_tok}, allow_redirects=True, timeout=25)
search_tok = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r_tmp.url).group(1)

lookup = {}  # pid (int) → {name, image}

for query in ('Cecilia', 'Xena Long'):
    results = search_products(query, search_tok)
    for item in results:
        pid = int(item['id'])
        lookup[pid] = {'name': item.get('name', ''), 'image': item.get('image', '')}
    print(f'  Search "{query}": {len(results)} results')

print(f'  Lookup built: {sorted(lookup.keys())}')
print()

# ── Verify all group members are in lookup ─────────────────────────────────────
all_pids = CECILIA_IDS + XENA_IDS
missing = [p for p in all_pids if p not in lookup]
if missing:
    print(f'WARNING: PIDs not found in search results: {missing}')
    print('These will be skipped as related products.\n')


# ── Process each group ─────────────────────────────────────────────────────────
def process_group(group_ids, group_name):
    ok, fail = 0, 0
    for pid in group_ids:
        # Siblings = all group members except this product
        siblings = [p for p in group_ids if p != pid and p in lookup]

        print(f'PID {pid} — {group_name} ({len(siblings)} related)')
        r_edit = s.get(f'{ADMIN}/index.php/sell/catalog/products/{pid}/edit',
                       params={'_token': cat_tok}, allow_redirects=True, timeout=25)
        edit_tok = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r_edit.url).group(1)
        html = r_edit.text

        all_inputs = scrape_form(html)
        payload = {k: html_mod.unescape(v) for k, v in all_inputs.items() if k not in EXCLUDE}

        # Strip old related products
        strip_related(payload)

        # Set new related products
        for n, rel_id in enumerate(siblings):
            info = lookup[rel_id]
            payload[f'product[description][related_products][{n}][id]']    = str(rel_id)
            payload[f'product[description][related_products][{n}][name]']  = info['name']
            payload[f'product[description][related_products][{n}][image]'] = info['image']

        # Standard overrides
        payload['product[details][features][feature_id]']     = '0'
        payload['product[options][visibility][visibility]']   = 'both'
        payload['product[options][visibility][online_only]']  = '0'
        payload['product[shipping][delivery_time_note_type]'] = '1'
        payload['_token'] = edit_tok

        r_save = s.post(
            f'{ADMIN}/index.php/sell/catalog/products/{pid}/edit',
            params={'_token': edit_tok},
            data=payload,
            headers={'Referer': r_edit.url},
            allow_redirects=True, timeout=25,
        )
        fv = re.search(r'data-form-valid="(\d+)"', r_save.text)
        valid = fv.group(1) if fv else '?'
        if valid == '1':
            print(f'  → OK ({len(siblings)} related)')
            ok += 1
        else:
            inv = re.findall(r'name="([^"]+)"[^>]*class="[^"]*is-invalid', r_save.text, re.I)
            errs = re.findall(r'"message"\s*:\s*"([^"]+)"', r_save.text)
            print(f'  → FAIL  invalid: {inv[:4]}  errors: {errs[:3]}')
            fail += 1
    return ok, fail


ok_total, fail_total = 0, 0

print('=== Cecilia group ===')
o, f = process_group(CECILIA_IDS, 'Cecilia')
ok_total += o; fail_total += f

print()
print('=== Xena group ===')
o, f = process_group(XENA_IDS, 'Xena Long')
ok_total += o; fail_total += f

print(f'\n{"═"*60}')
print(f'Done.  OK: {ok_total}  Failed: {fail_total}')
print(f'{"═"*60}')
