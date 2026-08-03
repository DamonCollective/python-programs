"""
Follow-up to fix_hero_name.py: the Greek product name for the Hero/Ηρώ
series (PIDs 37-45) still had the color word in English (e.g. "Περούκα
Ηρώ Green") after the Ήρωας->Ηρώ fix. Translates the trailing color word
to Greek, feminine form agreeing with "Περούκα" (matching the Xena/Cecilia
naming convention already used elsewhere on the site).

Does NOT touch product[seo][link_rewrite] (URL slug) — same reasoning as
fix_hero_name.py, leave live URLs alone.

Usage:
    python fix_hero_color_name.py
"""
import truststore
truststore.inject_into_ssl()

import requests, re, sys, html as html_mod, time

sys.stdout.reconfigure(encoding='utf-8')

ADMIN  = 'https://alegro.gr/admin875fdclzkf27m3shsg9'
PASSWD = 'cultivatesandspreadslove13579' + chr(33)
EMAIL  = 'damoncollective@gmail.com'

COLOR_MAP = {
    'Red': 'Κόκκινη',
    'Yellow': 'Κίτρινη',
    'Purple': 'Μωβ',
    'Green': 'Πράσινη',
    'Pink': 'Ροζ',
    'Black': 'Μαύρη',
    'Auburn': 'Ακαζού',
    'Blonde': 'Ξανθιά',
    'Fuchsia': 'Φούξια',
}
PIDS = [37, 38, 39, 40, 41, 42, 43, 44, 45]

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
print(f'Logged in. Fixing color word for {len(PIDS)} products…\n')

ok_count = fail_count = skip_count = 0

for pid in PIDS:
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

        name_key = 'product[header][name][2]'
        current_name = html_mod.unescape(all_inputs.get(name_key, ''))
        print(f'[PID {pid}] "{current_name}"', end='')

        new_name = current_name
        for en, el in COLOR_MAP.items():
            if current_name.endswith(en):
                new_name = current_name[:-len(en)] + el
                break

        if new_name == current_name:
            print('  -> SKIP (no known trailing English color word found)\n')
            skip_count += 1
            continue

        payload[name_key] = new_name
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
            print(f'  -> "{new_name}"  OK\n')
            ok_count += 1
        else:
            inv = re.findall(r'name="([^"]+)"[^>]*class="[^"]*is-invalid', r_save.text, re.I)
            print(f'  -> FAIL  invalid fields: {inv[:5]}\n')
            fail_count += 1

    except Exception as e:
        print(f'  -> ERROR: {e}\n')
        fail_count += 1

    time.sleep(0.5)

print(f'Done. {ok_count} OK  /  {skip_count} skipped  /  {fail_count} failed.')
