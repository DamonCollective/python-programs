"""
Step 1 of the description-review pipeline.

Audits every product in the catalog and checks its current EN/EL
description content via the admin. Flags any product whose Greek (or
English) description is missing or "thin" (empty, or just a copy of the
product name). Storefront category tags are unreliable for scoping this
(e.g. costume wigs like Wilma Flintstone are tagged "Women's/Halloween",
not "Theatrical"), so this scans the whole catalog and sorts the flagged
ones with likely costume/character products first.

Output: priority_queue.json — list of products needing review, each with
its current EN/EL name, description, and short description.

Usage:
    python fetch_priority_products.py
"""
import truststore
truststore.inject_into_ssl()

import requests, re, sys, json, html as html_mod
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

sys.stdout.reconfigure(encoding='utf-8')

BASE   = 'https://alegro.gr'
ADMIN  = 'https://alegro.gr/admin875fdclzkf27m3shsg9'
PASSWD = 'cultivatesandspreadslove13579' + chr(33)
EMAIL  = 'damoncollective@gmail.com'
WORKERS = 4

OUTPUT = r'C:\Users\Damon\Desktop\priority_queue.json'

print_lock = Lock()
def log(msg):
    with print_lock:
        print(msg, flush=True)

# Keywords suggesting a costume/character/theatrical wig, used only to sort
# the flagged queue so the highest-value fixes come first (not to exclude
# anything else that's flagged).
COSTUME_KEYWORDS = [
    'cosplay', 'theatr', 'θεατρ', 'costume', 'μεταμφί', 'απόκρι', 'carnival',
    'halloween', 'wizard', 'μάγο', 'santa', 'άγιο', 'βασίλ', 'clown', 'κλόουν',
    'pirate', 'πειρατ', 'king', 'βασιλιά', 'queen', 'βασίλισσ', 'historical',
    'ιστορικ', 'hero', 'ήρω', '1821', 'gandalf', 'flintstone', 'πρωτογον',
]

def looks_costume_related(name_en, name_el):
    text = (name_en + ' ' + name_el).lower()
    return any(kw in text for kw in COSTUME_KEYWORDS)

# ── Admin login (same pattern as backup_descriptions.py) ────────────────────
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

def strip_tags(s):
    return re.sub(r'<[^>]+>', '', s).strip()

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

def is_thin(desc, short, name):
    """A description counts as 'thin' if it's empty, or its stripped text
    is basically just the product name with no extra content."""
    d_text = strip_tags(desc)
    s_text = strip_tags(short)
    combined = (d_text + ' ' + s_text).strip()
    if len(combined) < 15:
        return True
    if combined.strip().lower() == name.strip().lower():
        return True
    if len(combined) < len(name) + 20 and name.lower() in combined.lower():
        return True
    return False

# ── Main ──────────────────────────────────────────────────────────────────
# The admin's product LIST page persists filter/pagination state server-side
# per employee, which caused inconsistent (tiny) results under concurrent
# sessions here. Brute-forcing the known PID range against the edit endpoint
# directly is more reliable — fetch_product() already skips non-product IDs.
PID_RANGE = range(1, 450)

log('Logging into admin…')
sessions = [make_session() for _ in range(WORKERS)]
pids = list(PID_RANGE)
log(f'Logged in. Scanning {len(pids)} candidate PIDs and fetching current descriptions…\n')

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
        if done % 25 == 0:
            log(f'  [{done}/{len(pids)}] fetched…')

log(f'\nFetched {len(results)}/{len(pids)} candidate PIDs ({len(errors)} not products / errors).')

# ── Flag thin/missing descriptions ──────────────────────────────────────────
queue = []
for pid in sorted(results.keys()):
    p = results[pid]
    thin_en = is_thin(p['desc_1'], p['short_1'], p['name_1'])
    thin_el = is_thin(p['desc_2'], p['short_2'], p['name_2'])
    if thin_en or thin_el:
        costume = looks_costume_related(p['name_1'], p['name_2'])
        queue.append({
            'id': pid,
            'costume_related': costume,
            'name_en': p['name_1'], 'name_el': p['name_2'],
            'desc_en': p['desc_1'], 'desc_el': p['desc_2'],
            'short_en': p['short_1'], 'short_el': p['short_2'],
            'meta_title_en': p['meta_title_1'], 'meta_title_el': p['meta_title_2'],
            'meta_desc_en': p['meta_desc_1'], 'meta_desc_el': p['meta_desc_2'],
            'slug_en': p['slug_1'], 'slug_el': p['slug_2'],
            'thin_en': thin_en, 'thin_el': thin_el,
        })

# Costume/character-related products first (highest SEO+sales value), then
# the rest, each group sorted by PID.
queue.sort(key=lambda q: (not q['costume_related'], q['id']))

with open(OUTPUT, 'w', encoding='utf-8') as f:
    json.dump(queue, f, ensure_ascii=False, indent=2)

log(f'\n{"="*60}')
log(f'Products needing review: {len(queue)} (of {len(results)} total in catalog)')
log(f'  - costume/character-related: {sum(1 for q in queue if q["costume_related"])}')
log(f'  - other:                     {sum(1 for q in queue if not q["costume_related"])}')
log(f'  - thin/missing EL only: {sum(1 for q in queue if q["thin_el"] and not q["thin_en"])}')
log(f'  - thin/missing EN only: {sum(1 for q in queue if q["thin_en"] and not q["thin_el"])}')
log(f'  - thin/missing both:    {sum(1 for q in queue if q["thin_en"] and q["thin_el"])}')
log(f'\nSaved -> {OUTPUT}')
if errors:
    log(f'\n{len(errors)} products failed to fetch:')
    for pid, msg in errors[:20]:
        log(f'  PID {pid}: {msg}')
