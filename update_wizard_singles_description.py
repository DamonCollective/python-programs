#!/usr/bin/env python3
"""
Update names and descriptions for the 4 individual wizard wig/beard products:
  194 — White Wizard's Wig
  195 — White Wizard's Beard
  196 — Gray Wizard's Wig
  197 — Gray Wizard's Beard
"""
import requests, re, sys, html as html_mod
sys.stdout.reconfigure(encoding='utf-8')

ADMIN  = 'https://alegro.gr/admin875fdclzkf27m3shsg9'
EMAIL  = 'damoncollective@gmail.com'
PASSWD = 'cultivatesandspreadslove13579' + chr(33)

PRODUCTS = {

194: {
    "name_en": "White Wizard's Long Wig — Merlin / Gandalf Style | Handmade in Greece",
    "name_el": "Περούκα Λευκού Μάγου Μακριά — Μέρλιν / Γκάνταλφ | Χειροποίητη στην Ελλάδα",
    "desc_en": (
        "<p>The <strong>White Wizard's Long Wig</strong> recreates the iconic flowing white hair "
        "of the great wizard — instantly recognisable from fantasy classics such as Gandalf the White, "
        "Merlin, and Dumbledore. Whether you are heading to a cosplay event, a Halloween party, "
        "a carnival, or a theatrical production, this wig delivers a powerful, authentic look.</p>\n"
        "<p>Handcrafted in our workshop in Greece with over 45 years of wig-making tradition. "
        "Features a comfortable elastic base that fits head circumferences from 42 to 63 cm. "
        "Ready to wear — no styling required. "
        "Can be paired with our matching <strong>White Wizard's Beard</strong> for the full wizard look.</p>\n"
        "<ul>\n"
        "<li>Style: long, flowing pure-white hair</li>\n"
        "<li>Ideal for: Gandalf the White, Merlin, Dumbledore cosplay, Halloween, carnival, LARP, theatre</li>\n"
        "<li>Elastic base: fits 42–63 cm head circumference</li>\n"
        "<li>Made in Greece — custom sizes available on request</li>\n"
        "</ul>"
    ),
    "short_en": "<p>Long white wizard wig — Gandalf / Merlin style. Handcrafted in Greece. Elastic base, fits all. Perfect for cosplay, carnival and theatre.</p>",
    "desc_el": (
        "<p>Η <strong>Περούκα Λευκού Μάγου</strong> αποδίδει τα εμβληματικά ρέουσα λευκά μαλλιά "
        "του μεγάλου μάγου — αμέσως αναγνωρίσιμα από φαντασιακά κλασικά όπως ο Γκάνταλφ ο Λευκός, "
        "ο Μέρλιν και ο Ντάμπλντορ. Ιδανική για cosplay, Halloween, αποκριές ή θεατρικές παραγωγές.</p>\n"
        "<p>Χειροποίητη στο εργαστήριό μας στην Ελλάδα με πάνω από 45 χρόνια παράδοσης. "
        "Διαθέτει ελαστική βάση που εφαρμόζει σε περίμετρο κεφαλής από 42 έως 63 εκ. "
        "Έτοιμη για χρήση — δεν απαιτεί styling. "
        "Συνδυάζεται με τη <strong>Γενειάδα Λευκού Μάγου</strong> για το πλήρες look.</p>\n"
        "<ul>\n"
        "<li>Στυλ: μακριά, ρέουσα λευκή περούκα</li>\n"
        "<li>Κατάλληλη για: Gandalf, Merlin, Dumbledore cosplay, Halloween, αποκριές, LARP, θέατρο</li>\n"
        "<li>Ελαστική βάση: εφαρμόζει σε περίμετρο κεφαλής 42–63 εκ.</li>\n"
        "<li>Κατασκευή στην Ελλάδα — διαθέσιμη κατά παραγγελία σε ειδικά μεγέθη</li>\n"
        "</ul>"
    ),
    "short_el": "<p>Μακριά λευκή περούκα μάγου — Γκάνταλφ / Μέρλιν. Χειροποίητη στην Ελλάδα. Ελαστική βάση, εφαρμόζει σε όλους.</p>",
    "slug_en": "white-wizards-long-wig-gandalf-merlin-cosplay",
    "slug_el": "perouka-lefkou-magou-gandalf-merlin",
    "meta_en": "White Wizard's Long Wig — Gandalf / Merlin Style | Alegro Athens",
    "meta_el": "Περούκα Λευκού Μάγου — Γκάνταλφ / Μέρλιν | Alegro Αθήνα",
},

195: {
    "name_en": "White Wizard's Long Beard — Merlin / Gandalf Style | Handmade in Greece",
    "name_el": "Γενειάδα Λευκού Μάγου Μακριά — Μέρλιν / Γκάνταλφ | Χειροποίητη στην Ελλάδα",
    "desc_en": (
        "<p>The <strong>White Wizard's Long Beard</strong> completes the iconic look of the great "
        "white wizard — long, flowing, and pure white. Perfect on its own or paired with our "
        "matching White Wizard's Wig for the full Gandalf the White, Merlin, or Dumbledore costume.</p>\n"
        "<p>Handcrafted in our workshop in Greece with over 45 years of wig-making tradition. "
        "Attaches easily with the included elastic band — no glue required. "
        "Ready to wear straight out of the box.</p>\n"
        "<ul>\n"
        "<li>Style: long, flowing pure-white beard</li>\n"
        "<li>Ideal for: Gandalf the White, Merlin, Dumbledore cosplay, Halloween, carnival, LARP, theatre</li>\n"
        "<li>Attachment: elastic band</li>\n"
        "<li>Made in Greece — custom sizes available on request</li>\n"
        "</ul>"
    ),
    "short_en": "<p>Long white wizard beard — Gandalf / Merlin style. Handcrafted in Greece. Elastic band attachment. Perfect for cosplay, carnival and theatre.</p>",
    "desc_el": (
        "<p>Η <strong>Γενειάδα Λευκού Μάγου</strong> συμπληρώνει το εμβληματικό look του μεγάλου "
        "λευκού μάγου — μακριά, ρέουσα, καθάρια λευκή. Ιδανική μόνη της ή σε συνδυασμό με "
        "την αντίστοιχη Περούκα Λευκού Μάγου για το πλήρες κοστούμι Γκάνταλφ, Μέρλιν ή Ντάμπλντορ.</p>\n"
        "<p>Χειροποίητη στο εργαστήριό μας στην Ελλάδα με πάνω από 45 χρόνια παράδοσης. "
        "Στερεώνεται εύκολα με το συνοδευτικό λαστιχάκι — χωρίς κόλλα. "
        "Έτοιμη για χρήση αμέσως.</p>\n"
        "<ul>\n"
        "<li>Στυλ: μακριά, ρέουσα λευκή γενειάδα</li>\n"
        "<li>Κατάλληλη για: Gandalf, Merlin, Dumbledore cosplay, Halloween, αποκριές, LARP, θέατρο</li>\n"
        "<li>Στερέωση: λαστιχάκι</li>\n"
        "<li>Κατασκευή στην Ελλάδα — διαθέσιμη κατά παραγγελία σε ειδικά μεγέθη</li>\n"
        "</ul>"
    ),
    "short_el": "<p>Μακριά λευκή γενειάδα μάγου — Γκάνταλφ / Μέρλιν. Χειροποίητη στην Ελλάδα. Στερέωση με λαστιχάκι. Ιδανική για cosplay και αποκριές.</p>",
    "slug_en": "white-wizards-long-beard-gandalf-merlin-cosplay",
    "slug_el": "geneiada-lefkou-magou-gandalf-merlin",
    "meta_en": "White Wizard's Long Beard — Gandalf / Merlin Style | Alegro Athens",
    "meta_el": "Γενειάδα Λευκού Μάγου — Γκάνταλφ / Μέρλιν | Alegro Αθήνα",
},

196: {
    "name_en": "Gray Wizard's Long Wig — Gandalf Style | Handmade in Greece",
    "name_el": "Περούκα Γκρίζου Μάγου Μακριά — Γκάνταλφ | Χειροποίητη στην Ελλάδα",
    "desc_en": (
        "<p>The <strong>Gray Wizard's Long Wig</strong> recreates the iconic flowing silver-grey hair "
        "of the great grey wizard — the look made legendary by Gandalf the Grey. "
        "Whether you are heading to a cosplay event, a Halloween party, a carnival, "
        "or a theatrical production, this wig delivers a powerful, authentic fantasy look.</p>\n"
        "<p>Handcrafted in our workshop in Greece with over 45 years of wig-making tradition. "
        "Features a comfortable elastic base that fits head circumferences from 42 to 63 cm. "
        "Ready to wear — no styling required. "
        "Can be paired with our matching <strong>Gray Wizard's Beard</strong> for the full wizard look.</p>\n"
        "<ul>\n"
        "<li>Style: long, flowing silver-grey hair</li>\n"
        "<li>Ideal for: Gandalf the Grey cosplay, Halloween, carnival, LARP, theatre, film</li>\n"
        "<li>Elastic base: fits 42–63 cm head circumference</li>\n"
        "<li>Made in Greece — custom sizes available on request</li>\n"
        "</ul>"
    ),
    "short_en": "<p>Long grey wizard wig — Gandalf style. Handcrafted in Greece. Elastic base, fits all. Perfect for cosplay, carnival and theatre.</p>",
    "desc_el": (
        "<p>Η <strong>Περούκα Γκρίζου Μάγου</strong> αποδίδει τα εμβληματικά ρέουσα ασημόγκριζα "
        "μαλλιά του μεγάλου γκρίζου μάγου — το look που έγινε θρυλικό με τον Γκάνταλφ τον Γκρίζο. "
        "Ιδανική για cosplay, Halloween, αποκριές ή θεατρικές παραγωγές.</p>\n"
        "<p>Χειροποίητη στο εργαστήριό μας στην Ελλάδα με πάνω από 45 χρόνια παράδοσης. "
        "Διαθέτει ελαστική βάση που εφαρμόζει σε περίμετρο κεφαλής από 42 έως 63 εκ. "
        "Έτοιμη για χρήση — δεν απαιτεί styling. "
        "Συνδυάζεται με τη <strong>Γενειάδα Γκρίζου Μάγου</strong> για το πλήρες look.</p>\n"
        "<ul>\n"
        "<li>Στυλ: μακριά, ρέουσα ασημόγκριζη περούκα</li>\n"
        "<li>Κατάλληλη για: Gandalf cosplay, Halloween, αποκριές, LARP, θέατρο, κινηματογράφο</li>\n"
        "<li>Ελαστική βάση: εφαρμόζει σε περίμετρο κεφαλής 42–63 εκ.</li>\n"
        "<li>Κατασκευή στην Ελλάδα — διαθέσιμη κατά παραγγελία σε ειδικά μεγέθη</li>\n"
        "</ul>"
    ),
    "short_el": "<p>Μακριά γκρίζα περούκα μάγου — Γκάνταλφ. Χειροποίητη στην Ελλάδα. Ελαστική βάση, εφαρμόζει σε όλους.</p>",
    "slug_en": "gray-wizards-long-wig-gandalf-cosplay",
    "slug_el": "perouka-gkrizou-magou-gandalf",
    "meta_en": "Gray Wizard's Long Wig — Gandalf Style | Alegro Athens",
    "meta_el": "Περούκα Γκρίζου Μάγου — Γκάνταλφ | Alegro Αθήνα",
},

197: {
    "name_en": "Gray Wizard's Long Beard — Gandalf Style | Handmade in Greece",
    "name_el": "Γενειάδα Γκρίζου Μάγου Μακριά — Γκάνταλφ | Χειροποίητη στην Ελλάδα",
    "desc_en": (
        "<p>The <strong>Gray Wizard's Long Beard</strong> completes the iconic look of Gandalf the Grey "
        "— long, wild, and silver-grey. Perfect on its own or paired with our matching "
        "Gray Wizard's Wig for the full Gandalf costume.</p>\n"
        "<p>Handcrafted in our workshop in Greece with over 45 years of wig-making tradition. "
        "Attaches easily with the included elastic band — no glue required. "
        "Ready to wear straight out of the box.</p>\n"
        "<ul>\n"
        "<li>Style: long, wild silver-grey beard</li>\n"
        "<li>Ideal for: Gandalf the Grey cosplay, Halloween, carnival, LARP, theatre, film</li>\n"
        "<li>Attachment: elastic band</li>\n"
        "<li>Made in Greece — custom sizes available on request</li>\n"
        "</ul>"
    ),
    "short_en": "<p>Long grey wizard beard — Gandalf style. Handcrafted in Greece. Elastic band attachment. Perfect for cosplay, carnival and theatre.</p>",
    "desc_el": (
        "<p>Η <strong>Γενειάδα Γκρίζου Μάγου</strong> συμπληρώνει το εμβληματικό look του Γκάνταλφ "
        "— μακριά, άγρια, ασημόγκριζη. Ιδανική μόνη της ή σε συνδυασμό με την αντίστοιχη "
        "Περούκα Γκρίζου Μάγου για το πλήρες κοστούμι Γκάνταλφ.</p>\n"
        "<p>Χειροποίητη στο εργαστήριό μας στην Ελλάδα με πάνω από 45 χρόνια παράδοσης. "
        "Στερεώνεται εύκολα με το συνοδευτικό λαστιχάκι — χωρίς κόλλα. "
        "Έτοιμη για χρήση αμέσως.</p>\n"
        "<ul>\n"
        "<li>Στυλ: μακριά, άγρια ασημόγκριζη γενειάδα</li>\n"
        "<li>Κατάλληλη για: Gandalf cosplay, Halloween, αποκριές, LARP, θέατρο, κινηματογράφο</li>\n"
        "<li>Στερέωση: λαστιχάκι</li>\n"
        "<li>Κατασκευή στην Ελλάδα — διαθέσιμη κατά παραγγελία σε ειδικά μεγέθη</li>\n"
        "</ul>"
    ),
    "short_el": "<p>Μακριά γκρίζα γενειάδα μάγου — Γκάνταλφ. Χειροποίητη στην Ελλάδα. Στερέωση με λαστιχάκι. Ιδανική για cosplay και αποκριές.</p>",
    "slug_en": "gray-wizards-long-beard-gandalf-cosplay",
    "slug_el": "geneiada-gkrizou-magou-gandalf",
    "meta_en": "Gray Wizard's Long Beard — Gandalf Style | Alegro Athens",
    "meta_el": "Γενειάδα Γκρίζου Μάγου — Γκάνταλφ | Alegro Αθήνα",
},

}  # end PRODUCTS

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

# ── Login ─────────────────────────────────────────────────────────────────────
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
print('Logged in.\n')

# ── Update each product ───────────────────────────────────────────────────────
for pid, c in PRODUCTS.items():
    print(f'Updating PID {pid} — {c["name_en"][:60]}...')
    r_edit = s.get(f'{ADMIN}/index.php/sell/catalog/products/{pid}/edit',
                   params={'_token': cat_tok}, allow_redirects=True, timeout=25)
    edit_tok = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r_edit.url).group(1)
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
        if not nm or 'paginator' in nm.group(1): continue
        sel = (re.search(r'<option[^>]+selected[^>]*value="([^"]*)"', body, re.I) or
               re.search(r'<option[^>]*value="([^"]*)"', body, re.I))
        all_inputs[nm.group(1)] = sel.group(1) if sel else ''

    payload = {k: html_mod.unescape(v) for k, v in all_inputs.items() if k not in EXCLUDE}

    payload['product[details][features][feature_id]']        = '0'
    payload['product[options][visibility][visibility]']      = 'both'
    payload['product[options][visibility][online_only]']     = '0'
    payload['product[shipping][delivery_time_note_type]']    = '1'

    payload['product[header][name][1]'] = c['name_en']
    payload['product[header][name][2]'] = c['name_el']
    payload['product[description][description][1]']       = c['desc_en']
    payload['product[description][description][2]']       = c['desc_el']
    payload['product[description][description_short][1]'] = c['short_en']
    payload['product[description][description_short][2]'] = c['short_el']
    payload['product[seo][link_rewrite][1]'] = c['slug_en']
    payload['product[seo][link_rewrite][2]'] = c['slug_el']
    payload['product[seo][meta_title][1]']   = c['meta_en']
    payload['product[seo][meta_title][2]']   = c['meta_el']
    payload['_token'] = edit_tok

    r_save = s.post(
        f'{ADMIN}/index.php/sell/catalog/products/{pid}/edit',
        params={'_token': edit_tok},
        data=payload,
        headers={'Referer': r_edit.url},
        allow_redirects=True, timeout=25,
    )
    fv = re.search(r'data-form-valid="(\d+)"', r_save.text)
    valid = fv.group(1) if fv else '?'
    if valid == '1':
        print(f'  → OK\n')
    else:
        inv = re.findall(r'name="([^"]+)"[^>]*class="[^"]*is-invalid', r_save.text, re.I)
        errs = re.findall(r'"message"\s*:\s*"([^"]+)"', r_save.text)
        print(f'  → FAIL  invalid: {inv[:4]}  errors: {errs[:3]}\n')

print('Done.')
