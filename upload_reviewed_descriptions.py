"""
Step 3 of the description-review pipeline.

Pushes the reviewed (status == 'done') descriptions from
review_state.json to alegro.gr, using the same scrape-then-overwrite
form-submit pattern as apply_descriptions_part1.py (proven to work
against this PS9 admin).

Only touches: description, description_short (EN + EL). Does not change
names, slugs, or anything else on the product.

Usage:
    python upload_reviewed_descriptions.py            # all done items
    python upload_reviewed_descriptions.py 251 253     # specific PIDs only
"""
import truststore
truststore.inject_into_ssl()

import requests, re, sys, json, html as html_mod, time

sys.stdout.reconfigure(encoding='utf-8')

ADMIN  = 'https://alegro.gr/admin875fdclzkf27m3shsg9'
PASSWD = 'cultivatesandspreadslove13579' + chr(33)
EMAIL  = 'damoncollective@gmail.com'
STATE_FILE = r'C:\Users\Damon\Desktop\review_state.json'

args = sys.argv[1:]
if args and args[0].startswith('--state='):
    STATE_FILE = args[0][len('--state='):]
    args = args[1:]

with open(STATE_FILE, encoding='utf-8') as f:
    state = json.load(f)

items = [i for i in state if i['status'] == 'done']
if args:
    pids = [int(x) for x in args]
    items = [i for i in items if i['id'] in pids]
    print(f'Running only PIDs: {sorted(pids)}')

if not items:
    print('Nothing to upload — no items with status "done" (run review_descriptions.py first).')
    sys.exit(0)

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

# ── Login ─────────────────────────────────────────────────────────────────
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
print(f'Logged in. Uploading {len(items)} products…\n')

ok_count = fail_count = 0

for item in items:
    pid = item['id']
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

        # Only touch descriptions — leave name/slug/meta as-is
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
            print(f'  -> OK\n')
            ok_count += 1
        else:
            inv = re.findall(r'name="([^"]+)"[^>]*class="[^"]*is-invalid', r_save.text, re.I)
            print(f'  -> FAIL  invalid fields: {inv[:5]}\n')
            fail_count += 1

    except Exception as e:
        print(f'  -> ERROR: {e}\n')
        fail_count += 1

    time.sleep(0.5)

print(f'Done. {ok_count} OK  /  {fail_count} failed.')
