"""
Batch update all 337 products: set delivery_time_note_type=0 (use global default)
so every product shows "Παράδοση σε 1 - 2 ημέρες" on its page.
Uses 4 concurrent sessions for speed.
"""
import requests, re, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
sys.stdout.reconfigure(encoding='utf-8')

ADMIN = 'https://alegro.gr/admin875fdclzkf27m3shsg9'
PASSWD = 'cultivatesandspreadslove13579' + chr(33)
EMAIL  = 'damoncollective@gmail.com'
WORKERS = 4

EXCLUDE = {
    'product[details][features][feature_value_id]',
    'product[details][features][custom_value][1]',
    'product[details][features][custom_value][2]',
    'product[pricing][priority_management][use_custom_priority]',
    'product[pricing][priority_management][priorities][0]',
    'product[pricing][priority_management][priorities][1]',
    'product[pricing][priority_management][priorities][2]',
    'product[pricing][priority_management][priorities][3]',
    'product[pricing][on_sale]',  # preserve on_sale=off state
}

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

def update_product(s, cat_token, pid):
    try:
        r_edit = s.get(f'{ADMIN}/index.php/sell/catalog/products/{pid}/edit',
                       params={'_token': cat_token}, allow_redirects=True, timeout=20)
        edit_tok_m = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r_edit.url)
        if not edit_tok_m:
            return pid, 'SKIP', 'no edit token'
        edit_tok = edit_tok_m.group(1)
        html = r_edit.text

        # Check current delivery_time_note_type (skip if already 0)
        checked = re.search(
            r'name="product\[shipping\]\[delivery_time_note_type\]"[^>]*value="([^"]*)"[^>]*checked'
            r'|name="product\[shipping\]\[delivery_time_note_type\]"[^>]*checked[^>]*value="([^"]*)"',
            html, re.I)
        current_type = (checked.group(1) or checked.group(2)) if checked else '?'
        if current_type == '0':
            return pid, 'SKIP', 'already type=0'

        # Collect inputs
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
            sel = re.search(r'<option[^>]+selected[^>]*value="([^"]*)"', body, re.I)
            if not sel:
                sel = re.search(r'<option[^>]*value="([^"]*)"', body, re.I)
            all_inputs[nm.group(1)] = sel.group(1) if sel else ''

        payload = {k: v for k, v in all_inputs.items() if k not in EXCLUDE}
        payload['product[details][features][feature_id]'] = '0'
        payload['product[shipping][delivery_time_note_type]'] = '0'
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
            return pid, 'OK', f'was type={current_type}'
        else:
            errs = re.findall(r'<div[^>]*alert-danger[^>]*>(.*?)</div>', r_save.text, re.I | re.S)
            err_text = ' | '.join(re.sub(r'<[^>]+>', ' ', e).strip()[:60] for e in errs[:2])
            return pid, 'FAIL', f'valid={valid} {err_text}'
    except Exception as e:
        return pid, 'ERROR', str(e)[:80]

# ── Main ────────────────────────────────────────────────────────────────────
# Get all product IDs
log('Logging in to get product list...')
s0, cat_token0 = make_session()
r_list = s0.get(f'{ADMIN}/index.php/sell/catalog/products/',
                params={'_token': cat_token0, 'products[limit]': 1000},
                allow_redirects=True)
pids = sorted(set(int(p) for p in re.findall(r'/sell/catalog/products/(\d+)/edit', r_list.text)))
log(f'Found {len(pids)} products to process.')

# Create worker sessions
log(f'Starting {WORKERS} concurrent workers...')
sessions = [make_session() for _ in range(WORKERS)]
log('All sessions ready.')

results = {'OK': 0, 'SKIP': 0, 'FAIL': 0, 'ERROR': 0}
done = 0

def worker_task(args):
    worker_idx, pid = args
    s, cat_tok = sessions[worker_idx % WORKERS]
    return update_product(s, cat_tok, pid)

tasks = [(i % WORKERS, pid) for i, pid in enumerate(pids)]
start = time.time()

with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    futures = {ex.submit(worker_task, t): t[1] for t in tasks}
    for fut in as_completed(futures):
        pid, status, msg = fut.result()
        results[status] = results.get(status, 0) + 1
        done += 1
        if status != 'SKIP':
            log(f'[{done:3d}/{len(pids)}] PID {pid:4d}: {status} — {msg}')
        elif done % 50 == 0:
            log(f'[{done:3d}/{len(pids)}] ... {results["SKIP"]} skipped (already type=0) ...')

elapsed = time.time() - start
log(f'\nDone in {elapsed:.0f}s')
log(f'  Updated (OK):  {results["OK"]}')
log(f'  Skipped:       {results["SKIP"]}')
log(f'  Failed:        {results["FAIL"]}')
log(f'  Errors:        {results.get("ERROR", 0)}')
