#!/usr/bin/env python3
"""
Remove δραματικ* from all Greek wig descriptions.
Affected: 53 (Diva), 89 (Valeria), 94 (Amphitrite Black),
          97 (Leda Black), 99 (Long Black Curly), 107 (Aphrodite Black)
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

PRODUCTS = {

    # 53 — DIVA: δραματικό, μοντέρνο → μοντέρνο, δυναμικό
    53: dict(
        desc_en=(
            "<p>The <strong>Diva Red Wig</strong> is a bold, asymmetric red bob with a sleek side part — "
            "a dramatic, fashion-forward style for those who love to stand out. The asymmetric cut adds a modern "
            "edge, making it a perfect choice for theatrical performances, cosplay, and daring fancy dress.</p>\n"
            "<p>Made in our workshop in Athens, Greece. Features a comfortable elastic base that fits head "
            "circumferences from 42 to 63 cm. Easy to wash and comb — built to last for years.</p>\n"
            "<ul>\n<li>Style: asymmetric red bob with side part</li>\n"
            "<li>Ideal for: cosplay, Halloween, theatre, diva-themed fancy dress</li>\n"
            "<li>Elastic base: fits 42–63 cm head circumference</li>\n"
            "<li>Made in Greece — custom sizes available on request</li>\n</ul>"
        ),
        desc_el=(
            "<p>Η <strong>Περούκα Ντίβα Κόκκινη</strong> είναι ένα τολμηρό, ασύμμετρο κόκκινο καρέ με "
            "χωρίστρα στο πλάι — μοντέρνο, δυναμικό στυλ για όσους αγαπούν να ξεχωρίζουν. Το ασύμμετρο "
            "κόψιμο δίνει έναν σύγχρονο χαρακτήρα, ιδανικό για θεατρικές παραστάσεις, cosplay και τολμηρές "
            "μεταμφιέσεις.</p>\n"
            "<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. Διαθέτει ελαστική βάση που εφαρμόζει σε "
            "περίμετρο κεφαλής από 42 έως 63 εκ. Πλένεται και χτενίζεται εύκολα — φτιαγμένη για να αντέχει χρόνια.</p>\n"
            "<ul>\n<li>Στυλ: ασύμμετρο κόκκινο καρέ με χωρίστρα στο πλάι</li>\n"
            "<li>Κατάλληλη για: cosplay, Halloween, θέατρο, diva-themed μεταμφιέσεις</li>\n"
            "<li>Ελαστική βάση: εφαρμόζει σε περίμετρο κεφαλής 42–63 εκ.</li>\n"
            "<li>Κατασκευάζεται στην Ελλάδα — διαθέσιμη κατά παραγγελία σε ειδικά μεγέθη</li>\n</ul>"
        ),
        short_en="<p>Red asymmetric bob wig with side part — Diva. Bold and dynamic. Handmade in Greece. Elastic base, fits all.</p>",
        short_el="<p>Κόκκινη ασύμμετρη καρέ περούκα με χωρίστρα στο πλάι — Ντίβα. Φτιάχνεται στην Ελλάδα. Ελαστική βάση.</p>",
        meta_en="Diva Red Asymmetric Bob Wig Side Part | Handmade in Greece | Alegro Athens",
        meta_el="Ντίβα Κόκκινη Ασύμμετρη Καρέ Περούκα Πλάι | Alegro Αθήνα",
    ),

    # 89 — VALERIA: δραματικό, τολμηρό → τολμηρό, δυναμικό
    89: dict(
        desc_en=(
            "<p>The <strong>Valeria Wig</strong> is a long, straight wig in platinum blonde with bold black streaks — "
            "a striking contrast that gives a dramatic, fashion-forward look. A single style with an unmistakable personality, "
            "perfect for cosplay, Halloween, and any occasion where you want to make a strong impression.</p>\n"
            "<p>Made in our workshop in Athens, Greece. Features a comfortable elastic base that fits head circumferences from 42 to 63 cm. Easy to wash and comb — built to last for years.</p>\n"
            "<ul>\n<li>Style: long straight hair, platinum blonde with black streaks</li>\n"
            "<li>Ideal for: cosplay, Halloween, carnival, fantasy costume</li>\n"
            "<li>Elastic base: fits 42–63 cm head circumference</li>\n"
            "<li>Made in Greece — custom sizes available on request</li>\n</ul>"
        ),
        desc_el=(
            "<p>Η <strong>Περούκα Βαλέρια</strong> είναι μια μακριά, ίσια περούκα σε πλατινέ ξανθό με έντονες μαύρες ανταύγειες — "
            "εντυπωσιακή αντίθεση που δίνει τολμηρό, δυναμικό αποτέλεσμα. Μοναδικό στυλ με ξεχωριστή προσωπικότητα, "
            "ιδανικό για cosplay, Halloween και κάθε στιγμή που θέλετε να τραβήξετε όλα τα βλέμματα.</p>\n"
            "<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. Διαθέτει ελαστική βάση που εφαρμόζει σε περίμετρο κεφαλής από 42 έως 63 εκ. Πλένεται και χτενίζεται εύκολα — φτιαγμένη για να αντέχει χρόνια.</p>\n"
            "<ul>\n<li>Στυλ: μακριά ίσια, πλατινέ ξανθή με μαύρες ανταύγειες</li>\n"
            "<li>Κατάλληλη για: cosplay, Halloween, απόκριες, φαντασιακή στολή</li>\n"
            "<li>Ελαστική βάση: εφαρμόζει σε περίμετρο κεφαλής 42–63 εκ.</li>\n"
            "<li>Κατασκευάζεται στην Ελλάδα — διαθέσιμη κατά παραγγελία σε ειδικά μεγέθη</li>\n</ul>"
        ),
        short_en="<p>Long straight wig in platinum blonde with black streaks — Valeria. Bold contrast. Handmade in Greece. Elastic base.</p>",
        short_el="<p>Μακριά ίσια περούκα πλατινέ ξανθή με μαύρες ανταύγειες — Βαλέρια. Φτιάχνεται στην Ελλάδα. Ελαστική βάση.</p>",
        meta_en="Valeria Platinum Blonde Black Streaks Long Wig | Handmade in Greece | Alegro Athens",
        meta_el="Βαλέρια Πλατινέ Ξανθιά Μαύρες Ανταύγειες Μακριά Περούκα | Alegro Αθήνα",
    ),

    # 94 — AMPHITRITE BLACK: κομψή και δραματική → κομψή και εντυπωσιακή
    94: dict(
        desc_en=(
            "<p>The <strong>Amphitrite Black Wig</strong> is a long, straight black wig reaching to the waist — "
            "elegant and striking. A great choice for cosplay, Halloween, carnival, and theatrical performances.</p>\n"
            "<p>Made in our workshop in Athens, Greece. Features a comfortable elastic base that fits head circumferences from 42 to 63 cm. Easy to wash and comb — built to last for years.</p>\n"
            "<ul>\n<li>Style: long straight black wig, waist-length</li>\n"
            "<li>Ideal for: cosplay, Halloween, carnival, theatre</li>\n"
            "<li>Elastic base: fits 42–63 cm head circumference</li>\n"
            "<li>Made in Greece — custom sizes available on request</li>\n</ul>"
        ),
        desc_el=(
            "<p>Η <strong>Περούκα Αμφιτρίτη Μαύρη</strong> είναι μια μακριά, ίσια μαύρη περούκα ως τη μέση — "
            "κομψή και εντυπωσιακή. Ιδανική για cosplay, Halloween, αποκριές και θεατρικές παραστάσεις.</p>\n"
            "<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. Διαθέτει ελαστική βάση που εφαρμόζει σε περίμετρο κεφαλής από 42 έως 63 εκ. Πλένεται και χτενίζεται εύκολα — φτιαγμένη για να αντέχει χρόνια.</p>\n"
            "<ul>\n<li>Στυλ: μακριά ίσια μαύρη περούκα ως τη μέση</li>\n"
            "<li>Κατάλληλη για: cosplay, Halloween, αποκριές, θέατρο</li>\n"
            "<li>Ελαστική βάση: εφαρμόζει σε περίμετρο κεφαλής 42–63 εκ.</li>\n"
            "<li>Κατασκευάζεται στην Ελλάδα — διαθέσιμη κατά παραγγελία σε ειδικά μεγέθη</li>\n</ul>"
        ),
        short_en="<p>Long straight black wig, waist-length — Amphitrite. Handmade in Greece. Elastic base, fits all.</p>",
        short_el="<p>Μακριά ίσια μαύρη περούκα ως τη μέση — Αμφιτρίτη. Φτιάχνεται στην Ελλάδα. Ελαστική βάση.</p>",
        meta_en="Amphitrite Black Long Straight Wig Waist-Length | Handmade in Greece | Alegro Athens",
        meta_el="Αμφιτρίτη Μαύρη Μακριά Ίσια Περούκα ως τη Μέση | Alegro Αθήνα",
    ),

    # 97 — LEDA BLACK: κομψή και δραματική → κομψή και εντυπωσιακή (desc + bullet + short)
    97: dict(
        desc_en=(
            "<p>The <strong>Leda Black Wig</strong> is a long, flowing black wig — "
            "elegant and striking. A wonderful choice for cosplay, Halloween, carnival, and theatrical performances.</p>\n"
            "<p>Made in our workshop in Athens, Greece. Features a comfortable elastic base that fits head circumferences from 42 to 63 cm. Easy to wash and comb — built to last for years.</p>\n"
            "<ul>\n<li>Style: long black wig — elegant and striking</li>\n"
            "<li>Ideal for: cosplay, Halloween, carnival, theatre</li>\n"
            "<li>Elastic base: fits 42–63 cm head circumference</li>\n"
            "<li>Made in Greece — custom sizes available on request</li>\n</ul>"
        ),
        desc_el=(
            "<p>Η <strong>Περούκα Λήδα Μαύρη</strong> είναι μια μακριά μαύρη περούκα — "
            "κομψή και εντυπωσιακή. Υπέροχη επιλογή για cosplay, Halloween, αποκριές και θεατρικές παραστάσεις.</p>\n"
            "<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. Διαθέτει ελαστική βάση που εφαρμόζει σε περίμετρο κεφαλής από 42 έως 63 εκ. Πλένεται και χτενίζεται εύκολα — φτιαγμένη για να αντέχει χρόνια.</p>\n"
            "<ul>\n<li>Στυλ: μακριά μαύρη περούκα — κομψή και εντυπωσιακή</li>\n"
            "<li>Κατάλληλη για: cosplay, Halloween, αποκριές, θέατρο</li>\n"
            "<li>Ελαστική βάση: εφαρμόζει σε περίμετρο κεφαλής 42–63 εκ.</li>\n"
            "<li>Κατασκευάζεται στην Ελλάδα — διαθέσιμη κατά παραγγελία σε ειδικά μεγέθη</li>\n</ul>"
        ),
        short_en="<p>Long black wig — Leda. Elegant and striking. Handmade in Greece. Elastic base, fits all.</p>",
        short_el="<p>Μακριά μαύρη περούκα — Λήδα. Κομψή και εντυπωσιακή. Φτιάχνεται στην Ελλάδα. Ελαστική βάση.</p>",
        meta_en="Leda Black Long Wig | Handmade in Greece | Alegro Athens",
        meta_el="Λήδα Μαύρη Μακριά Περούκα | Alegro Αθήνα",
    ),

    # 99 — LONG BLACK CURLY: τολμηρό, δραματικό → τολμηρό, εντυπωσιακό
    99: dict(
        desc_en=(
            "<p>The <strong>Long Black Curly Wig</strong> is a full, voluminous wig with long, loose curls in deep black — "
            "a bold, striking style that makes an immediate impression. "
            "An excellent choice for cosplay, Halloween, carnival, theatrical performances, and any occasion calling for abundant, curly hair.</p>\n"
            "<p>Made in our workshop in Athens, Greece. Features a comfortable elastic base that fits head circumferences from 42 to 63 cm. Easy to wear — built to last for years.</p>\n"
            "<ul>\n<li>Style: long loose curls — deep black</li>\n"
            "<li>Ideal for: cosplay, Halloween, carnival, theatre, fantasy costume</li>\n"
            "<li>Elastic base: fits 42–63 cm head circumference</li>\n"
            "<li>Made in Greece — custom sizes available on request</li>\n</ul>"
        ),
        desc_el=(
            "<p>Η <strong>Μακριά Μαύρη Σγουρή Περούκα</strong> είναι μια πλούσια, ογκώδης περούκα με μακριές, ελεύθερες μπούκλες σε βαθύ μαύρο — "
            "τολμηρό, εντυπωσιακό στυλ που τραβάει αμέσως το βλέμμα. "
            "Εξαιρετική επιλογή για cosplay, Halloween, αποκριές, θεατρικές παραστάσεις και κάθε στιγμή που θέλετε πλούσια, σγουρά μαλλιά.</p>\n"
            "<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. Διαθέτει ελαστική βάση που εφαρμόζει σε περίμετρο κεφαλής από 42 έως 63 εκ. Εύκολη στη χρήση — φτιαγμένη για να αντέχει χρόνια.</p>\n"
            "<ul>\n<li>Στυλ: μακριές ελεύθερες μπούκλες — βαθύ μαύρο</li>\n"
            "<li>Κατάλληλη για: cosplay, Halloween, αποκριές, θέατρο, φαντασιακή στολή</li>\n"
            "<li>Ελαστική βάση: εφαρμόζει σε περίμετρο κεφαλής 42–63 εκ.</li>\n"
            "<li>Κατασκευάζεται στην Ελλάδα — διαθέσιμη κατά παραγγελία σε ειδικά μεγέθη</li>\n</ul>"
        ),
        short_en="<p>Long black curly wig. Full, voluminous style. Handmade in Greece. Elastic base, fits all.</p>",
        short_el="<p>Μακριά μαύρη σγουρή περούκα. Πλούσιο, ογκώδες στυλ. Φτιάχνεται στην Ελλάδα. Ελαστική βάση.</p>",
        meta_en="Long Black Curly Wig | Handmade in Greece | Alegro Athens",
        meta_el="Μακριά Μαύρη Σγουρή Περούκα | Alegro Αθήνα",
    ),

    # 107 — APHRODITE BLACK: διαχρονικό, δραματικό μαύρο → διαχρονικό, βαθύ μαύρο
    107: dict(
        desc_en=(
            "<p>The <strong>Aphrodite Black Wig</strong> is a long, straight black wig with a sweeping side part — "
            "inspired by Aphrodite, the Greek goddess of love and beauty, rendered here in timeless, deep black. "
            "Elegant and striking, it suits mythology cosplay, fancy dress, Halloween, and theatrical performances.</p>\n"
            "<p>Made in our workshop in Athens, Greece. Features a comfortable elastic base that fits head circumferences from 42 to 63 cm. Easy to wash and comb — built to last for years.</p>\n"
            "<ul>\n<li>Style: long straight black hair with side part</li>\n"
            "<li>Ideal for: mythology cosplay, Halloween, carnival, theatre, fantasy costume</li>\n"
            "<li>Elastic base: fits 42–63 cm head circumference</li>\n"
            "<li>Made in Greece — custom sizes available on request</li>\n</ul>"
        ),
        desc_el=(
            "<p>Η <strong>Περούκα Αφροδίτη Μαύρη</strong> είναι μια μακριά, ίσια μαύρη περούκα με χωρίστρα στο πλάι — "
            "εμπνευσμένη από την Αφροδίτη, τη θεά της αγάπης και της ομορφιάς, εδώ σε διαχρονικό, βαθύ μαύρο. "
            "Κομψή και εντυπωσιακή, ταιριάζει σε μυθολογικές μεταμφιέσεις, Halloween, αποκριές και θεατρικές παραστάσεις.</p>\n"
            "<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. Διαθέτει ελαστική βάση που εφαρμόζει σε περίμετρο κεφαλής από 42 έως 63 εκ. Πλένεται και χτενίζεται εύκολα — φτιαγμένη για να αντέχει χρόνια.</p>\n"
            "<ul>\n<li>Στυλ: μακριά ίσια μαύρη με χωρίστρα στο πλάι</li>\n"
            "<li>Κατάλληλη για: μυθολογικό cosplay, Halloween, αποκριές, θέατρο, φαντασιακή στολή</li>\n"
            "<li>Ελαστική βάση: εφαρμόζει σε περίμετρο κεφαλής 42–63 εκ.</li>\n"
            "<li>Κατασκευάζεται στην Ελλάδα — διαθέσιμη κατά παραγγελία σε ειδικά μεγέθη</li>\n</ul>"
        ),
        short_en="<p>Long straight black wig with side part — Aphrodite. Handmade in Greece. Elastic base, fits all.</p>",
        short_el="<p>Μακριά ίσια μαύρη περούκα με χωρίστρα στο πλάι — Αφροδίτη. Φτιάχνεται στην Ελλάδα. Ελαστική βάση.</p>",
        meta_en="Aphrodite Black Long Wig Side Part | Handmade in Greece | Alegro Athens",
        meta_el="Αφροδίτη Μαύρη Μακριά Περούκα | Alegro Αθήνα",
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
log(f'Fixing δραματικ* in {len(PRODUCTS)} products.\n')

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

log(f'\nDone — {ok} fixed, {fail} failed')
