#!/usr/bin/env python3
"""
Batch set available_for_order=1 for all products.

Fixes the ⊘ symbol showing even for in-stock products.
After this fix PS9 correctly shows:
  green tick  = in stock  (qty > 0)
  ⊘           = out of stock (qty = 0)

Skips products already set correctly. 5 parallel workers.
"""
import requests, re, sys, html as html_mod, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
sys.stdout.reconfigure(encoding='utf-8')

ADMIN   = 'https://alegro.gr/admin875fdclzkf27m3shsg9'
EMAIL   = 'damoncollective@gmail.com'
PASSWD  = 'cultivatesandspreadslove13579' + chr(33)
WORKERS = 5

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

INVALID_CHARS = re.compile(r'[<>;=#{}\[\]]')
print_lock = Lock()

def log(msg):
    with print_lock:
        print(msg, flush=True)

def make_session():
    s = requests.Session()
    s.headers['User-Agent'] = 'Mozilla/5.0'
    r = s.get(ADMIN + '/login')
    ft = re.search(r'name="_token"\s+value="([^"]+)"', r.text).group(1)
    r = s.post(ADMIN + '/login',
               data={'email': EMAIL, 'passwd': PASSWD,
                     'stay_logged_in': '0', '_token': ft, 'submitLogin': '1'},
               allow_redirects=True)
    m = re.search(r'[?&]token=([A-Za-z0-9._\-]+)', r.url)
    legacy_tok = m.group(1) if m else ''
    r2 = s.get(ADMIN + '/index.php',
               params={'controller': 'AdminProducts', 'token': legacy_tok},
               allow_redirects=True)
    cat_token = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r2.url).group(1)
    return s, cat_token


def process_product(s, cat_token, pid):
    try:
        r_edit = s.get(f'{ADMIN}/index.php/sell/catalog/products/{pid}/edit',
                       params={'_token': cat_token}, allow_redirects=True, timeout=20)
        edit_tok_m = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r_edit.url)
        if not edit_tok_m:
            return pid, 'SKIP', 'no token'
        edit_tok = edit_tok_m.group(1)
        html = r_edit.text

        # Check current value — skip if already correct
        afo_m = re.search(
            r'name="product\[options\]\[visibility\]\[available_for_order\]"\s+value="([^"]*)"',
            html, re.I)
        if afo_m and afo_m.group(1) == '1':
            return pid, 'ALREADY_OK', ''

        # Scrape full form
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
            if not nm or 'paginator' in nm.group(1):
                continue
            sel = (re.search(r'<option[^>]+selected[^>]*value="([^"]*)"', body, re.I) or
                   re.search(r'<option[^>]*value="([^"]*)"', body, re.I))
            all_inputs[nm.group(1)] = sel.group(1) if sel else ''

        payload = {k: html_mod.unescape(v) for k, v in all_inputs.items() if k not in EXCLUDE}

        for k in list(payload.keys()):
            if 'name][' in k and INVALID_CHARS.search(payload[k]):
                payload[k] = INVALID_CHARS.sub('', payload[k]).strip()

        payload['product[options][visibility][available_for_order]'] = '1'
        payload['product[details][features][feature_id]']            = '0'
        payload['product[options][visibility][visibility]']           = 'both'
        payload['product[options][visibility][online_only]']          = '0'
        payload['product[shipping][delivery_time_note_type]']         = '1'
        payload['_token'] = edit_tok

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
            return pid, 'FIXED', ''
        else:
            inv = re.findall(r'name="([^"]+)"[^>]*class="[^"]*is-invalid', r_save.text, re.I)
            errs = re.findall(r'"message"\s*:\s*"([^"]+)"', r_save.text)
            return pid, 'FAIL', f'inv={inv[:2]} errs={errs[:2]}'
    except Exception as e:
        return pid, 'ERROR', str(e)[:80]


# ── Main ───────────────────────────────────────────────────────────────────────
log('Logging in...')
s0, cat0 = make_session()

log('Loading product IDs from backup JSON...')
import json
with open('/home/hrundivbachsi/alegro/descriptions_backup_20260304.json') as f:
    _backup = json.load(f)
pids = sorted(int(k) for k in _backup.keys())
log(f'Found {len(pids)} products.\n')

log(f'Spawning {WORKERS} worker sessions...')
sessions = [make_session() for _ in range(WORKERS)]

tasks = [(i % WORKERS, pid) for i, pid in enumerate(pids)]
start = time.time()
done = fixed = skipped = fail = 0

def worker_task(args):
    idx, pid = args
    s, cat = sessions[idx]
    return process_product(s, cat, pid)

with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    futures = {ex.submit(worker_task, t): t[1] for t in tasks}
    for fut in as_completed(futures):
        pid, status, msg = fut.result()
        done += 1
        if status == 'FIXED':
            fixed += 1
            log(f'  [{done:3d}/{len(pids)}] PID {pid}: FIXED')
        elif status == 'ALREADY_OK':
            skipped += 1
        else:
            fail += 1
            log(f'  [{done:3d}/{len(pids)}] PID {pid}: {status} — {msg}')
        if done % 50 == 0:
            log(f'  [{done:3d}/{len(pids)}] {fixed} fixed, {skipped} already OK, {fail} failed')

elapsed = time.time() - start
log(f'\n{"═"*60}')
log(f'Done in {elapsed:.0f}s')
log(f'  Fixed:      {fixed}')
log(f'  Already OK: {skipped}')
log(f'  Failed:     {fail}')
log(f'{"═"*60}')
