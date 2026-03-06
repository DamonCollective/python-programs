"""
Restore product descriptions from the July 2025 SQL backup via admin form.
Reads description + description_short for each product/language from the backup
and submits them to the PrestaShop admin, correctly including textarea fields.
"""
import requests, re, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
sys.stdout.reconfigure(encoding='utf-8')

ADMIN   = 'https://alegro.gr/admin875fdclzkf27m3shsg9'
PASSWD  = 'cultivatesandspreadslove13579' + chr(33)
EMAIL   = 'damoncollective@gmail.com'
WORKERS = 4
BACKUP  = r'C:\Users\Damon\Desktop\ALLA\sqlqueries\1753088504-255a1d97.sql'

# ── Parse backup ─────────────────────────────────────────────────────────────
def _parse_rows(block):
    rows = []
    i = 0
    while i < len(block):
        if block[i] == '(':
            j, depth, in_str, esc = i+1, 1, False, False
            while j < len(block) and depth > 0:
                c = block[j]
                if esc: esc = False
                elif c == '\\': esc = True
                elif c == "'" and not esc: in_str = not in_str
                elif not in_str:
                    if c == '(': depth += 1
                    elif c == ')': depth -= 1
                j += 1
            rows.append(block[i:j])
            i = j
        else:
            i += 1
    return rows

def _parse_vals(row_str):
    inner = row_str.strip().strip('()')
    vals, i = [], 0
    while i < len(inner):
        while i < len(inner) and inner[i] in ' \t\n': i += 1
        if i >= len(inner): break
        if inner[i:i+4] == 'NULL':
            vals.append(None); i += 4
        elif inner[i] == "'":
            i += 1; s = []
            while i < len(inner):
                c = inner[i]
                if c == '\\' and i+1 < len(inner):
                    nc = inner[i+1]
                    s.append({'n':'\n','r':'\r','t':'\t','\\':'\\', "'":"'", '"':'"'}.get(nc, nc))
                    i += 2
                elif c == "'":
                    i += 1; break
                else:
                    s.append(c); i += 1
            vals.append(''.join(s))
        else:
            j = i
            while j < len(inner) and inner[j] != ',': j += 1
            vals.append(inner[i:j].strip()); i = j
        while i < len(inner) and inner[i] in ' \t\n,':
            if inner[i] == ',': i += 1; break
            i += 1
    return vals

print('Parsing backup…')
with open(BACKUP, encoding='utf-8', errors='replace') as f:
    content = f.read()

blocks = re.findall(r"INSERT INTO `l9n7b_product_lang` VALUES\s*\n(.*?);", content, re.S)

# descs[pid][lang] = {'desc': ..., 'short': ...}
descs = {}
for block in blocks:
    for rs in _parse_rows(block):
        v = _parse_vals(rs)
        if len(v) < 10: continue
        pid, lang = v[0], v[2]
        desc  = v[3] or ''
        short = v[4] or ''
        descs.setdefault(pid, {})[lang] = {'desc': desc, 'short': short}

print(f'Loaded descriptions for {len(descs)} products from backup.')

# ── EXCLUDE list (same safe pattern from working scripts) ────────────────────
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

INVALID_CHARS = re.compile(r'[<>;=#{}\\[\\]]')
print_lock = Lock()

def log(msg):
    with print_lock:
        print(msg, flush=True)

# ── Session factory ──────────────────────────────────────────────────────────
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
    legacy = m.group(1) if m else ''
    r2 = s.get(ADMIN + '/index.php',
               params={'controller': 'AdminProducts', 'token': legacy},
               allow_redirects=True)
    cat_tok = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r2.url).group(1)
    return s, cat_tok

# ── Per-product worker ───────────────────────────────────────────────────────
def restore_product(s, cat_tok, pid, lang_descs):
    try:
        r_edit = s.get(f'{ADMIN}/index.php/sell/catalog/products/{pid}/edit',
                       params={'_token': cat_tok}, allow_redirects=True, timeout=25)
        m = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r_edit.url)
        if not m:
            return pid, 'SKIP', 'no edit token'
        edit_tok = m.group(1)
        html = r_edit.text

        # Collect inputs
        all_inputs = {}
        for im in re.finditer(r'<input[^>]+>', html, re.I):
            tag = im.group(0)
            nm = re.search(r'\bname="([^"]+)"', tag, re.I)
            vm = re.search(r'\bvalue="([^"]*)"', tag, re.I)
            if nm:
                all_inputs[nm.group(1)] = vm.group(1) if vm else ''

        # Collect selects
        for sm in re.finditer(r'<select([^>]*)>(.*?)</select>', html, re.I | re.S):
            attrs, body = sm.group(1), sm.group(2)
            nm = re.search(r'\bname="([^"]+)"', attrs, re.I)
            if not nm or 'paginator' in nm.group(1): continue
            sel = (re.search(r'<option[^>]+selected[^>]*value="([^"]*)"', body, re.I) or
                   re.search(r'<option[^>]*value="([^"]*)"', body, re.I))
            all_inputs[nm.group(1)] = sel.group(1) if sel else ''

        payload = {k: v for k, v in all_inputs.items() if k not in EXCLUDE}
        payload['product[details][features][feature_id]']        = '0'
        payload['product[options][visibility][visibility]']      = 'both'
        payload['product[options][visibility][online_only]']     = '0'
        payload['product[shipping][delivery_time_note_type]']    = '1'

        # ── Set descriptions from backup ──────────────────────────────────
        for lang, data in lang_descs.items():
            payload[f'product[description][description][{lang}]']       = data['desc']
            payload[f'product[description][description_short][{lang}]'] = data['short']

        # Clean invalid chars in name fields
        for k in list(payload.keys()):
            if 'name][' in k and INVALID_CHARS.search(payload[k]):
                payload[k] = INVALID_CHARS.sub('', payload[k]).strip()

        payload['_token'] = edit_tok

        r_save = s.post(
            f'{ADMIN}/index.php/sell/catalog/products/{pid}/edit',
            params={'_token': edit_tok},
            data=payload,
            headers={'Referer': r_edit.url},
            allow_redirects=True,
            timeout=25,
        )
        fv = re.search(r'data-form-valid="(\d+)"', r_save.text)
        valid = fv.group(1) if fv else '?'
        if valid == '1':
            return pid, 'OK', ''
        else:
            inv = re.findall(r'name="([^"]+)"[^>]*class="[^"]*is-invalid', r_save.text, re.I)
            return pid, 'FAIL', f'inv={inv[:3]}'
    except Exception as e:
        return pid, 'ERROR', str(e)[:80]

# ── Main ─────────────────────────────────────────────────────────────────────
log('Logging in (main session)…')
s0, cat0 = make_session()

# Only process products we have descriptions for
pids = sorted(descs.keys(), key=int)
log(f'Will restore descriptions for {len(pids)} products using {WORKERS} workers.\n')

sessions = [make_session() for _ in range(WORKERS)]
log('All sessions ready.\n')

done = ok = fail = 0
start = time.time()

def worker(args):
    idx, pid = args
    s, cat = sessions[idx]
    return restore_product(s, cat, pid, descs[pid])

tasks = [(i % WORKERS, pid) for i, pid in enumerate(pids)]

with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    futures = {ex.submit(worker, t): t[1] for t in tasks}
    for fut in as_completed(futures):
        pid, status, msg = fut.result()
        done += 1
        if status == 'OK':
            ok += 1
        else:
            fail += 1
            log(f'[{done:3d}/{len(pids)}] PID {pid}: {status} — {msg}')
        if done % 25 == 0:
            log(f'[{done:3d}/{len(pids)}] {ok} restored so far…')

elapsed = time.time() - start
log(f'\nDone in {elapsed:.0f}s — {ok} restored, {fail} failed')
