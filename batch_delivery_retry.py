"""
Retry the 26 failed products: strip invalid chars from name fields, then set delivery_time_note_type=0.
"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8')

ADMIN  = 'https://alegro.gr/admin875fdclzkf27m3shsg9'
PASSWD = 'cultivatesandspreadslove13579' + chr(33)
EMAIL  = 'damoncollective@gmail.com'

FAILED_PIDS = [150, 167, 181, 182, 193, 194, 195, 196, 197, 198, 199,
               225, 231, 238, 286, 288, 291, 300, 309, 317, 319, 328,
               335, 347, 382, 383]

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
}

INVALID_CHARS = re.compile(r'[<>;=#{}\[\]]')

def clean_name(v):
    return INVALID_CHARS.sub('', v).strip()

s = requests.Session()
s.headers['User-Agent'] = 'Mozilla/5.0'
r = s.get(ADMIN + '/login')
ft = re.search(r'name="_token"\s+value="([^"]+)"', r.text).group(1)
r = s.post(ADMIN + '/login', data={'email': EMAIL, 'passwd': PASSWD,
           'stay_logged_in': '0', '_token': ft, 'submitLogin': '1'}, allow_redirects=True)
m = re.search(r'[?&]token=([A-Za-z0-9._\-]+)', r.url)
legacy_tok = m.group(1) if m else ''
r2 = s.get(ADMIN + '/index.php', params={'controller': 'AdminProducts', 'token': legacy_tok}, allow_redirects=True)
cat_token = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r2.url).group(1)
print(f'Logged in. Retrying {len(FAILED_PIDS)} products...\n')

ok = fail = 0
for pid in FAILED_PIDS:
    r_edit = s.get(f'{ADMIN}/index.php/sell/catalog/products/{pid}/edit',
                   params={'_token': cat_token}, allow_redirects=True, timeout=20)
    edit_tok = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r_edit.url).group(1)
    html = r_edit.text

    all_inputs = {}
    for m in re.finditer(r'<input[^>]+>', html, re.I):
        tag = m.group(0)
        nm = re.search(r'\bname="([^"]+)"', tag, re.I)
        vm = re.search(r'\bvalue="([^"]*)"', tag, re.I)
        if nm:
            all_inputs[nm.group(1)] = vm.group(1) if vm else ''

    for sel_m in re.finditer(r'<select([^>]*)>(.*?)</select>', html, re.I | re.S):
        attrs, body = sel_m.group(1), sel_m.group(2)
        nm = re.search(r'\bname="([^"]+)"', attrs, re.I)
        if not nm or 'paginator' in nm.group(1): continue
        sel = (re.search(r'<option[^>]+selected[^>]*value="([^"]*)"', body, re.I) or
               re.search(r'<option[^>]*value="([^"]*)"', body, re.I))
        all_inputs[nm.group(1)] = sel.group(1) if sel else ''

    payload = {k: v for k, v in all_inputs.items() if k not in EXCLUDE}
    payload['product[details][features][feature_id]'] = '0'
    payload['product[shipping][delivery_time_note_type]'] = '0'
    payload['_token'] = edit_tok

    # Clean invalid chars from all name fields
    for k in list(payload.keys()):
        if 'name][' in k and INVALID_CHARS.search(payload[k]):
            old = payload[k]
            payload[k] = clean_name(old)
            print(f'  PID {pid} cleaned {k}: {repr(old[:50])} → {repr(payload[k][:50])}')

    r_save = s.post(
        f'{ADMIN}/index.php/sell/catalog/products/{pid}/edit',
        params={'_token': edit_tok},
        data=payload,
        headers={'Referer': r_edit.url},
        allow_redirects=True,
        timeout=20,
    )
    fv = re.search(r'data-form-valid="(\d+)"', r_save.text)
    valid = fv.group(1) if fv else '?'

    if valid == '1':
        print(f'  PID {pid}: OK')
        ok += 1
    else:
        inv = re.findall(r'name="([^"]+)"[^>]*class="[^"]*is-invalid', r_save.text, re.I)
        errs = re.findall(r'<div[^>]*alert-danger[^>]*>(.*?)</div>', r_save.text, re.I | re.S)
        err_text = ' | '.join(re.sub(r'<[^>]+>', ' ', e).strip()[:80] for e in errs[:1])
        print(f'  PID {pid}: FAIL — inv={inv[:3]} {err_text[:100]}')
        fail += 1

print(f'\nRetry done: {ok} OK, {fail} still failing')
