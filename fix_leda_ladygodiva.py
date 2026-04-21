#!/usr/bin/env python3
"""
Fix Leda (97, 98): remove mythology reference — just a name.
Fix Lady Godiva (101): τρέσες → μαλλιά.
"""
import requests, re, sys, html as html_mod
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
sys.stdout.reconfigure(encoding='utf-8')

ADMIN   = 'https://alegro.gr/admin875fdclzkf27m3shsg9'
EMAIL   = 'damoncollective@gmail.com'
PASSWD  = 'cultivatesandspreadslove13579' + chr(33)
WORKERS = 3

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

print_lock = Lock()
def log(msg):
    with print_lock:
        print(msg, flush=True)

PRODUCTS = {

    # 97 — LEDA BLACK: no mythology, just a name
    97: dict(
        desc_en=(
            "<p>The <strong>Leda Black Wig</strong> is a long, flowing black wig — "
            "elegant and dramatic. A wonderful choice for cosplay, Halloween, carnival, and theatrical performances.</p>\n"
            "<p>Made in our workshop in Athens, Greece. Features a comfortable elastic base that fits head circumferences from 42 to 63 cm. Easy to wash and comb — built to last for years.</p>\n"
            "<ul>\n<li>Style: long black wig — elegant and dramatic</li>\n"
            "<li>Ideal for: cosplay, Halloween, carnival, theatre</li>\n"
            "<li>Elastic base: fits 42–63 cm head circumference</li>\n"
            "<li>Made in Greece — custom sizes available on request</li>\n</ul>"
        ),
        desc_el=(
            "<p>Η <strong>Περούκα Λήδα Μαύρη</strong> είναι μια μακριά μαύρη περούκα — "
            "κομψή και δραματική. Υπέροχη επιλογή για cosplay, Halloween, αποκριές και θεατρικές παραστάσεις.</p>\n"
            "<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. Διαθέτει ελαστική βάση που εφαρμόζει σε περίμετρο κεφαλής από 42 έως 63 εκ. Πλένεται και χτενίζεται εύκολα — φτιαγμένη για να αντέχει χρόνια.</p>\n"
            "<ul>\n<li>Στυλ: μακριά μαύρη περούκα — κομψή και δραματική</li>\n"
            "<li>Κατάλληλη για: cosplay, Halloween, αποκριές, θέατρο</li>\n"
            "<li>Ελαστική βάση: εφαρμόζει σε περίμετρο κεφαλής 42–63 εκ.</li>\n"
            "<li>Κατασκευάζεται στην Ελλάδα — διαθέσιμη κατά παραγγελία σε ειδικά μεγέθη</li>\n</ul>"
        ),
        short_en="<p>Long black wig — Leda. Elegant and dramatic. Handmade in Greece. Elastic base, fits all.</p>",
        short_el="<p>Μακριά μαύρη περούκα — Λήδα. Κομψή και δραματική. Φτιάχνεται στην Ελλάδα. Ελαστική βάση.</p>",
        meta_en="Leda Black Long Wig | Handmade in Greece | Alegro Athens",
        meta_el="Λήδα Μαύρη Μακριά Περούκα | Alegro Αθήνα",
    ),

    # 98 — LEDA BLONDE: no mythology, just a name
    98: dict(
        desc_en=(
            "<p>The <strong>Leda Blonde Wig</strong> is a long, flowing blonde wig — "
            "luminous and graceful. A wonderful choice for cosplay, Halloween, carnival, and theatrical performances.</p>\n"
            "<p>Made in our workshop in Athens, Greece. Features a comfortable elastic base that fits head circumferences from 42 to 63 cm. Easy to wash and comb — built to last for years.</p>\n"
            "<ul>\n<li>Style: long blonde wig — luminous and graceful</li>\n"
            "<li>Ideal for: cosplay, Halloween, carnival, theatre</li>\n"
            "<li>Elastic base: fits 42–63 cm head circumference</li>\n"
            "<li>Made in Greece — custom sizes available on request</li>\n</ul>"
        ),
        desc_el=(
            "<p>Η <strong>Περούκα Λήδα Ξανθιά</strong> είναι μια μακριά ξανθιά περούκα — "
            "λαμπερή και χαριτωμένη. Υπέροχη επιλογή για cosplay, Halloween, αποκριές και θεατρικές παραστάσεις.</p>\n"
            "<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. Διαθέτει ελαστική βάση που εφαρμόζει σε περίμετρο κεφαλής από 42 έως 63 εκ. Πλένεται και χτενίζεται εύκολα — φτιαγμένη για να αντέχει χρόνια.</p>\n"
            "<ul>\n<li>Στυλ: μακριά ξανθιά περούκα — λαμπερή και χαριτωμένη</li>\n"
            "<li>Κατάλληλη για: cosplay, Halloween, αποκριές, θέατρο</li>\n"
            "<li>Ελαστική βάση: εφαρμόζει σε περίμετρο κεφαλής 42–63 εκ.</li>\n"
            "<li>Κατασκευάζεται στην Ελλάδα — διαθέσιμη κατά παραγγελία σε ειδικά μεγέθη</li>\n</ul>"
        ),
        short_en="<p>Long blonde wig — Leda. Luminous and graceful. Handmade in Greece. Elastic base, fits all.</p>",
        short_el="<p>Μακριά ξανθιά περούκα — Λήδα. Λαμπερή και χαριτωμένη. Φτιάχνεται στην Ελλάδα. Ελαστική βάση.</p>",
        meta_en="Leda Blonde Long Wig | Handmade in Greece | Alegro Athens",
        meta_el="Λήδα Ξανθιά Μακριά Περούκα | Alegro Αθήνα",
    ),

    # 101 — LADY GODIVA: τρέσες → μαλλιά
    101: dict(
        desc_en=(
            "<p>The <strong>Lady Godiva Wig</strong> is a long, abundant blonde curly wig inspired by the legendary Lady Godiva — "
            "the Anglo-Saxon noblewoman immortalised for riding through Coventry with her flowing golden hair as her only covering. "
            "Lush, romantic, and unmistakably dramatic, this wig is perfect for historical cosplay, Halloween, carnival, and theatrical performances.</p>\n"
            "<p>Made in our workshop in Athens, Greece. Features a comfortable elastic base that fits head circumferences from 42 to 63 cm. Easy to wear — built to last for years.</p>\n"
            "<ul>\n<li>Style: long abundant blonde curls — romantic and dramatic</li>\n"
            "<li>Ideal for: historical cosplay, Halloween, carnival, theatre</li>\n"
            "<li>Elastic base: fits 42–63 cm head circumference</li>\n"
            "<li>Made in Greece — custom sizes available on request</li>\n</ul>"
        ),
        desc_el=(
            "<p>Η <strong>Περούκα Λέιντι Γκοντίβα</strong> είναι μια μακριά, πλούσια ξανθιά σγουρή περούκα εμπνευσμένη από τη θρυλική Λέιντι Γκοντίβα — "
            "την Αγγλοσαξονική ευγενή που αθανατίστηκε για τον περίπατό της στο Κόβεντρι με μόνο κάλυμμα τα χρυσά μακριά μαλλιά της. "
            "Πλούσια, ρομαντική και αναμφίβολα εντυπωσιακή, ιδανική για ιστορικές μεταμφιέσεις, Halloween, αποκριές και θεατρικές παραστάσεις.</p>\n"
            "<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. Διαθέτει ελαστική βάση που εφαρμόζει σε περίμετρο κεφαλής από 42 έως 63 εκ. Εύκολη στη χρήση — φτιαγμένη για να αντέχει χρόνια.</p>\n"
            "<ul>\n<li>Στυλ: μακριές πλούσιες ξανθές μπούκλες — ρομαντικό και εντυπωσιακό</li>\n"
            "<li>Κατάλληλη για: ιστορικές μεταμφιέσεις, Halloween, αποκριές, θέατρο</li>\n"
            "<li>Ελαστική βάση: εφαρμόζει σε περίμετρο κεφαλής 42–63 εκ.</li>\n"
            "<li>Κατασκευάζεται στην Ελλάδα — διαθέσιμη κατά παραγγελία σε ειδικά μεγέθη</li>\n</ul>"
        ),
        short_en="<p>Long abundant blonde curly wig — Lady Godiva. Romantic and dramatic. Handmade in Greece. Elastic base, fits all.</p>",
        short_el="<p>Μακριά πλούσια ξανθιά σγουρή περούκα — Λέιντι Γκοντίβα. Ρομαντική και εντυπωσιακή. Φτιάχνεται στην Ελλάδα.</p>",
        meta_en="Lady Godiva Long Blonde Curly Wig | Handmade in Greece | Alegro Athens",
        meta_el="Λέιντι Γκοντίβα Μακριά Ξανθιά Σγουρή Περούκα | Alegro Αθήνα",
    ),
}

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

def update_product(s, cat_tok, pid, content):
    try:
        r_edit = s.get(f'{ADMIN}/index.php/sell/catalog/products/{pid}/edit',
                       params={'_token': cat_tok}, allow_redirects=True, timeout=30)
        m = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r_edit.url)
        if not m:
            return pid, 'SKIP', 'no edit token'
        edit_tok = m.group(1)
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

        payload = {k: html_mod.unescape(v) for k, v in all_inputs.items() if k not in EXCLUDE}
        payload['product[details][features][feature_id]']        = '0'
        payload['product[options][visibility][visibility]']      = 'both'
        payload['product[options][visibility][online_only]']     = '0'
        payload['product[shipping][delivery_time_note_type]']    = '1'

        payload['product[description][description][1]']       = content['desc_en']
        payload['product[description][description][2]']       = content['desc_el']
        payload['product[description][description_short][1]'] = content['short_en']
        payload['product[description][description_short][2]'] = content['short_el']
        payload['product[seo][meta_description][1]']          = content['meta_en']
        payload['product[seo][meta_description][2]']          = content['meta_el']

        invalid = re.compile(r'[<>;=#{}\\[\]]')
        for k in list(payload.keys()):
            if 'name][' in k and invalid.search(payload[k]):
                payload[k] = invalid.sub('', payload[k]).strip()

        payload['_token'] = edit_tok

        r_save = s.post(
            f'{ADMIN}/index.php/sell/catalog/products/{pid}/edit',
            params={'_token': edit_tok},
            data=payload,
            headers={'Referer': r_edit.url},
            allow_redirects=True,
            timeout=30,
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

log('Logging in…')
sessions = [make_session() for _ in range(WORKERS)]
log(f'Correcting {len(PRODUCTS)} products.\n')

pids = sorted(PRODUCTS.keys())
tasks = [(i % WORKERS, pid) for i, pid in enumerate(pids)]

def worker(args):
    idx, pid = args
    s, cat = sessions[idx]
    return update_product(s, cat, pid, PRODUCTS[pid])

ok = fail = 0
with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    futures = {ex.submit(worker, t): t[1] for t in tasks}
    for fut in as_completed(futures):
        pid, status, msg = fut.result()
        if status == 'OK':
            ok += 1
            log(f'PID {pid}: OK')
        else:
            fail += 1
            log(f'PID {pid}: {status} — {msg}')

log(f'\nDone — {ok} corrected, {fail} failed')
