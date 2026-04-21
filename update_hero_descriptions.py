"""
Write complete bilingual descriptions for the four 1821 Greek Revolution hero products:
  265 — Kolokotronis wig
  266 — Karaiskakis wig
  268 — Diakos moustache
  386 — Kapodistrias wig
"""
import requests, re, sys, html as html_mod
sys.stdout.reconfigure(encoding='utf-8')

ADMIN  = 'https://alegro.gr/admin875fdclzkf27m3shsg9'
PASSWD = 'cultivatesandspreadslove13579' + chr(33)
EMAIL  = 'damoncollective@gmail.com'

# ── Product content ───────────────────────────────────────────────────────────

PRODUCTS = {

265: {
    "name_en": "Kolokotronis Wig — Hero of the 1821 Greek Revolution",
    "name_el": "Περούκα Κολοκοτρώνη — Ήρωας της Επανάστασης του 1821",
    "desc_en": (
        "<p>The <strong>Kolokotronis Wig</strong> recreates the iconic dark, wild curls "
        "of Theodoros Kolokotronis — the legendary general who led the Greek forces to "
        "victory during the War of Independence of 1821. One of the most recognisable "
        "figures in Greek history, Kolokotronis is immortalised in paintings, statues, "
        "and films with his fierce, flowing dark mane.</p>"
        "<p>This theatrical-quality wig faithfully captures that look, making it the "
        "ideal choice for theatrical productions, historical reenactments, school events, "
        "and carnival costumes celebrating Greek heritage. "
        "Handcrafted in our small atelier in Athens, Greece, with over 45 years of "
        "wig-making tradition. Features an elastic base that comfortably fits head "
        "circumferences from 42 to 63 cm.</p>"
        "<ul>"
        "<li>Style: Dark, wild curly hair — inspired by Theodoros Kolokotronis</li>"
        "<li>Ideal for: theatre, historical reenactment, school plays, carnival, 25th March events</li>"
        "<li>Elastic base: fits 42–63 cm head circumference</li>"
        "<li>Made in Greece — custom sizes available on request</li>"
        "</ul>"
    ),
    "short_en": "<p>Dark curly wig inspired by General Kolokotronis, hero of the 1821 Greek Revolution. Made in Athens, Greece.</p>",
    "desc_el": (
        "<p>Η <strong>περούκα Κολοκοτρώνη</strong> αναπαράγει τις εμβληματικές, σκοτεινές, "
        "άγριες μπούκλες του Θεόδωρου Κολοκοτρώνη — του θρυλικού στρατηγού που οδήγησε "
        "τις ελληνικές δυνάμεις στη νίκη κατά τον Αγώνα Ανεξαρτησίας του 1821. "
        "Μία από τις πιο αναγνωρίσιμες μορφές της ελληνικής ιστορίας, ο Κολοκοτρώνης "
        "έχει αθανατιστεί σε πίνακες, αγάλματα και ταινίες με την άγρια, ρέουσα σκοτεινή χαίτη του.</p>"
        "<p>Αυτή η περούκα επαγγελματικής ποιότητας αποδίδει με πιστότητα αυτή την εικόνα, "
        "καθιστώντας την ιδανική επιλογή για θεατρικές παραστάσεις, ιστορικές αναπαραστάσεις, "
        "σχολικές εκδηλώσεις και αποκριάτικες μεταμφιέσεις που τιμούν την ελληνική κληρονομιά. "
        "Χειροποίητη στο μικρό μας ατελιέ στην Αθήνα, με πάνω από 45 χρόνια παράδοσης. "
        "Διαθέτει ελαστική βάση που προσαρμόζεται άνετα σε περίμετρο κεφαλής από 42 έως 63 εκ.</p>"
        "<ul>"
        "<li>Στυλ: Σκοτεινά, άγρια σγουρά μαλλιά — εμπνευσμένα από τον Θεόδωρο Κολοκοτρώνη</li>"
        "<li>Κατάλληλη για: θέατρο, ιστορικές αναπαραστάσεις, σχολικές παραστάσεις, αποκριές, εκδηλώσεις 25ης Μαρτίου</li>"
        "<li>Ελαστική βάση: κατάλληλη για περίμετρο κεφαλής 42–63 εκ.</li>"
        "<li>Κατασκευή στην Ελλάδα — διαθέσιμη κατασκευή κατά παραγγελία σε ειδικά μεγέθη</li>"
        "</ul>"
    ),
    "short_el": "<p>Σκοτεινή σγουρή περούκα εμπνευσμένη από τον στρατηγό Κολοκοτρώνη, ήρωα της Επανάστασης του 1821. Κατασκευή στην Αθήνα.</p>",
    "slug_en": "kolokotronis-wig-1821-greek-revolution",
    "slug_el": "perouka-kolokotroni-iroas-epanastasis-1821",
    "meta_en": "Kolokotronis Wig | 1821 Greek Revolution Hero | Alegro Athens",
    "meta_el": "Περούκα Κολοκοτρώνη | Ήρωας Επανάστασης 1821 | Alegro Αθήνα",
},

266: {
    "name_en": "Karaiskakis Wig — Hero of the 1821 Greek Revolution",
    "name_el": "Περούκα Καραϊσκάκη — Ήρωας της Επανάστασης του 1821",
    "desc_en": (
        "<p>The <strong>Karaiskakis Wig</strong> recreates the rugged, distinctive look "
        "of Georgios Karaiskakis — one of the most daring and celebrated military commanders "
        "of the Greek War of Independence of 1821. Known for his boldness and unconventional "
        "tactics, Karaiskakis remains a beloved hero of Greek national memory, commemorated "
        "every year on the 25th of March.</p>"
        "<p>This theatrical-quality wig faithfully captures the wild, natural hair of a "
        "Greek warrior of the early 19th century, making it the perfect choice for theatre "
        "productions, historical reenactments, school celebrations, and carnival costumes. "
        "Handcrafted in our small atelier in Athens, Greece, with over 45 years of "
        "wig-making tradition. Features an elastic base that comfortably fits head "
        "circumferences from 42 to 63 cm.</p>"
        "<ul>"
        "<li>Style: Rugged natural hair — inspired by Georgios Karaiskakis</li>"
        "<li>Ideal for: theatre, historical reenactment, school plays, carnival, 25th March events</li>"
        "<li>Elastic base: fits 42–63 cm head circumference</li>"
        "<li>Made in Greece — custom sizes available on request</li>"
        "</ul>"
    ),
    "short_en": "<p>Theatrical wig inspired by Karaiskakis, hero of the 1821 Greek Revolution. Made in Athens, Greece.</p>",
    "desc_el": (
        "<p>Η <strong>περούκα Καραϊσκάκη</strong> αναπαράγει το χαρακτηριστικό, ατίθασο "
        "look του Γεώργιου Καραϊσκάκη — ενός από τους πιο τολμηρούς και διάσημους "
        "στρατιωτικούς αρχηγούς της Ελληνικής Επανάστασης του 1821. Γνωστός για το θάρρος "
        "και τις ασυμβατικές τακτικές του, ο Καραϊσκάκης παραμένει αγαπημένος ήρωας της "
        "ελληνικής εθνικής μνήμης, που τιμάται κάθε χρόνο στις 25 Μαρτίου.</p>"
        "<p>Αυτή η περούκα επαγγελματικής ποιότητας αποδίδει με πιστότητα τα άγρια, "
        "φυσικά μαλλιά ενός Έλληνα αγωνιστή των αρχών του 19ου αιώνα, αποτελώντας "
        "την τέλεια επιλογή για θεατρικές παραστάσεις, ιστορικές αναπαραστάσεις, "
        "σχολικές εκδηλώσεις και αποκριάτικες μεταμφιέσεις. "
        "Χειροποίητη στο μικρό μας ατελιέ στην Αθήνα, με πάνω από 45 χρόνια παράδοσης. "
        "Διαθέτει ελαστική βάση που προσαρμόζεται άνετα σε περίμετρο κεφαλής από 42 έως 63 εκ.</p>"
        "<ul>"
        "<li>Στυλ: Άγρια φυσικά μαλλιά — εμπνευσμένα από τον Γεώργιο Καραϊσκάκη</li>"
        "<li>Κατάλληλη για: θέατρο, ιστορικές αναπαραστάσεις, σχολικές παραστάσεις, αποκριές, εκδηλώσεις 25ης Μαρτίου</li>"
        "<li>Ελαστική βάση: κατάλληλη για περίμετρο κεφαλής 42–63 εκ.</li>"
        "<li>Κατασκευή στην Ελλάδα — διαθέσιμη κατασκευή κατά παραγγελία σε ειδικά μεγέθη</li>"
        "</ul>"
    ),
    "short_el": "<p>Θεατρική περούκα εμπνευσμένη από τον Καραϊσκάκη, ήρωα της Επανάστασης του 1821. Κατασκευή στην Αθήνα.</p>",
    "slug_en": "karaiskakis-wig-1821-greek-revolution",
    "slug_el": "perouka-karaiskaki-iroas-epanastasis-1821",
    "meta_en": "Karaiskakis Wig | 1821 Greek Revolution Hero | Alegro Athens",
    "meta_el": "Περούκα Καραϊσκάκη | Ήρωας Επανάστασης 1821 | Alegro Αθήνα",
},

268: {
    "name_en": "Athanasios Diakos Moustache — Hero of the 1821 Greek Revolution",
    "name_el": "Μουστάκι Αθανάσιου Διάκου — Ήρωας της Επανάστασης του 1821",
    "desc_en": (
        "<p>The <strong>Athanasios Diakos Moustache</strong> recreates the bold, thick "
        "moustache of Athanasios Diakos — one of the most celebrated martyrs of the "
        "Greek War of Independence of 1821. A former monk turned fearless military commander, "
        "Diakos was captured by the Ottomans at the Battle of Alamana and executed with "
        "extraordinary bravery, becoming an eternal symbol of Greek heroism and sacrifice.</p>"
        "<p>This handcrafted theatrical moustache is made from high-quality synthetic fibre "
        "and attaches securely to the upper lip for a convincing, authentic look. "
        "Perfect for theatrical productions, historical reenactments, school celebrations "
        "of the 25th of March, and carnival costumes honouring Greek national heroes.</p>"
        "<p>Handcrafted in our small atelier in Athens, Greece, with over 45 years of "
        "theatrical accessory-making tradition.</p>"
        "<ul>"
        "<li>Style: Thick, dark moustache — inspired by Athanasios Diakos</li>"
        "<li>Ideal for: theatre, historical reenactment, school plays, carnival, 25th March events</li>"
        "<li>Material: High-quality synthetic fibre</li>"
        "<li>Made in Greece</li>"
        "</ul>"
    ),
    "short_en": "<p>Theatrical moustache inspired by Athanasios Diakos, martyr-hero of the 1821 Greek Revolution. Made in Athens, Greece.</p>",
    "desc_el": (
        "<p>Το <strong>μουστάκι Αθανάσιου Διάκου</strong> αναπαράγει το τολμηρό, πυκνό "
        "μουστάκι του Αθανάσιου Διάκου — ενός από τους πιο αγαπημένους μάρτυρες της "
        "Ελληνικής Επανάστασης του 1821. Πρώην μοναχός που μετατράπηκε σε ατρόμητο "
        "στρατιωτικό αρχηγό, ο Διάκος αιχμαλωτίστηκε από τους Οθωμανούς στη μάχη "
        "της Αλαμάνας και εκτελέστηκε με εξαιρετική γενναιότητα, γινόμενος αιώνιο σύμβολο "
        "ελληνικού ηρωισμού και θυσίας.</p>"
        "<p>Αυτό το χειροποίητο θεατρικό μουστάκι είναι κατασκευασμένο από υψηλής ποιότητας "
        "συνθετική ίνα και προσαρμόζεται με ασφάλεια στο άνω χείλος για μια πειστική, "
        "αυθεντική εμφάνιση. Ιδανικό για θεατρικές παραστάσεις, ιστορικές αναπαραστάσεις, "
        "σχολικές εκδηλώσεις της 25ης Μαρτίου και αποκριάτικες μεταμφιέσεις που τιμούν "
        "τους Έλληνες εθνικούς ήρωες.</p>"
        "<p>Χειροποίητο στο μικρό μας ατελιέ στην Αθήνα, με πάνω από 45 χρόνια παράδοσης "
        "στην κατασκευή θεατρικών αξεσουάρ.</p>"
        "<ul>"
        "<li>Στυλ: Πυκνό, σκοτεινό μουστάκι — εμπνευσμένο από τον Αθανάσιο Διάκο</li>"
        "<li>Κατάλληλο για: θέατρο, ιστορικές αναπαραστάσεις, σχολικές παραστάσεις, αποκριές, εκδηλώσεις 25ης Μαρτίου</li>"
        "<li>Υλικό: Υψηλής ποιότητας συνθετική ίνα</li>"
        "<li>Κατασκευή στην Ελλάδα</li>"
        "</ul>"
    ),
    "short_el": "<p>Θεατρικό μουστάκι εμπνευσμένο από τον Αθανάσιο Διάκο, μάρτυρα-ήρωα της Επανάστασης του 1821. Κατασκευή στην Αθήνα.</p>",
    "slug_en": "diakos-moustache-1821-greek-revolution-hero",
    "slug_el": "moustaki-diakos-iroas-epanastasis-1821",
    "meta_en": "Athanasios Diakos Moustache | 1821 Greek Revolution Hero | Alegro Athens",
    "meta_el": "Μουστάκι Αθανάσιου Διάκου | Ήρωας Επανάστασης 1821 | Alegro Αθήνα",
},

386: {
    "name_en": "Ioannis Kapodistrias Theatrical Wig | Reenactment & Stage | Made in Greece",
    "name_el": "Περούκα Καποδίστριας | Θεατρική Ιστορική Περούκα | Κατασκευή Ελλάδα",
    "desc_en": (
        "<p>The <strong>Ioannis Kapodistrias Theatrical Wig</strong> is a stage-quality wig "
        "that faithfully recreates the iconic look of Greece's first Governor, as seen in "
        "the 2026 epic film <em>Kapodistrias</em> directed by Ioannis Smaragdis. "
        "Featuring voluminous silver-grey curls in authentic 18th–19th century aristocratic "
        "style, this wig is the ideal choice for theatre productions, historical reenactments, "
        "carnival costumes, and period film or TV productions.</p>"
        "<p>Ioannis Kapodistrias (1776–1831) was a distinguished Greek statesman and diplomat "
        "who served as the first head of state of independent Greece. His elegant, composed "
        "appearance — silver-grey hair, refined bearing — has made him one of the most "
        "dignified figures of modern Greek history.</p>"
        "<p>Handcrafted in our small atelier in Athens, Greece, with over 45 years of "
        "wig-making expertise. Features an elastic base that comfortably fits head "
        "circumferences from 42 to 63 cm.</p>"
        "<ul>"
        "<li>Style: Voluminous silver-grey curls, mid-length, 19th-century aristocratic</li>"
        "<li>Inspired by the film <em>Kapodistrias</em> (2026) — directed by Ioannis Smaragdis</li>"
        "<li>Ideal for: theatre, historical reenactment, carnival, film/TV productions</li>"
        "<li>Elastic base: fits 42–63 cm head circumference</li>"
        "<li>Made in Greece</li>"
        "</ul>"
    ),
    "short_en": "<p>Silver-grey theatrical wig inspired by Ioannis Kapodistrias, first Governor of Greece. As seen in the 2026 film. Made in Athens.</p>",
    "desc_el": (
        "<p>Η <strong>θεατρική περούκα Ιωάννης Καποδίστριας</strong> είναι περούκα "
        "επαγγελματικής ποιότητας που αναπαράγει με πιστότητα το εμβληματικό look "
        "του πρώτου Κυβερνήτη της Ελλάδας, όπως εμφανίζεται στην επική ταινία "
        "«<em>Καποδίστριας</em>» 2026 του σκηνοθέτη Ιωάννη Σμαράγδη. "
        "Πλούσιες ασημόγκριζες μπούκλες σε αριστοκρατικό ύφος 18ου–19ου αιώνα.</p>"
        "<p>Ο Ιωάννης Καποδίστριας (1776–1831) ήταν διακεκριμένος Έλληνας πολιτικός "
        "και διπλωμάτης που διετέλεσε πρώτος κυβερνήτης της ανεξάρτητης Ελλάδας. "
        "Η κομψή, συγκρατημένη εμφάνισή του — ασημόγκριζα μαλλιά, εκλεπτυσμένη "
        "παρουσία — τον καθιστά μία από τις πιο αξιοπρεπείς μορφές της νεότερης "
        "ελληνικής ιστορίας.</p>"
        "<p>Χειροποίητη στο μικρό μας ατελιέ στην Αθήνα, με πάνω από 45 χρόνια εμπειρίας "
        "στην κατασκευή περούκων. Διαθέτει ελαστική βάση που προσαρμόζεται άνετα σε "
        "περίμετρο κεφαλής από 42 έως 63 εκ.</p>"
        "<ul>"
        "<li>Στυλ: Ογκώδεις ασημόγκριζες μπούκλες, μεσαίο μήκος, αριστοκρατικό 19ου αιώνα</li>"
        "<li>Εμπνευσμένη από την ταινία <em>Καποδίστριας</em> (2026) — σκηνοθεσία Ιωάννη Σμαράγδη</li>"
        "<li>Κατάλληλη για: θέατρο, ιστορικές αναπαραστάσεις, αποκριές, κινηματογράφο/TV</li>"
        "<li>Ελαστική βάση: κατάλληλη για περίμετρο κεφαλής 42–63 εκ.</li>"
        "<li>Κατασκευή στην Ελλάδα</li>"
        "</ul>"
    ),
    "short_el": "<p>Ασημόγκριζη θεατρική περούκα εμπνευσμένη από τον Καποδίστρια, πρώτο Κυβερνήτη της Ελλάδας. Από την ταινία 2026. Κατασκευή στην Αθήνα.</p>",
    "slug_en": "kapodistrias-theatrical-wig-1821-first-governor-greece",
    "slug_el": "perouka-kapodistrias-theatriki-istoriki-kyvernitis",
    "meta_en": "Kapodistrias Theatrical Wig | First Governor of Greece | Alegro Athens",
    "meta_el": "Περούκα Καποδίστριας | Πρώτος Κυβερνήτης Ελλάδας | Alegro Αθήνα",
},

}  # end PRODUCTS

# ── EXCLUDE ───────────────────────────────────────────────────────────────────
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

# ── Submit each product ───────────────────────────────────────────────────────
for pid, content in PRODUCTS.items():
    print(f'Updating PID {pid} — {content["name_en"][:50]}…')

    r_edit = s.get(f'{ADMIN}/index.php/sell/catalog/products/{pid}/edit',
                   params={'_token': cat_tok}, allow_redirects=True, timeout=25)
    edit_tok = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r_edit.url).group(1)
    html = r_edit.text

    all_inputs = {}
    for im in re.finditer(r'<input[^>]+>', html, re.I):
        tag = im.group(0)
        nm = re.search(r'\bname="([^"]+)"', tag, re.I)
        vm = re.search(r'\bvalue="([^"]*)"', tag, re.I)
        if nm: all_inputs[nm.group(1)] = vm.group(1) if vm else ''

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

    # Names
    payload['product[header][name][1]'] = content['name_en']
    payload['product[header][name][2]'] = content['name_el']

    # Descriptions
    payload['product[description][description][1]']       = content['desc_en']
    payload['product[description][description][2]']       = content['desc_el']
    payload['product[description][description_short][1]'] = content['short_en']
    payload['product[description][description_short][2]'] = content['short_el']

    # SEO
    payload['product[seo][link_rewrite][1]'] = content['slug_en']
    payload['product[seo][link_rewrite][2]'] = content['slug_el']
    payload['product[seo][meta_title][1]']   = content['meta_en']
    payload['product[seo][meta_title][2]']   = content['meta_el']

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
        print(f'  → FAIL  invalid fields: {inv[:4]}\n')

print('Done.')
