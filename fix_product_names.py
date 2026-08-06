"""
Fixes the product NAME field (product[header][name][2], Greek only) for
products where a description rewrite renamed a colour/detail but the
name field was never touched (upload_reviewed_descriptions.py only ever
touches description/description_short).

Also fixes the Greek URL slug (product[seo][link_rewrite][2]) for PID 91
per explicit request (perouka-tou-aera -> perouka-anemos).

SAFETY: PS9's description/description_short fields are <textarea>s, not
scraped by the generic input/select scrape below. This script explicitly
re-sets them from all_products_state.json (the known-good, already-live
text) on every submit, exactly like upload_reviewed_descriptions.py does.
Never rely on scraping textareas — see fix_hero_name.py incident in memory
where skipping this wiped descriptions for 9 products.

Usage:
    python fix_product_names.py
"""
import truststore
truststore.inject_into_ssl()

import requests, re, sys, json, html as html_mod, time

sys.stdout.reconfigure(encoding='utf-8')

ADMIN  = 'https://alegro.gr/admin875fdclzkf27m3shsg9'
PASSWD = 'cultivatesandspreadslove13579' + chr(33)
EMAIL  = 'damoncollective@gmail.com'
STATE_FILE = r'C:\Users\Damon\Desktop\all_products_state.json'

with open(STATE_FILE, encoding='utf-8') as f:
    state = json.load(f)
by_id = {item['id']: item for item in state}

# (pid, old_substring_in_name, new_substring, new_slug_or_None)
RENAMES = [
    (65, 'Ανοιχτή Καστανή', 'Μελί', None),
    (66, 'με Φράντζα', 'με Αφέλεια', None),
    (67, 'με Φράντζα', 'με Αφέλεια', None),
    (68, 'με Φράντζα', 'με Αφέλεια', None),
    (69, 'με Φράντζα', 'με Αφέλεια', None),
    (70, 'με Φράντζα', 'με Αφέλεια', None),
    (71, 'με Φράντζα', 'με Αφέλεια', None),
    (72, 'με Φράντζα', 'με Αφέλεια', None),
    (76, 'Ανοιχτή Καστανή', 'Μελί', None),
    (91, 'Αέρας', 'Άνεμος', 'perouka-anemos'),
]
# PID 65 also needs the Φράντζα->Αφέλεια fix in the same name (two substitutions)
RENAMES_EXTRA = {65: [('Ανοιχτή Καστανή', 'Μελί'), ('με Φράντζα', 'με Αφέλεια')]}

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
r2 = s.get(ADMIN + '/index.php',
           params={'controller': 'AdminProducts', 'token': legacy},
           allow_redirects=True)
cat_tok = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r2.url).group(1)
print(f'Logged in. Fixing names for {len(RENAMES)} products…\n')

ok_count = fail_count = 0

for pid, old_sub, new_sub, new_slug in RENAMES:
    item = by_id.get(pid)
    if item is None:
        print(f'[PID {pid}] not in state file, skipping')
        fail_count += 1
        continue
    print(f'[PID {pid}] {item["name_en"][:55]}…')
    try:
        r_edit = s.get(
            f'{ADMIN}/index.php/sell/catalog/products/{pid}/edit',
            params={'_token': cat_tok}, allow_redirects=True, timeout=30
        )
        edit_tok = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r_edit.url).group(1)
        html = r_edit.text

        all_inputs = {}
        for im in re.finditer(r'<input[^>]+>', html, re.I):
            tag = im.group(0)
            nm = re.search(r'\bname="([^"]+)"', tag, re.I)
            vm = re.search(r'\bvalue="([^"]*)"', tag, re.I)
            if nm:
                all_inputs[nm.group(1)] = vm.group(1) if vm else ''

        for sm in re.finditer(r'<select([^>]*)>(.*?)</select>', html, re.I | re.S):
            attrs, body = sm.group(1), sm.group(2)
            nm = re.search(r'\bname="([^"]+)"', attrs, re.I)
            if not nm or 'paginator' in nm.group(1):
                continue
            sel = (re.search(r'<option[^>]+selected[^>]*value="([^"]*)"', body, re.I) or
                   re.search(r'<option[^>]*value="([^"]*)"', body, re.I))
            all_inputs[nm.group(1)] = sel.group(1) if sel else ''

        payload = {k: html_mod.unescape(v)
                   for k, v in all_inputs.items() if k not in EXCLUDE}

        payload['product[details][features][feature_id]']     = '0'
        payload['product[options][visibility][visibility]']   = 'both'
        payload['product[options][visibility][online_only]']  = '0'
        payload['product[shipping][delivery_time_note_type]'] = '1'

        # Rename the Greek name field
        current_name = payload.get('product[header][name][2]', '')
        if pid in RENAMES_EXTRA:
            new_name = current_name
            for o, n in RENAMES_EXTRA[pid]:
                new_name = new_name.replace(o, n)
        else:
            new_name = current_name.replace(old_sub, new_sub)
        if new_name == current_name:
            print(f'  -> WARNING: substring "{old_sub}" not found in name "{current_name}" — no change made')
        payload['product[header][name][2]'] = new_name

        if new_slug:
            payload['product[seo][link_rewrite][2]'] = new_slug

        # Never rely on scraped textareas for descriptions — pin known-good values
        payload['product[description][description][1]']       = item['desc_en']
        payload['product[description][description][2]']       = item['desc_el']
        payload['product[description][description_short][1]'] = item['short_en']
        payload['product[description][description_short][2]'] = item['short_el']

        payload['_token'] = edit_tok

        r_save = s.post(
            f'{ADMIN}/index.php/sell/catalog/products/{pid}/edit',
            params={'_token': edit_tok},
            data=payload,
            headers={'Referer': r_edit.url},
            allow_redirects=True, timeout=30,
        )

        fv = re.search(r'data-form-valid="(\d+)"', r_save.text)
        valid = fv.group(1) if fv else '?'

        if valid == '1':
            print(f'  -> OK   "{current_name}" -> "{new_name}"' + (f'  slug -> {new_slug}' if new_slug else ''))
            ok_count += 1
        else:
            inv = re.findall(r'name="([^"]+)"[^>]*class="[^"]*is-invalid', r_save.text, re.I)
            print(f'  -> FAIL  invalid fields: {inv[:5]}')
            fail_count += 1

    except Exception as e:
        print(f'  -> ERROR: {e}')
        fail_count += 1

    time.sleep(0.5)

print(f'\nDone. {ok_count} OK  /  {fail_count} failed.')
