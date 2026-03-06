"""
Fetch all current product descriptions from the live admin and save locally.
Output: descriptions_backup_YYYYMMDD.json
"""
import requests, re, sys, json, time, html as html_mod
from datetime import date
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
sys.stdout.reconfigure(encoding='utf-8')

ADMIN   = 'https://alegro.gr/admin875fdclzkf27m3shsg9'
PASSWD  = 'cultivatesandspreadslove13579' + chr(33)
EMAIL   = 'damoncollective@gmail.com'
WORKERS = 4
OUTPUT  = fr'C:\Users\Damon\Desktop\descriptions_backup_{date.today().strftime("%Y%m%d")}.json'

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
    """Extract and HTML-decode a named textarea's content."""
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

        # Confirm it's a product page
        if 'product[description][description][1]' not in html:
            return pid, None, 'not a product page'

        data = {
            'id': pid,
            'langs': {
                '1': {
                    'name':              get_input(html,    'product[header][name][1]'),
                    'description':       get_textarea(html, 'product[description][description][1]'),
                    'description_short': get_textarea(html, 'product[description][description_short][1]'),
                    'meta_title':        get_input(html,    'product[seo][meta_title][1]'),
                    'meta_description':  get_textarea(html, 'product[seo][meta_description][1]'),
                    'link_rewrite':      get_input(html,    'product[seo][link_rewrite][1]'),
                },
                '2': {
                    'name':              get_input(html,    'product[header][name][2]'),
                    'description':       get_textarea(html, 'product[description][description][2]'),
                    'description_short': get_textarea(html, 'product[description][description_short][2]'),
                    'meta_title':        get_input(html,    'product[seo][meta_title][2]'),
                    'meta_description':  get_textarea(html, 'product[seo][meta_description][2]'),
                    'link_rewrite':      get_input(html,    'product[seo][link_rewrite][2]'),
                },
            }
        }
        return pid, data, 'OK'
    except Exception as e:
        return pid, None, str(e)[:80]

# ── Main ──────────────────────────────────────────────────────────────────────
log('Logging in…')
s0, cat0 = make_session()

r_list = s0.get(f'{ADMIN}/index.php/sell/catalog/products/',
                params={'_token': cat0, 'products[limit]': 1000},
                allow_redirects=True)
pids = sorted(set(int(p) for p in re.findall(r'/sell/catalog/products/(\d+)/edit', r_list.text)))
log(f'Found {len(pids)} products. Fetching with {WORKERS} workers…\n')

sessions = [make_session() for _ in range(WORKERS)]
results  = {}
errors   = []
done     = 0
start    = time.time()

def worker(args):
    idx, pid = args
    s, cat = sessions[idx]
    return fetch_product(s, cat, str(pid))

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
            log(f'  [{done}/{len(pids)}] PID {pid}: {msg}')
        if done % 50 == 0:
            log(f'  [{done}/{len(pids)}] {len(results)} fetched…')

# ── Build final output ────────────────────────────────────────────────────────
ordered = {}
for pid in sorted(results.keys()):
    p = results[pid]
    ordered[str(pid)] = {
        "id": pid,
        "lang_1": {
            "lang": "en",
            "name":              p['langs']['1']['name'],
            "description":       p['langs']['1']['description'],
            "description_short": p['langs']['1']['description_short'],
            "meta_title":        p['langs']['1']['meta_title'],
            "meta_description":  p['langs']['1']['meta_description'],
            "link_rewrite":      p['langs']['1']['link_rewrite'],
        },
        "lang_2": {
            "lang": "el",
            "name":              p['langs']['2']['name'],
            "description":       p['langs']['2']['description'],
            "description_short": p['langs']['2']['description_short'],
            "meta_title":        p['langs']['2']['meta_title'],
            "meta_description":  p['langs']['2']['meta_description'],
            "link_rewrite":      p['langs']['2']['link_rewrite'],
        },
    }

with open(OUTPUT, 'w', encoding='utf-8') as f:
    json.dump(ordered, f, ensure_ascii=False, indent=2)

elapsed = time.time() - start
log(f'\nDone in {elapsed:.0f}s')
log(f'Saved {len(ordered)} products → {OUTPUT}')

has_desc = sum(1 for p in ordered.values() if p['lang_1']['description'] or p['lang_2']['description'])
no_desc  = len(ordered) - has_desc
log(f'\nWith description:    {has_desc}')
log(f'Without description: {no_desc}')
if no_desc:
    missing = [pid for pid, p in ordered.items()
               if not p['lang_1']['description'] and not p['lang_2']['description']]
    log(f'Empty PIDs: {sorted(int(x) for x in missing)}')
if errors:
    log(f'\nFailed to fetch {len(errors)} products:')
    for pid, msg in sorted(errors): log(f'  PID {pid}: {msg}')
