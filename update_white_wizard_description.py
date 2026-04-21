#!/usr/bin/env python3
"""
Write bilingual description for product 383:
  Σετ Περούκα και Γενειάδα Λευκού Μάγου / White Wizard's Wig and Beard Set
"""
import requests, re, sys, html as html_mod
sys.stdout.reconfigure(encoding='utf-8')

ADMIN  = 'https://alegro.gr/admin875fdclzkf27m3shsg9'
EMAIL  = 'damoncollective@gmail.com'
PASSWD = 'cultivatesandspreadslove13579' + chr(33)
PID    = 383

CONTENT = {
    "name_en": "White Wizard's Wig and Beard Set — Gandalf the White Style | Handmade in Greece",
    "name_el": "Σετ Περούκα και Γενειάδα Λευκού Μάγου — Γκάνταλφ ο Λευκός",

    "desc_en": (
        "<p>Command the stage with the <strong>White Wizard's Wig and Beard Set</strong> — "
        "a theatrical-quality ensemble that captures the iconic look of the great white wizard. "
        "Flowing pure-white hair and a matching long white beard combine to create a powerful, "
        "instantly recognisable fantasy character, perfect for Gandalf the White cosplay, "
        "fantasy stage productions, Halloween, and carnival events.</p>\n"
        "<p>Both the wig and the beard are handcrafted in our workshop in Greece, "
        "with over 45 years of wig-making tradition. The wig features a comfortable elastic base "
        "that fits head circumferences from 42 to 63 cm, while the beard attaches easily with "
        "the included elastic band. The set is ready to wear — no styling required.</p>\n"
        "<ul>\n"
        "<li>Contents: long white wizard wig + matching long white beard</li>\n"
        "<li>Style: flowing pure white, inspired by the classic fantasy white wizard</li>\n"
        "<li>Ideal for: Gandalf the White cosplay, Halloween, carnival, LARP, theatre, film</li>\n"
        "<li>Elastic base: fits 42–63 cm head circumference</li>\n"
        "<li>Made in Greece — custom sizes available on request</li>\n"
        "</ul>"
    ),
    "short_en": "<p>White wizard wig and beard set — Gandalf the White style. Handcrafted in Greece. Elastic base, fits all. Perfect for cosplay, carnival and theatre.</p>",

    "desc_el": (
        "<p>Εντυπωσιάστε με το <strong>Σετ Περούκα και Γενειάδα Λευκού Μάγου</strong> — "
        "ένα σύνολο θεατρικής ποιότητας που αποδίδει με πιστότητα το εμβληματικό look "
        "του μεγάλου λευκού μάγου. Η περούκα και η γενειάδα σχηματίζουν μια δυναμική, "
        "αμέσως αναγνωρίσιμη φιγούρα, ιδανική για cosplay Gandalf ο Λευκός, θεατρικές "
        "παραγωγές, Halloween και αποκριάτικες εκδηλώσεις.</p>\n"
        "<p>Τόσο η περούκα όσο και η γενειάδα φτιάχνονται στο εργαστήριό μας "
        "στην Ελλάδα, με πάνω από 45 χρόνια παράδοσης στην κατασκευή περούκων. "
        "Η περούκα διαθέτει άνετη ελαστική βάση που εφαρμόζει σε περίμετρο κεφαλής "
        "από 42 έως 63 εκ., ενώ η γενειάδα στερεώνεται εύκολα με το συνοδευτικό "
        "λαστιχάκι. Το σετ είναι έτοιμο για χρήση — δεν απαιτεί ιδιαίτερο styling.</p>\n"
        "<ul>\n"
        "<li>Περιεχόμενα: μακριά λευκή περούκα μάγου + ταιριαστή μακριά λευκή γενειάδα</li>\n"
        "<li>Στυλ: Λευκό μαλλί, άγριο, εμπνευσμένο από τον κλασικό λευκό μάγο</li>\n"
        "<li>Κατάλληλο για: cosplay Gandalf ο Λευκός, Halloween, αποκριές, LARP</li>\n"
        "<li>Ελαστική βάση: εφαρμόζει σε περίμετρο κεφαλής 42–63 εκ.</li>\n"
        "<li>Κατασκευή στην Ελλάδα — διαθέσιμη κατασκευή κατά παραγγελία σε ειδικά μεγέθη</li>\n"
        "</ul>"
    ),
    "short_el": "<p>Σετ περούκα και γενειάδα λευκού μάγου — Γκάνταλφ ο Λευκός. Ελαστική βάση, εφαρμόζει σε όλους. Ιδανικό για cosplay, αποκριές.</p>",

    "slug_en": "white-wizards-wig-and-beard-set-gandalf-cosplay",
    "slug_el": "set-perouka-geneiada-lefkou-magou-gandalf",
    "meta_en": "White Wizard's Wig and Beard Set — Gandalf the White Cosplay | Alegro Athens",
    "meta_el": "Σετ Περούκα και Γενειάδα Λευκού Μάγου — Gandalf Cosplay | Alegro Αθήνα",
}

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
r2 = s.get(ADMIN + '/index.php', params={'controller': 'AdminProducts', 'token': legacy}, allow_redirects=True)
cat_tok = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r2.url).group(1)
print('Logged in.')

print(f'Fetching edit page for PID {PID}...')
r_edit = s.get(f'{ADMIN}/index.php/sell/catalog/products/{PID}/edit',
               params={'_token': cat_tok}, allow_redirects=True, timeout=25)
edit_tok = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r_edit.url).group(1)
html = r_edit.text
print(f'  Page size: {len(html):,} bytes')

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
    if not nm or 'paginator' in nm.group(1): continue
    sel = (re.search(r'<option[^>]+selected[^>]*value="([^"]*)"', body, re.I) or
           re.search(r'<option[^>]*value="([^"]*)"', body, re.I))
    all_inputs[nm.group(1)] = sel.group(1) if sel else ''

payload = {k: html_mod.unescape(v) for k, v in all_inputs.items() if k not in EXCLUDE}

payload['product[details][features][feature_id]']        = '0'
payload['product[options][visibility][visibility]']      = 'both'
payload['product[options][visibility][online_only]']     = '0'
payload['product[shipping][delivery_time_note_type]']    = '1'

payload['product[header][name][1]'] = CONTENT['name_en']
payload['product[header][name][2]'] = CONTENT['name_el']
payload['product[description][description][1]']       = CONTENT['desc_en']
payload['product[description][description][2]']       = CONTENT['desc_el']
payload['product[description][description_short][1]'] = CONTENT['short_en']
payload['product[description][description_short][2]'] = CONTENT['short_el']
payload['product[seo][link_rewrite][1]'] = CONTENT['slug_en']
payload['product[seo][link_rewrite][2]'] = CONTENT['slug_el']
payload['product[seo][meta_title][1]']   = CONTENT['meta_en']
payload['product[seo][meta_title][2]']   = CONTENT['meta_el']
payload['_token'] = edit_tok

print('Saving...')
r_save = s.post(
    f'{ADMIN}/index.php/sell/catalog/products/{PID}/edit',
    params={'_token': edit_tok},
    data=payload,
    headers={'Referer': r_edit.url},
    allow_redirects=True, timeout=25,
)
fv = re.search(r'data-form-valid="(\d+)"', r_save.text)
valid = fv.group(1) if fv else '?'
if valid == '1':
    print(f'\n  OK — description saved successfully.')
    print(f'  View: {ADMIN}/index.php/sell/catalog/products/{PID}/edit')
else:
    inv = re.findall(r'name="([^"]+)"[^>]*class="[^"]*is-invalid', r_save.text, re.I)
    errs = re.findall(r'"message"\s*:\s*"([^"]+)"', r_save.text)
    print(f'\n  FAIL — invalid fields: {inv[:6]}')
    print(f'  Errors: {errs[:4]}')
