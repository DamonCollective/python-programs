"""
EMERGENCY: Batch restore visibility='both' for all products.
The batch_delivery_time.py accidentally set visibility='none' (first select option, Vue-rendered).
"""
import requests, re, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
sys.stdout.reconfigure(encoding='utf-8')

ADMIN  = 'https://alegro.gr/admin875fdclzkf27m3shsg9'
PASSWD = 'cultivatesandspreadslove13579' + chr(33)
EMAIL  = 'damoncollective@gmail.com'
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
    # Exclude visibility select — we'll set it explicitly to 'both'
    'product[options][visibility][visibility]',
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

def fix_product(s, cat_token, pid):
    try:
        r_edit = s.get(f'{ADMIN}/index.php/sell/catalog/products/{pid}/edit',
                       params={'_token': cat_token}, allow_redirects=True, timeout=20)
        edit_tok_m = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r_edit.url)
        if not edit_tok_m:
            return pid, 'SKIP', 'no edit token'
        edit_tok = edit_tok_m.group(1)
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
        payload['product[options][visibility][visibility]'] = 'both'  # THE FIX
        payload['_token'] = edit_tok

        # Clean invalid chars from name fields
        for k in list(payload.keys()):
            if 'name][' in k and INVALID_CHARS.search(payload[k]):
                payload[k] = INVALID_CHARS.sub('', payload[k]).strip()

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
            return pid, 'OK', ''
        else:
            inv = re.findall(r'name="([^"]+)"[^>]*class="[^"]*is-invalid', r_save.text, re.I)
            return pid, 'FAIL', f'inv={inv[:2]}'
    except Exception as e:
        return pid, 'ERROR', str(e)[:60]

log('Logging in...')
s0, cat0 = make_session()
r_list = s0.get(f'{ADMIN}/index.php/sell/catalog/products/',
                params={'_token': cat0, 'products[limit]': 1000}, allow_redirects=True)
pids = sorted(set(int(p) for p in re.findall(r'/sell/catalog/products/(\d+)/edit', r_list.text)))
log(f'Found {len(pids)} products. Starting emergency fix with {WORKERS} workers...\n')

sessions = [make_session() for _ in range(WORKERS)]
done = ok = fail = 0
tasks = [(i % WORKERS, pid) for i, pid in enumerate(pids)]
start = time.time()

def worker_task(args):
    idx, pid = args
    s, cat = sessions[idx]
    return fix_product(s, cat, pid)

with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    futures = {ex.submit(worker_task, t): t[1] for t in tasks}
    for fut in as_completed(futures):
        pid, status, msg = fut.result()
        done += 1
        if status == 'OK':
            ok += 1
        else:
            fail += 1
            log(f'[{done:3d}/{len(pids)}] PID {pid}: {status} — {msg}')
        if done % 50 == 0 or status != 'OK':
            log(f'[{done:3d}/{len(pids)}] {ok} restored so far...')

elapsed = time.time() - start
log(f'\nDone in {elapsed:.0f}s — {ok} restored, {fail} failed')
