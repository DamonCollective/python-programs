#!/usr/bin/env python3
"""
Fix Daphne (139-142): remove φουντωτή from product name fields and all description fields.
"""
import requests, re, sys, html as html_mod
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
sys.stdout.reconfigure(encoding='utf-8')

ADMIN   = 'https://alegro.gr/admin875fdclzkf27m3shsg9'
EMAIL   = 'damoncollective@gmail.com'
PASSWD  = 'cultivatesandspreadslove13579' + chr(33)
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
    'product[pricing][on_sale]',
    'product[options][visibility][visibility]',
    'product[options][visibility][online_only]',
}

PIDS = [139, 140, 141, 142]

# Corrected descriptions (no φουντωτή)
def daphne(en_color, el_fem, el_neuter):
    en = en_color.lower(); el_adj = el_fem.lower()
    return dict(
        desc_en=(
            f"<p>The <strong>Daphne {en_color} Wig</strong> is a full, voluminous curly wig — "
            f"a bold style with plenty of body and presence. Available in many colours, here in {en}. "
            f"A fun choice for cosplay, Halloween, carnival, and any occasion that calls for a striking, high-volume look.</p>\n"
            f"<p>Made in our workshop in Athens, Greece. Features a comfortable elastic base that fits head circumferences from 42 to 63 cm. Easy to wear — built to last for years.</p>\n"
            f"<ul>\n<li>Style: full curly wig — {en}</li>\n"
            f"<li>Ideal for: cosplay, Halloween, carnival, retro / vintage look, fancy dress</li>\n"
            f"<li>Elastic base: fits 42–63 cm head circumference</li>\n"
            f"<li>Made in Greece — custom sizes available on request</li>\n</ul>"
        ),
        desc_el=(
            f"<p>Η <strong>Περούκα Δάφνη {el_fem}</strong> είναι μια σγουρή περούκα με μεγάλο, πλούσιο όγκο — "
            f"τολμηρό στυλ με δυναμική παρουσία. Σε πολλά χρώματα, εδώ σε {el_neuter}. "
            f"Διασκεδαστική επιλογή για cosplay, Halloween, αποκριές και κάθε στιγμή που θέλετε εντυπωσιακή, σγουρή εμφάνιση.</p>\n"
            f"<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. Διαθέτει ελαστική βάση που εφαρμόζει σε περίμετρο κεφαλής από 42 έως 63 εκ. Εύκολη στη χρήση — φτιαγμένη για να αντέχει χρόνια.</p>\n"
            f"<ul>\n<li>Στυλ: σγουρή περούκα — {el_adj}</li>\n"
            f"<li>Κατάλληλη για: cosplay, Halloween, αποκριές, retro / vintage look, μεταμφιέσεις</li>\n"
            f"<li>Ελαστική βάση: εφαρμόζει σε περίμετρο κεφαλής 42–63 εκ.</li>\n"
            f"<li>Κατασκευάζεται στην Ελλάδα — διαθέσιμη κατά παραγγελία σε ειδικά μεγέθη</li>\n</ul>"
        ),
        short_en=f"<p>Full curly {en} wig — Daphne style. Bold, high-volume look. Handmade in Greece. Elastic base, fits all.</p>",
        short_el=f"<p>Σγουρή {el_adj} περούκα — Δάφνη. Τολμηρό, ογκώδες στυλ. Φτιάχνεται στην Ελλάδα. Ελαστική βάση.</p>",
        meta_en=f"Daphne {en_color} Curly Wig | Handmade in Greece | Alegro Athens",
        meta_el=f"Δάφνη {el_fem} Σγουρή Περούκα | Alegro Αθήνα",
    )

CONTENT = {
    139: daphne("Black",       "Μαύρη",           "μαύρο"),
    140: daphne("Blonde",      "Ξανθιά",          "ξανθό"),
    141: daphne("Red",         "Κόκκινη",         "κόκκινο"),
    142: daphne("Light Brown", "Ανοιχτή Καστανή", "ανοιχτό καστανό"),
}

print_lock = Lock()
def log(msg):
    with print_lock:
        print(msg, flush=True)

def fix_name(val):
    """Replace φουντωτ* → σγουρ* in any inflection."""
    return re.sub(r'[Φφ]ουντωτ\w*', lambda m: 'σγουρή' if m.group(0)[0].islower() else 'Σγουρή', val)

def get_textarea(html, name):
    m = re.search(r'<textarea[^>]+name="' + re.escape(name) + r'"[^>]*>(.*?)</textarea>', html, re.I | re.S)
    return html_mod.unescape(m.group(1).strip()) if m else ''

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

        # Fix φουντωτή in name fields
        for lang in ['1', '2']:
            k = f'product[details][name][{lang}]'
            if k in payload and 'ουντωτ' in payload[k]:
                old = payload[k]
                payload[k] = fix_name(old)
                log(f'  PID {pid} name[{lang}]: {old!r} → {payload[k]!r}')

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
log(f'Fixing φουντωτή in names + descriptions for {len(PIDS)} Daphne products.\n')

tasks = [(i % WORKERS, pid) for i, pid in enumerate(PIDS)]

def worker(args):
    idx, pid = args
    s, cat = sessions[idx]
    return update_product(s, cat, pid, CONTENT[pid])

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

log(f'\nDone — {ok} fixed, {fail} failed')
