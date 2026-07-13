"""
Fetches EVERY real product in the catalog (not just thin/flagged ones) and
builds all_products_state.json — same shape as review_state.json, so the
same generate_batch_file.py / apply_batch_file.py / upload_reviewed_descriptions.py
scripts work on it unchanged (just point STATE_FILE at this file).

Products already fixed in the previous priority batch (tracked in
review_state.json as 'done') are carried over as 'done' here too, so they
don't get re-opened for editing.

Usage:
    python fetch_all_products.py
"""
import truststore
truststore.inject_into_ssl()

import requests, re, sys, json, html as html_mod
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

sys.stdout.reconfigure(encoding='utf-8')

ADMIN  = 'https://alegro.gr/admin875fdclzkf27m3shsg9'
PASSWD = 'cultivatesandspreadslove13579' + chr(33)
EMAIL  = 'damoncollective@gmail.com'
WORKERS = 4
PID_RANGE = range(1, 450)

PREVIOUS_STATE = r'C:\Users\Damon\Desktop\review_state.json'
OUTPUT = r'C:\Users\Damon\Desktop\all_products_state.json'

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
    legacy = m.group(1) if m else ''
    r2 = s.get(ADMIN + '/index.php',
               params={'controller': 'AdminProducts', 'token': legacy},
               allow_redirects=True)
    cat_tok = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r2.url).group(1)
    return s, cat_tok

def get_textarea(html, name):
    m = re.search(
        r'<textarea[^>]+name="' + re.escape(name) + r'"[^>]*>(.*?)</textarea>',
        html, re.I | re.S)
    return html_mod.unescape(m.group(1).strip()) if m else ''

def get_input(html, name):
    m = re.search(r'<input[^>]+name="' + re.escape(name) + r'"[^>]*value="([^"]*)"', html, re.I)
    if not m:
        m = re.search(r'<input[^>]+value="([^"]*)"[^>]+name="' + re.escape(name) + r'"', html, re.I)
    return html_mod.unescape(m.group(1).strip()) if m else ''

def fetch_product(s, cat_tok, pid):
    try:
        r = s.get(f'{ADMIN}/index.php/sell/catalog/products/{pid}/edit',
                  params={'_token': cat_tok}, allow_redirects=True, timeout=25)
        if r.status_code != 200:
            return pid, None, f'HTTP {r.status_code}'
        html = r.text
        if 'product[description][description][1]' not in html:
            return pid, None, 'not a product page'

        data = {'id': pid}
        for lang in ('1', '2'):
            data[f'name_{lang}']    = get_input(html,    f'product[header][name][{lang}]')
            data[f'desc_{lang}']    = get_textarea(html, f'product[description][description][{lang}]')
            data[f'short_{lang}']   = get_textarea(html, f'product[description][description_short][{lang}]')
            data[f'meta_title_{lang}'] = get_input(html, f'product[seo][meta_title][{lang}]')
            data[f'meta_desc_{lang}']  = get_textarea(html, f'product[seo][meta_description][{lang}]')
            data[f'slug_{lang}']    = get_input(html,    f'product[seo][link_rewrite][{lang}]')
        return pid, data, 'OK'
    except Exception as e:
        return pid, None, str(e)[:80]

# ── Carry over already-done PIDs from the previous priority batch ──────────
done_pids = {}
try:
    with open(PREVIOUS_STATE, encoding='utf-8') as f:
        prev = json.load(f)
    for item in prev:
        if item['status'] == 'done':
            done_pids[item['id']] = item
    log(f'Carrying over {len(done_pids)} already-done products from review_state.json')
except FileNotFoundError:
    log('No previous review_state.json found — starting fresh.')

# ── Main ─────────────────────────────────────────────────────────────────
log('Logging into admin…')
sessions = [make_session() for _ in range(WORKERS)]
pids = list(PID_RANGE)
log(f'Logged in. Scanning {len(pids)} candidate PIDs…\n')

results = {}
errors = []
done = 0

def worker(args):
    idx, pid = args
    s, cat = sessions[idx]
    return fetch_product(s, cat, pid)

tasks = [(i % WORKERS, pid) for i, pid in enumerate(pids)]
with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    futures = {ex.submit(worker, t): t[1] for t in tasks}
    for fut in as_completed(futures):
        pid, data, msg = fut.result()
        done += 1
        if data:
            results[pid] = data
        else:
            errors.append((pid, msg))
        if done % 50 == 0:
            log(f'  [{done}/{len(pids)}] fetched…')

log(f'\nFetched {len(results)} real products ({len(errors)} not products / errors).')

state = []
for pid in sorted(results.keys()):
    p = results[pid]
    if pid in done_pids:
        state.append(done_pids[pid])
        continue
    state.append({
        'id': pid,
        'name_en': p['name_1'], 'name_el': p['name_2'],
        'desc_en': p['desc_1'], 'desc_el': p['desc_2'],
        'short_en': p['short_1'], 'short_el': p['short_2'],
        'meta_title_en': p['meta_title_1'], 'meta_title_el': p['meta_title_2'],
        'meta_desc_en': p['meta_desc_1'], 'meta_desc_el': p['meta_desc_2'],
        'slug_en': p['slug_1'], 'slug_el': p['slug_2'],
        'status': 'pending',
    })

with open(OUTPUT, 'w', encoding='utf-8') as f:
    json.dump(state, f, ensure_ascii=False, indent=2)

pending_count = sum(1 for s in state if s['status'] == 'pending')
done_count = sum(1 for s in state if s['status'] == 'done')
log(f'\nSaved {len(state)} products -> {OUTPUT}')
log(f'  pending: {pending_count}   already done: {done_count}')
if errors:
    log(f'\n{len(errors)} PIDs were not real products (expected for gaps in the ID range).')
