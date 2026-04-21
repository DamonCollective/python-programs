#!/usr/bin/env python3
"""
Update names and descriptions for all Xena and Cecilia wig products.
Templates follow description_standards.md (Cecilia Black as base).

Xena (Σίσσυ) — long straight wig with fringe (13 colors):
  21 Black, 22 Blonde, 23 Auburn, 24 Brown, 63 White,
  65 Light Brown, 66 Red, 67 Purple, 68 Green, 69 Pink,
  70 Fuchsia, 71 Orange, 72 Light Green

Cecilia — bob wig with fringe (7 colors):
  46 Black, 47 Purple, 48 Pink, 49 Fuchsia,
  50 Auburn, 51 Blonde, 52 Red
"""
import requests, re, sys, html as html_mod
sys.stdout.reconfigure(encoding='utf-8')

ADMIN  = 'https://alegro.gr/admin875fdclzkf27m3shsg9'
EMAIL  = 'damoncollective@gmail.com'
PASSWD = 'cultivatesandspreadslove13579' + chr(33)


# Color name mapping EN → EL feminine adjective (used in name, desc headings)
color_el_adj = {
    "Black":       "Μαύρη",
    "Blonde":      "Ξανθιά",
    "Auburn":      "Ακαζού",
    "Brown":       "Καστανή",
    "White":       "Λευκή",
    "Light Brown": "Ανοιχτή Καστανή",
    "Red":         "Κόκκινη",
    "Purple":      "Μωβ",
    "Green":       "Πράσινη",
    "Pink":        "Ροζ",
    "Fuchsia":     "Φούξια",
    "Orange":      "Πορτοκαλί",
    "Light Green": "Λαχανί",
}

# EN → EL neuter form (used in "εδώ σε {color_neuter}")
color_el_neuter = {
    "Black":       "μαύρο",
    "Blonde":      "ξανθό",
    "Auburn":      "ακαζού",
    "Brown":       "καστανό",
    "White":       "λευκό",
    "Light Brown": "ανοιχτό καστανό",
    "Red":         "κόκκινο",
    "Purple":      "μωβ",
    "Green":       "πράσινο",
    "Pink":        "ροζ",
    "Fuchsia":     "φούξια",
    "Orange":      "πορτοκαλί",
    "Light Green": "λαχανί",
}


def xena(color_en, color_slug):
    el_adj    = color_el_adj[color_en]
    el_neuter = color_el_neuter[color_en]
    en_lower  = color_en.lower()
    return {
        "name_en": f"Xena Long {color_en} Wig with Fringe | Handmade in Greece",
        "name_el": f"Σίσσυ {el_adj} Μακριά Περούκα με Φράντζα | φτιάχνεται στην Ελλάδα",
        "desc_en": (
            f"<p>The <strong>Xena {color_en} Wig</strong> is a long, straight wig with a neat fringe — "
            f"a bold, dramatic style. Available in many colours, here in {en_lower}. "
            f"A great choice for fancy dress, cosplay, theatrical productions, Halloween, "
            f"and any occasion where you want to make a strong impression.</p>\n"
            "<p>Made in our workshop in Athens, Greece. "
            "Features a comfortable elastic base that fits head circumferences from 42 to 63 cm. "
            "Easy to wash and comb — built to last for years.</p>\n"
            "<ul>\n"
            f"<li>Style: long straight hair with fringe — {en_lower}</li>\n"
            "<li>Ideal for: cosplay, Halloween, carnival, theatre, fantasy costume</li>\n"
            "<li>Elastic base: fits 42–63 cm head circumference</li>\n"
            "<li>Made in Greece — custom sizes available on request</li>\n"
            "</ul>"
        ),
        "short_en": f"<p>Long {en_lower} wig with fringe — Xena warrior princess style. Handmade in Greece. Elastic base, fits all.</p>",
        "desc_el": (
            f"<p>Η Περούκα Σίσσυ {el_adj} είναι μια μακριά, ίσια περούκα με φράντζα — "
            f"ένα τολμηρό, δυναμικό στυλ. Σε πολλά χρώματα, εδώ σε {el_neuter}. "
            f"Είναι μια ωραία επιλογή για μεταμφιέσεις, cosplay, role-playing, απόκριες και Halloween.</p>\n"
            "<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. "
            "Διαθέτει ελαστική βάση που εφαρμόζει σε περίμετρο κεφαλής από 42 έως 63 εκ. "
            "Πλένεται και χτενίζεται εύκολα — φτιαγμένη για να αντέχει χρόνια.</p>\n"
            "<ul>\n"
            f"<li>Στυλ: μακριά ίσια με φράντζα — {el_adj.lower()}</li>\n"
            "<li>Κατάλληλη για: cosplay, Halloween, απόκριες, θέατρο, φαντασιακή στολή</li>\n"
            "<li>Ελαστική βάση: εφαρμόζει σε περίμετρο κεφαλής 42–63 εκ.</li>\n"
            "<li>Κατασκευάζεται στην Ελλάδα — διαθέσιμη κατά παραγγελία σε ειδικά μεγέθη</li>\n"
            "</ul>"
        ),
        "short_el": f"<p>{el_adj} μακριά περούκα με φράντζα — Σίσσυ. Φτιάχνεται στην Ελλάδα. Ελαστική βάση, εφαρμόζει σε όλους.</p>",
        "slug_en": f"xena-long-{color_slug}-wig-with-fringe",
        "slug_el": f"sissy-{color_slug}-makria-perouka-me-frantza",
        "meta_en": f"Xena Long {color_en} Wig with Fringe | Handmade in Greece | Alegro Athens",
        "meta_el": f"Σίσσυ {el_adj} Μακριά Περούκα με Φράντζα | Alegro Αθήνα",
    }


def cecilia(color_en, color_slug):
    el_adj    = color_el_adj[color_en]
    el_neuter = color_el_neuter[color_en]
    en_lower  = color_en.lower()
    return {
        "name_en": f"Cecilia {color_en} Bob Wig with Fringe | Handmade in Greece",
        "name_el": f"Σεσίλια {el_adj} Καρέ Περούκα με Φράντζα | φτιάχνεται στην Ελλάδα",
        "desc_en": (
            f"<p>The <strong>Cecilia {color_en} Wig</strong> is a chic, chin-length bob with a neat fringe — "
            f"a timeless cut that instantly changes any look. Available in many colours, here in {en_lower}. "
            f"A great choice for retro styles, fancy dress, cosplay, carnival, and Halloween events.</p>\n"
            "<p>Made in our workshop in Athens, Greece. "
            "Features a comfortable elastic base that fits head circumferences from 42 to 63 cm. "
            "Easy to wash and comb — built to last for years.</p>\n"
            "<ul>\n"
            f"<li>Style: chin-length bob with fringe — {en_lower}</li>\n"
            "<li>Ideal for: cosplay, Halloween, carnival, retro / vintage look</li>\n"
            "<li>Elastic base: fits 42–63 cm head circumference</li>\n"
            "<li>Made in Greece — custom sizes available on request</li>\n"
            "</ul>"
        ),
        "short_en": f"<p>{color_en} bob wig with fringe — Cecilia style. Handmade in Greece. Elastic base, fits all. Perfect for cosplay and carnival.</p>",
        "desc_el": (
            f"<p>Η Περούκα Σεσίλια {el_adj} είναι ένα κομψό καρέ με φράντζα — "
            f"ένα διαχρονικό κούρεμα που αλλάζει εύκολα την εμφάνιση. Σε πολλά χρώματα, εδώ σε {el_neuter}. "
            f"Είναι μια ωραία επιλογή για retro εμφανίσεις, μεταμφιέσεις, role-playing, απόκριες και Halloween.</p>\n"
            "<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. "
            "Διαθέτει ελαστική βάση που εφαρμόζει σε περίμετρο κεφαλής από 42 έως 63 εκ. "
            "Πλένεται και χτενίζεται εύκολα — φτιαγμένη για να αντέχει χρόνια.</p>\n"
            "<ul>\n"
            f"<li>Στυλ: καρέ με φράντζα — {el_adj.lower()}</li>\n"
            "<li>Κατάλληλη για: cosplay, Halloween, απόκριες, retro / vintage look</li>\n"
            "<li>Ελαστική βάση: εφαρμόζει σε περίμετρο κεφαλής 42–63 εκ.</li>\n"
            "<li>Κατασκευάζεται στην Ελλάδα — διαθέσιμη κατά παραγγελία σε ειδικά μεγέθη</li>\n"
            "</ul>"
        ),
        "short_el": f"<p>{el_adj} καρέ περούκα με φράντζα — Σεσίλια. Φτιάχνεται στην Ελλάδα. Ελαστική βάση, εφαρμόζει σε όλους.</p>",
        "slug_en": f"cecilia-{color_slug}-bob-wig-with-fringe",
        "slug_el": f"cecilia-{color_slug}-kare-perouka-me-frantza",
        "meta_en": f"Cecilia {color_en} Bob Wig with Fringe | Handmade in Greece | Alegro Athens",
        "meta_el": f"Σεσίλια {el_adj} Καρέ Περούκα με Φράντζα | Alegro Αθήνα",
    }


PRODUCTS = {
    # ── Xena (Σίσσυ) ──────────────────────────────────────────────────────────
    21:  xena("Black",       "black"),
    22:  xena("Blonde",      "blonde"),
    23:  xena("Auburn",      "auburn"),
    24:  xena("Brown",       "brown"),
    63:  xena("White",       "white"),
    65:  xena("Light Brown", "light-brown"),
    66:  xena("Red",         "red"),
    67:  xena("Purple",      "purple"),
    68:  xena("Green",       "green"),
    69:  xena("Pink",        "pink"),
    70:  xena("Fuchsia",     "fuchsia"),
    71:  xena("Orange",      "orange"),
    72:  xena("Light Green", "light-green"),
    # ── Cecilia ───────────────────────────────────────────────────────────────
    46:  cecilia("Black",   "black"),
    47:  cecilia("Purple",  "purple"),
    48:  cecilia("Pink",    "pink"),
    49:  cecilia("Fuchsia", "fuchsia"),
    50:  cecilia("Auburn",  "auburn"),
    51:  cecilia("Blonde",  "blonde"),
    52:  cecilia("Red",     "red"),
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

ok, fail = 0, 0
for pid, c in PRODUCTS.items():
    print(f'PID {pid} — {c["name_en"][:65]}...')
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

    payload['product[header][name][1]']                   = c['name_en']
    payload['product[header][name][2]']                   = c['name_el']
    payload['product[description][description][1]']       = c['desc_en']
    payload['product[description][description][2]']       = c['desc_el']
    payload['product[description][description_short][1]'] = c['short_en']
    payload['product[description][description_short][2]'] = c['short_el']
    payload['product[seo][link_rewrite][1]']              = c['slug_en']
    payload['product[seo][link_rewrite][2]']              = c['slug_el']
    payload['product[seo][meta_title][1]']                = c['meta_en']
    payload['product[seo][meta_title][2]']                = c['meta_el']
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
        print(f'  → OK')
        ok += 1
    else:
        inv = re.findall(r'name="([^"]+)"[^>]*class="[^"]*is-invalid', r_save.text, re.I)
        errs = re.findall(r'"message"\s*:\s*"([^"]+)"', r_save.text)
        print(f'  → FAIL  invalid: {inv[:4]}  errors: {errs[:3]}')
        fail += 1

print(f'\n{"═"*60}')
print(f'Done.  OK: {ok}  Failed: {fail}')
print(f'{"═"*60}')
