"""
Fixes the Greek product name for the Hero/Ηρώ series (PIDs 37-45): the Greek
name field currently reads "Περούκα Ήρωας <Color>" (Ήρωας = "the hero"),
but Ηρώ is a female Greek name unrelated to "hero" — the English name "Hero"
is a transliteration of Ηρώ, not the English word "hero". Corrects the
Greek name field only, replacing "Ήρωας" with "Ηρώ".

Deliberately does NOT touch product[seo][link_rewrite] (the URL slug) —
changing live URLs risks breaking existing indexing/links, and wasn't asked
for. Only the visible name field is corrected.

Usage:
    python fix_hero_name.py
    python fix_hero_name.py 37 38     # specific PIDs only
"""
import truststore
truststore.inject_into_ssl()

import requests, re, sys, html as html_mod, time

sys.stdout.reconfigure(encoding='utf-8')

ADMIN  = 'https://alegro.gr/admin875fdclzkf27m3shsg9'
PASSWD = 'cultivatesandspreadslove13579' + chr(33)
EMAIL  = 'damoncollective@gmail.com'

PIDS = [37, 38, 39, 40, 41, 42, 43, 44, 45]
if len(sys.argv) > 1:
    PIDS = [int(x) for x in sys.argv[1:]]

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
print(f'Logged in. Fixing name for {len(PIDS)} products…\n')

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

        if 'Ήρωας' not in current_name:
            print('  -> SKIP (no "Ήρωας" found, already fixed or unexpected text)\n')
            skip_count += 1
            continue

        new_name = current_name.replace('Ήρωας', 'Ηρώ')
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
