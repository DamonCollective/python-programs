#!/usr/bin/env python3
"""
Correct all 15 Sylvia descriptions: ίσια (not λεία), PID 73 unisex.
Force-updates even if description already exists.
"""
import requests, re, sys, html as html_mod
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

print_lock = Lock()
def log(msg):
    with print_lock:
        print(msg, flush=True)


def sylvia(en_color, el_fem, el_neuter):
    en = en_color.lower()
    el_adj = el_fem.lower()
    return dict(
        desc_en=(
            f"<p>The <strong>Sylvia {en_color} Wig</strong> is a long, straight wig with a clean center part — "
            f"a timeless, romantic style with a natural-looking flow. Available in many colours, here in {en}. "
            f"A versatile choice for cosplay, fancy dress, Halloween, carnival, and any occasion that calls for long, beautiful hair.</p>\n"
            f"<p>Made in our workshop in Athens, Greece. Features a comfortable elastic base that fits head "
            f"circumferences from 42 to 63 cm. Easy to wash and comb — built to last for years.</p>\n"
            f"<ul>\n"
            f"<li>Style: long straight hair with center part — {en}</li>\n"
            f"<li>Ideal for: cosplay, Halloween, carnival, retro / vintage look, fantasy costume</li>\n"
            f"<li>Elastic base: fits 42–63 cm head circumference</li>\n"
            f"<li>Made in Greece — custom sizes available on request</li>\n"
            f"</ul>"
        ),
        desc_el=(
            f"<p>Η <strong>Περούκα Σύλβια {el_fem}</strong> είναι μια μακριά, ίσια περούκα με χωρίστρα στη μέση — "
            f"διαχρονικό, ρομαντικό στυλ με φυσικό αποτέλεσμα. Σε πολλά χρώματα, εδώ σε {el_neuter}. "
            f"Ευέλικτη επιλογή για cosplay, μεταμφιέσεις, απόκριες, Halloween και κάθε στιγμή που θέλετε πλούσια, μακριά μαλλιά.</p>\n"
            f"<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. Διαθέτει ελαστική βάση που εφαρμόζει σε "
            f"περίμετρο κεφαλής από 42 έως 63 εκ. Πλένεται και χτενίζεται εύκολα — φτιαγμένη για να αντέχει χρόνια.</p>\n"
            f"<ul>\n"
            f"<li>Στυλ: μακριά ίσια με χωρίστρα στη μέση — {el_adj}</li>\n"
            f"<li>Κατάλληλη για: cosplay, Halloween, απόκριες, retro / vintage look, φαντασιακή στολή</li>\n"
            f"<li>Ελαστική βάση: εφαρμόζει σε περίμετρο κεφαλής 42–63 εκ.</li>\n"
            f"<li>Κατασκευάζεται στην Ελλάδα — διαθέσιμη κατά παραγγελία σε ειδικά μεγέθη</li>\n"
            f"</ul>"
        ),
        short_en=f"<p>Long straight {en} wig with center part — Sylvia style. Handmade in Greece. Elastic base, fits all.</p>",
        short_el=f"<p>Μακριά ίσια {el_adj} περούκα με χωρίστρα στη μέση — Σύλβια. Φτιάχνεται στην Ελλάδα. Ελαστική βάση.</p>",
        meta_en=f"Sylvia {en_color} Long Straight Wig Center Part | Handmade in Greece | Alegro Athens",
        meta_el=f"Σύλβια {el_fem} Μακριά Ίσια Περούκα Χωρίστρα Μέση | Alegro Αθήνα",
    )


PRODUCTS = {
    73: dict(
        desc_en=(
            "<p>The <strong>Sylvia Black Wig</strong> is a long, straight black wig with a clean center part — "
            "a timeless, versatile style that works beautifully for both men and women. Available in many colours, here in black. "
            "A great choice for cosplay, fancy dress, Halloween, carnival, and any occasion that calls for long, dramatic hair.</p>\n"
            "<p>Made in our workshop in Athens, Greece. Features a comfortable elastic base that fits head "
            "circumferences from 42 to 63 cm. Easy to wash and comb — built to last for years.</p>\n"
            "<ul>\n"
            "<li>Style: long straight black hair with center part — unisex</li>\n"
            "<li>Ideal for: cosplay, Halloween, carnival, retro / vintage look, fantasy costume</li>\n"
            "<li>Elastic base: fits 42–63 cm head circumference</li>\n"
            "<li>Made in Greece — custom sizes available on request</li>\n"
            "</ul>"
        ),
        desc_el=(
            "<p>Η <strong>Περούκα Σύλβια Μαύρη</strong> είναι μια μακριά, ίσια μαύρη περούκα με χωρίστρα στη μέση — "
            "διαχρονικό, ευέλικτο στυλ που ταιριάζει εξίσου σε άντρες και γυναίκες. Σε πολλά χρώματα, εδώ σε μαύρο. "
            "Ιδανική επιλογή για cosplay, μεταμφιέσεις, απόκριες, Halloween και κάθε στιγμή που θέλετε πλούσια, μακριά μαλλιά.</p>\n"
            "<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. Διαθέτει ελαστική βάση που εφαρμόζει σε "
            "περίμετρο κεφαλής από 42 έως 63 εκ. Πλένεται και χτενίζεται εύκολα — φτιαγμένη για να αντέχει χρόνια.</p>\n"
            "<ul>\n"
            "<li>Στυλ: μακριά ίσια μαύρη με χωρίστρα στη μέση — unisex</li>\n"
            "<li>Κατάλληλη για: cosplay, Halloween, απόκριες, retro / vintage look, φαντασιακή στολή</li>\n"
            "<li>Ελαστική βάση: εφαρμόζει σε περίμετρο κεφαλής 42–63 εκ.</li>\n"
            "<li>Κατασκευάζεται στην Ελλάδα — διαθέσιμη κατά παραγγελία σε ειδικά μεγέθη</li>\n"
            "</ul>"
        ),
        short_en="<p>Long straight black wig with center part — Sylvia. Unisex. Handmade in Greece. Elastic base, fits all.</p>",
        short_el="<p>Μακριά ίσια μαύρη περούκα με χωρίστρα στη μέση — Σύλβια. Unisex. Φτιάχνεται στην Ελλάδα. Ελαστική βάση.</p>",
        meta_en="Sylvia Black Long Straight Wig Center Part Unisex | Handmade in Greece | Alegro Athens",
        meta_el="Σύλβια Μαύρη Μακριά Ίσια Περούκα Unisex | Alegro Αθήνα",
    ),
    74: sylvia("Blonde",              "Ξανθιά",                "ξανθό"),
    75: sylvia("Auburn",              "Καστανοκόκκινη",        "καστανοκόκκινο"),
    76: sylvia("Light Brown",         "Ανοιχτή Καστανή",       "ανοιχτό καστανό"),
    77: sylvia("Brown",               "Καστανή",               "καστανό"),
    78: sylvia("Platinum Blonde",     "Πλατινέ Ξανθιά",        "πλατινέ ξανθό"),
    79: sylvia("Red",                 "Κόκκινη",               "κόκκινο"),
    80: sylvia("Blue",                "Μπλε",                  "μπλε"),
    81: sylvia("Yellow",              "Κίτρινη",               "κίτρινο"),
    82: sylvia("Purple",              "Μωβ",                   "μωβ"),
    83: sylvia("Light Blue",          "Γαλάζια",               "γαλάζιο"),
    84: sylvia("Pink",                "Ροζ",                   "ροζ"),
    85: sylvia("Fuchsia",             "Φούξια",                "φούξια"),
    86: sylvia("Brown with Streaks",  "Καστανή με Ανταύγειες", "καστανό με ανταύγειες"),
    87: sylvia("Purple with Streaks", "Μωβ με Ανταύγειες",     "μωβ με ανταύγειες"),
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
log(f'All {WORKERS} sessions ready. Correcting {len(PRODUCTS)} Sylvia products.\n')

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
