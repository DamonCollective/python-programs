#!/usr/bin/env python3
"""
Set related products for 1821 hero wig+moustache pairs.

Pairs (each product gets the other as related):
  Kolokotronis wig  (265) ↔ Kolokotronis moustache (270)
  Karaiskakis wig   (266) ↔ Karaiskakis moustache  (269)
  Diakos wig        (267) ↔ Diakos moustache        (268)
  Kapodistrias      (386)   no moustache
"""
import requests, re, sys, html as html_mod
sys.stdout.reconfigure(encoding='utf-8')

ADMIN  = 'https://alegro.gr/admin875fdclzkf27m3shsg9'
EMAIL  = 'damoncollective@gmail.com'
PASSWD = 'cultivatesandspreadslove13579' + chr(33)

# Each tuple: (wig_id, moustache_id)
PAIRS = [
    (265, 270),  # Kolokotronis
    (266, 269),  # Karaiskakis
    (267, 268),  # Diakos
]

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

# ── Login ──────────────────────────────────────────────────────────────────────
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


def search_product(pid, edit_tok):
    """Search by ID to get name+image for the related products widget."""
    r = s.get(
        f'{ADMIN}/index.php/sell/catalog/products/search/en',
        params={'query': str(pid), '_token': edit_tok},
        timeout=15,
    )
    try:
        results = r.json()
        for item in results:
            if int(item['id']) == pid:
                return {'name': item.get('name', ''), 'image': item.get('image', '')}
        # fallback: return first result if any
        if results:
            return {'name': results[0].get('name', ''), 'image': results[0].get('image', '')}
    except Exception:
        print(f'  [warn] search({pid}) non-JSON: {r.text[:200]}')
    return {'name': '', 'image': ''}


def strip_related(payload):
    for k in [k for k in payload if 'related_products' in k]:
        del payload[k]


# ── Build lookup: pid → {name, image} ─────────────────────────────────────────
# Get a search token from product 265
r_tmp = s.get(f'{ADMIN}/index.php/sell/catalog/products/265/edit',
              params={'_token': cat_tok}, allow_redirects=True, timeout=25)
search_tok = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r_tmp.url).group(1)

all_pids = sorted({pid for pair in PAIRS for pid in pair})
print('Building lookup for PIDs:', all_pids)
lookup = {}
for pid in all_pids:
    info = search_product(pid, search_tok)
    lookup[pid] = info
    print(f'  {pid}: {info["name"][:60]}')
print()


# ── Process each product in each pair ─────────────────────────────────────────
ok, fail = 0, 0

for wig_id, moust_id in PAIRS:
    for pid, related_id in [(wig_id, moust_id), (moust_id, wig_id)]:
        rel_info = lookup.get(related_id, {'name': '', 'image': ''})
        print(f'PID {pid} → related: {related_id} ({rel_info["name"][:50]})')

        r_edit = s.get(f'{ADMIN}/index.php/sell/catalog/products/{pid}/edit',
                       params={'_token': cat_tok}, allow_redirects=True, timeout=25)
        edit_tok = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r_edit.url).group(1)
        html = r_edit.text

        all_inputs = scrape_form(html)
        payload = {k: html_mod.unescape(v) for k, v in all_inputs.items() if k not in EXCLUDE}

        strip_related(payload)

        payload['product[description][related_products][0][id]']    = str(related_id)
        payload['product[description][related_products][0][name]']  = rel_info['name']
        payload['product[description][related_products][0][image]'] = rel_info['image']

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
            print(f'  → OK')
            ok += 1
        else:
            inv = re.findall(r'name="([^"]+)"[^>]*class="[^"]*is-invalid', r_save.text, re.I)
            errs = re.findall(r'"message"\s*:\s*"([^"]+)"', r_save.text)
            print(f'  → FAIL  invalid: {inv[:4]}  errors: {errs[:3]}')
            fail += 1

print(f'\n{"═"*60}')
print(f'Done.  OK: {ok}  Failed: {fail}')
print(f'{"═"*60}')
