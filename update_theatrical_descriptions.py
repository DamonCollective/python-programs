#!/usr/bin/env python3
"""
Add bilingual descriptions to all theatrical products that currently have none.
Skips any product that already has a description (rule: never overwrite existing).

Products covered:
  267  Athanasios Diakos wig
  268  Diakos moustache
  269  Karaiskakis moustache
  270  Kolokotronis moustache
  325  Sifis black moustache
  326  President set (wig + moustache + soul patch)
  327  President dark brown moustache + soul patch
  334  Thick black moustache
  335  Trader's handlebar brown moustache
  349  Mitsos thick brown moustache
  351  Uncle (Bampas) white moustache
  386  Kapodistrias wig

Products already with descriptions (SKIPPED by script):
  265  Kolokotronis wig      ← existing description kept
  266  Karaiskakis wig       ← existing description kept
"""
import requests, re, sys, html as html_mod
sys.stdout.reconfigure(encoding='utf-8')

ADMIN  = 'https://alegro.gr/admin875fdclzkf27m3shsg9'
EMAIL  = 'damoncollective@gmail.com'
PASSWD = 'cultivatesandspreadslove13579' + chr(33)

# ── Content ───────────────────────────────────────────────────────────────────

PRODUCTS = {

# ─────────────────────────────────────────────────────────────────────────────
267: {  # Athanasios Diakos wig
    "desc_en": (
        "<p>The <strong>Athanasios Diakos Theatrical Wig</strong> recreates the look of one of the most beloved heroes of the Greek Revolution of 1821. "
        "Athanasios Diakos — a brave young commander from Fokida — met his death with legendary courage at the Battle of Alamana. "
        "This wig features dark, medium-length hair in the style of the early 19th century Greek warriors.</p>\n"
        "<p>Made in our workshop in Athens, Greece. "
        "Features a comfortable elastic base that fits head circumferences from 42 to 63 cm. "
        "Easy to wash and comb — built to last for years.</p>\n"
        "<ul>\n"
        "<li>Style: dark, medium-length warrior's hair — 1821 era</li>\n"
        "<li>Ideal for: theatre, historical reenactment, carnival, school events, 25th March celebrations</li>\n"
        "<li>Elastic base: fits 42–63 cm head circumference</li>\n"
        "<li>Made in Greece — custom sizes available on request</li>\n"
        "</ul>"
    ),
    "desc_el": (
        "<p>Η <strong>θεατρική περούκα Αθανάσιος Διάκος</strong> αναπαράγει την εμφάνιση ενός από τους πιο αγαπημένους ήρωες της Ελληνικής Επανάστασης του 1821. "
        "Ο Αθανάσιος Διάκος — νεαρός και γενναίος οπλαρχηγός από τη Φωκίδα — έγινε σύμβολο θυσίας στη μάχη της Αλαμάνας. "
        "Η περούκα αναπαράγει τα σκούρα, μεσαίου μήκους μαλλιά του στο ύφος των αγωνιστών του 1821.</p>\n"
        "<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. "
        "Διαθέτει ελαστική βάση που εφαρμόζει σε περίμετρο κεφαλής από 42 έως 63 εκ. "
        "Πλένεται και χτενίζεται εύκολα — φτιαγμένη για να αντέχει χρόνια.</p>\n"
        "<ul>\n"
        "<li>Στυλ: σκούρα, μεσαίου μήκους — εποχή 1821</li>\n"
        "<li>Κατάλληλη για: θέατρο, ιστορικές παρελάσεις, αποκριές, σχολικές εκδηλώσεις, 25η Μαρτίου</li>\n"
        "<li>Ελαστική βάση: εφαρμόζει σε περίμετρο κεφαλής 42–63 εκ.</li>\n"
        "<li>Κατασκευάζεται στην Ελλάδα — διαθέσιμη κατά παραγγελία σε ειδικά μεγέθη</li>\n"
        "</ul>"
    ),
    "short_en": "<p>Dark medium-length theatrical wig — Athanasios Diakos, hero of the 1821 Greek Revolution. Handmade in Greece. Elastic base, fits all.</p>",
    "short_el": "<p>Θεατρική περούκα Αθανάσιος Διάκος, ήρωας της Ελληνικής Επανάστασης 1821. Φτιάχνεται στην Ελλάδα. Ελαστική βάση.</p>",
    "meta_en":  "Athanasios Diakos 1821 Theatrical Wig | Handmade in Greece | Alegro Athens",
    "meta_el":  "Περούκα Αθανάσιος Διάκος Ήρωας 1821 | Θεατρική Περούκα | Alegro Αθήνα",
},

# ─────────────────────────────────────────────────────────────────────────────
268: {  # Diakos moustache
    "desc_en": (
        "<p>The <strong>Athanasios Diakos Moustache</strong> is a handmade theatrical moustache recreating the look of this legendary hero of the 1821 Greek Revolution. "
        "Made from natural human hair mounted on a fine lace base, it is the perfect companion to the Athanasios Diakos wig for a complete theatrical costume.</p>\n"
        "<p>Made in our workshop in Athens, Greece. "
        "Applied easily with theatrical spirit gum adhesive (not included). Suitable for all skin types.</p>\n"
        "<ul>\n"
        "<li>Style: dark hero's moustache — 1821 era</li>\n"
        "<li>Ideal for: theatre, historical reenactment, carnival, 25th March celebrations</li>\n"
        "<li>Material: natural human hair on fine lace base</li>\n"
        "<li>Made in Greece</li>\n"
        "</ul>"
    ),
    "desc_el": (
        "<p>Το <strong>Μουστάκι Αθανάσιου Διάκου</strong> είναι χειροποίητο θεατρικό μουστάκι που αναπαράγει την εμφάνιση του θρυλικού ήρωα της Επανάστασης του 1821. "
        "Κατασκευασμένο από φυσική τρίχα σε βάση τούλι, είναι το ιδανικό συμπλήρωμα στην περούκα Διάκου για πλήρη θεατρική ενδυμασία.</p>\n"
        "<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. "
        "Τοποθετείται εύκολα με ειδική κόλλα θεάτρου (δεν συμπεριλαμβάνεται). Κατάλληλο για όλους τους τύπους δέρματος.</p>\n"
        "<ul>\n"
        "<li>Στυλ: σκούρο μουστάκι ήρωα — εποχή 1821</li>\n"
        "<li>Κατάλληλο για: θέατρο, ιστορικές παρελάσεις, αποκριές, 25η Μαρτίου</li>\n"
        "<li>Υλικό: φυσική τρίχα σε βάση τούλι</li>\n"
        "<li>Κατασκευάζεται στην Ελλάδα</li>\n"
        "</ul>"
    ),
    "short_en": "<p>Handmade theatrical moustache — Athanasios Diakos, hero of 1821. Natural human hair on lace base. Made in Greece.</p>",
    "short_el": "<p>Χειροποίητο θεατρικό μουστάκι Αθανάσιος Διάκος, ήρωας 1821. Φυσική τρίχα σε τούλι. Κατασκευή Ελλάδα.</p>",
    "meta_en":  "Athanasios Diakos Theatrical Moustache | 1821 Hero | Handmade in Greece | Alegro",
    "meta_el":  "Μουστάκι Αθανάσιος Διάκος Ήρωας 1821 | Θεατρικό | Κατασκευή Ελλάδα | Alegro",
},

# ─────────────────────────────────────────────────────────────────────────────
269: {  # Karaiskakis moustache
    "desc_en": (
        "<p>The <strong>Georgios Karaiskakis Moustache</strong> is a handmade theatrical moustache recreating the distinctive look of Georgios Karaiskakis, "
        "one of the most daring commanders of the 1821 Greek Revolution. "
        "Made from natural human hair on a fine lace base, it pairs perfectly with the Karaiskakis wig for a complete theatrical costume.</p>\n"
        "<p>Made in our workshop in Athens, Greece. "
        "Applied easily with theatrical spirit gum adhesive (not included).</p>\n"
        "<ul>\n"
        "<li>Style: dark warrior's moustache — 1821 era</li>\n"
        "<li>Ideal for: theatre, historical reenactment, carnival, 25th March celebrations</li>\n"
        "<li>Material: natural human hair on fine lace base</li>\n"
        "<li>Made in Greece</li>\n"
        "</ul>"
    ),
    "desc_el": (
        "<p>Το <strong>Μουστάκι Γεώργιου Καραϊσκάκη</strong> είναι χειροποίητο θεατρικό μουστάκι που αναπαράγει το χαρακτηριστικό look "
        "του Γεώργιου Καραϊσκάκη, ενός από τους πιο τολμηρούς οπλαρχηγούς της Επανάστασης του 1821. "
        "Κατασκευασμένο από φυσική τρίχα σε βάση τούλι, συνδυάζεται ιδανικά με την περούκα Καραϊσκάκη για πλήρη θεατρική εμφάνιση.</p>\n"
        "<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. "
        "Τοποθετείται εύκολα με ειδική κόλλα θεάτρου (δεν συμπεριλαμβάνεται).</p>\n"
        "<ul>\n"
        "<li>Στυλ: σκούρο μουστάκι πολεμιστή — εποχή 1821</li>\n"
        "<li>Κατάλληλο για: θέατρο, ιστορικές παρελάσεις, αποκριές, 25η Μαρτίου</li>\n"
        "<li>Υλικό: φυσική τρίχα σε βάση τούλι</li>\n"
        "<li>Κατασκευάζεται στην Ελλάδα</li>\n"
        "</ul>"
    ),
    "short_en": "<p>Handmade theatrical moustache — Georgios Karaiskakis, hero of 1821. Natural human hair on lace base. Made in Greece.</p>",
    "short_el": "<p>Χειροποίητο θεατρικό μουστάκι Γεώργιος Καραϊσκάκης, ήρωας 1821. Φυσική τρίχα σε τούλι. Κατασκευή Ελλάδα.</p>",
    "meta_en":  "Karaiskakis Theatrical Moustache | 1821 Hero | Handmade in Greece | Alegro",
    "meta_el":  "Μουστάκι Καραϊσκάκης Ήρωας 1821 | Θεατρικό | Κατασκευή Ελλάδα | Alegro",
},

# ─────────────────────────────────────────────────────────────────────────────
270: {  # Kolokotronis moustache
    "desc_en": (
        "<p>The <strong>Theodoros Kolokotronis Moustache</strong> is a handmade theatrical moustache recreating the bold look of Theodoros Kolokotronis, "
        "the legendary commander-in-chief of the Greek Revolution of 1821. "
        "Made from natural human hair on a fine lace base, it pairs perfectly with the Kolokotronis wig for a complete theatrical costume.</p>\n"
        "<p>Made in our workshop in Athens, Greece. "
        "Applied easily with theatrical spirit gum adhesive (not included).</p>\n"
        "<ul>\n"
        "<li>Style: dark, full moustache — 1821 era</li>\n"
        "<li>Ideal for: theatre, historical reenactment, carnival, 25th March celebrations</li>\n"
        "<li>Material: natural human hair on fine lace base</li>\n"
        "<li>Made in Greece</li>\n"
        "</ul>"
    ),
    "desc_el": (
        "<p>Το <strong>Μουστάκι Θεόδωρου Κολοκοτρώνη</strong> είναι χειροποίητο θεατρικό μουστάκι που αναπαράγει το τολμηρό look "
        "του Θεόδωρου Κολοκοτρώνη, του θρυλικού αρχιστράτηγου της Ελληνικής Επανάστασης του 1821. "
        "Κατασκευασμένο από φυσική τρίχα σε βάση τούλι, συνδυάζεται ιδανικά με την περούκα Κολοκοτρώνη για πλήρη θεατρική εμφάνιση.</p>\n"
        "<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. "
        "Τοποθετείται εύκολα με ειδική κόλλα θεάτρου (δεν συμπεριλαμβάνεται).</p>\n"
        "<ul>\n"
        "<li>Στυλ: σκούρο, πλούσιο μουστάκι — εποχή 1821</li>\n"
        "<li>Κατάλληλο για: θέατρο, ιστορικές παρελάσεις, αποκριές, 25η Μαρτίου</li>\n"
        "<li>Υλικό: φυσική τρίχα σε βάση τούλι</li>\n"
        "<li>Κατασκευάζεται στην Ελλάδα</li>\n"
        "</ul>"
    ),
    "short_en": "<p>Handmade theatrical moustache — Theodoros Kolokotronis, hero of 1821. Natural human hair on lace base. Made in Greece.</p>",
    "short_el": "<p>Χειροποίητο θεατρικό μουστάκι Θεόδωρος Κολοκοτρώνης, ήρωας 1821. Φυσική τρίχα σε τούλι. Κατασκευή Ελλάδα.</p>",
    "meta_en":  "Kolokotronis Theatrical Moustache | 1821 Hero | Handmade in Greece | Alegro",
    "meta_el":  "Μουστάκι Κολοκοτρώνης Ήρωας 1821 | Θεατρικό | Κατασκευή Ελλάδα | Alegro",
},

# ─────────────────────────────────────────────────────────────────────────────
325: {  # Sifis black moustache
    "desc_en": (
        "<p>The <strong>Sifis Black Moustache</strong> is a handmade theatrical fake moustache crafted from natural black human hair on a fine lace base. "
        "With its bold, classic shape and highly realistic appearance, it is ideal for theatrical performances, cosplay, Halloween costumes, "
        "and any fancy dress occasion that calls for a convincing moustache.</p>\n"
        "<p>Made in our workshop in Athens, Greece. "
        "Applied easily with theatrical spirit gum adhesive (not included). "
        "The lace base blends naturally with skin for a seamless stage look.</p>\n"
        "<ul>\n"
        "<li>Style: thick, classic black moustache — Sifis style</li>\n"
        "<li>Ideal for: theatre, cosplay, Halloween, carnival, fancy dress</li>\n"
        "<li>Material: natural human hair on fine lace base</li>\n"
        "<li>Made in Greece</li>\n"
        "</ul>"
    ),
    "desc_el": (
        "<p>Το <strong>Μουστάκι Σήφης μαύρο</strong> είναι χειροποίητο θεατρικό μουστάκι από φυσική μαύρη τρίχα σε βάση τούλι. "
        "Με το κλασικό, δυναμικό σχήμα και την ρεαλιστική εμφάνιση, είναι ιδανικό για θεατρικές παραστάσεις, cosplay, αποκριές "
        "και κάθε μεταμφίεση που απαιτεί πειστικό μουστάκι.</p>\n"
        "<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. "
        "Τοποθετείται εύκολα με ειδική κόλλα θεάτρου (δεν συμπεριλαμβάνεται). "
        "Η βάση τούλι ενσωματώνεται φυσικά στο δέρμα για αδιόρατη εμφάνιση σκηνής.</p>\n"
        "<ul>\n"
        "<li>Στυλ: παχύ, κλασικό μαύρο μουστάκι — στυλ Σήφης</li>\n"
        "<li>Κατάλληλο για: θέατρο, cosplay, αποκριές, Halloween, μεταμφιέσεις</li>\n"
        "<li>Υλικό: φυσική τρίχα σε βάση τούλι</li>\n"
        "<li>Κατασκευάζεται στην Ελλάδα</li>\n"
        "</ul>"
    ),
    "short_en": "<p>Thick black handmade theatrical moustache on lace — Sifis style. Natural human hair. Made in Greece.</p>",
    "short_el": "<p>Παχύ μαύρο χειροποίητο θεατρικό μουστάκι σε τούλι — στυλ Σήφης. Φυσική τρίχα. Κατασκευή Ελλάδα.</p>",
    "meta_en":  "Sifis Black Theatrical Moustache on Lace | Natural Hair | Handmade in Greece | Alegro",
    "meta_el":  "Μουστάκι Σήφης Μαύρο σε Τούλι | Φυσική Τρίχα | Χειροποίητο | Alegro",
},

# ─────────────────────────────────────────────────────────────────────────────
326: {  # President set (wig + moustache + soul patch)
    "desc_en": (
        "<p>The <strong>President Set</strong> is a complete theatrical look in one package: a wig, a handmade moustache, and a wool crepe soul patch beard. "
        "Designed to create an authoritative, distinguished appearance, it is the ideal choice for theatrical characters, political satire costumes, "
        "Halloween, and any occasion that demands a memorable presence.</p>\n"
        "<p>Made in our workshop in Athens, Greece. "
        "The moustache and soul patch are mounted on a fine lace base — applied with theatrical spirit gum adhesive (not included). "
        "The wig features an elastic base fitting head circumferences from 42 to 63 cm.</p>\n"
        "<ul>\n"
        "<li>Includes: wig + moustache + wool crepe soul patch beard</li>\n"
        "<li>Ideal for: theatre, political satire, cosplay, Halloween, carnival, fancy dress</li>\n"
        "<li>Moustache and soul patch: natural human hair / wool crepe on lace base</li>\n"
        "<li>Made in Greece</li>\n"
        "</ul>"
    ),
    "desc_el": (
        "<p>Το <strong>Σετ Πρόεδρος</strong> είναι ένα πλήρες θεατρικό look σε ένα πακέτο: περούκα, χειροποίητο μουστάκι και γενάκι κρεπ μαλλί. "
        "Σχεδιασμένο για να δημιουργεί αυθεντική, αξιοπρεπή εμφάνιση, είναι ιδανικό για θεατρικούς χαρακτήρες, κοστούμια πολιτικής σάτιρας, "
        "αποκριές και κάθε περίσταση που απαιτεί αξέχαστη παρουσία.</p>\n"
        "<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. "
        "Το μουστάκι και το γενάκι τοποθετούνται σε βάση τούλι με ειδική κόλλα θεάτρου (δεν συμπεριλαμβάνεται). "
        "Η περούκα διαθέτει ελαστική βάση για περίμετρο κεφαλής 42–63 εκ.</p>\n"
        "<ul>\n"
        "<li>Περιλαμβάνει: περούκα + μουστάκι + γενάκι κρεπ μαλλί</li>\n"
        "<li>Κατάλληλο για: θέατρο, πολιτική σάτιρα, cosplay, αποκριές, μεταμφιέσεις</li>\n"
        "<li>Μουστάκι και γενάκι: φυσική τρίχα / κρεπ μαλλί σε βάση τούλι</li>\n"
        "<li>Κατασκευάζεται στην Ελλάδα</li>\n"
        "</ul>"
    ),
    "short_en": "<p>Complete theatrical set: wig + moustache + soul patch beard — President style. Handmade in Greece.</p>",
    "short_el": "<p>Πλήρες θεατρικό σετ: περούκα + μουστάκι + γενάκι — στυλ Πρόεδρος. Χειροποίητο, κατασκευή Ελλάδα.</p>",
    "meta_en":  "President Theatrical Set: Wig + Moustache + Soul Patch | Handmade in Greece | Alegro",
    "meta_el":  "Σετ Πρόεδρος: Περούκα + Μουστάκι + Γενάκι | Χειροποίητο | Alegro",
},

# ─────────────────────────────────────────────────────────────────────────────
327: {  # President moustache (dark brown + soul patch)
    "desc_en": (
        "<p>The <strong>President Moustache</strong> is a handmade theatrical fake moustache with a matching wool crepe soul patch beard, "
        "crafted from dark brown natural human hair on a fine lace base. "
        "With its dignified, formal shape, it creates an authoritative look perfect for theatre, political satire costumes, "
        "and elegant fancy dress occasions.</p>\n"
        "<p>Made in our workshop in Athens, Greece. "
        "Applied easily with theatrical spirit gum adhesive (not included). "
        "The lace base blends naturally with skin.</p>\n"
        "<ul>\n"
        "<li>Style: dark brown presidential moustache with soul patch beard</li>\n"
        "<li>Ideal for: theatre, political satire, cosplay, Halloween, carnival</li>\n"
        "<li>Material: natural human hair + wool crepe soul patch on lace base</li>\n"
        "<li>Made in Greece</li>\n"
        "</ul>"
    ),
    "desc_el": (
        "<p>Το <strong>Μουστάκι Πρόεδρος</strong> είναι χειροποίητο θεατρικό μουστάκι με αντίστοιχο γενάκι κρεπ μαλλί, "
        "κατασκευασμένο από σκούρο καστανό φυσική τρίχα σε βάση τούλι. "
        "Με το αξιοπρεπές, επίσημο σχήμα του, δημιουργεί αυθεντική εμφάνιση ιδανική για θέατρο, κοστούμια πολιτικής σάτιρας "
        "και κομψές μεταμφιέσεις.</p>\n"
        "<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. "
        "Τοποθετείται εύκολα με ειδική κόλλα θεάτρου (δεν συμπεριλαμβάνεται). "
        "Η βάση τούλι ενσωματώνεται φυσικά στο δέρμα.</p>\n"
        "<ul>\n"
        "<li>Στυλ: σκούρο καστανό μουστάκι Πρόεδρος με γενάκι</li>\n"
        "<li>Κατάλληλο για: θέατρο, πολιτική σάτιρα, cosplay, αποκριές, μεταμφιέσεις</li>\n"
        "<li>Υλικό: φυσική τρίχα + κρεπ μαλλί γενάκι σε βάση τούλι</li>\n"
        "<li>Κατασκευάζεται στην Ελλάδα</li>\n"
        "</ul>"
    ),
    "short_en": "<p>Dark brown handmade theatrical moustache with soul patch — President style. Natural human hair on lace. Made in Greece.</p>",
    "short_el": "<p>Σκούρο καστανό χειροποίητο μουστάκι με γενάκι — στυλ Πρόεδρος. Φυσική τρίχα σε τούλι. Κατασκευή Ελλάδα.</p>",
    "meta_en":  "President Theatrical Moustache with Soul Patch | Natural Hair on Lace | Handmade in Greece | Alegro",
    "meta_el":  "Μουστάκι Πρόεδρος με Γενάκι | Φυσική Τρίχα σε Τούλι | Χειροποίητο | Alegro",
},

# ─────────────────────────────────────────────────────────────────────────────
334: {  # Thick black moustache
    "desc_en": (
        "<p>The <strong>Thick Black Moustache</strong> is a handmade theatrical fake moustache crafted from natural black human hair on a fine lace base. "
        "Its bold, full shape makes a strong visual statement — the perfect choice for theatre, character costumes, Halloween, "
        "and any occasion calling for a convincing, dramatic moustache.</p>\n"
        "<p>Made in our workshop in Athens, Greece. "
        "Applied easily with theatrical spirit gum adhesive (not included). "
        "The lace base blends naturally with skin for a realistic appearance.</p>\n"
        "<ul>\n"
        "<li>Style: thick, full black moustache</li>\n"
        "<li>Ideal for: theatre, cosplay, Halloween, carnival, fancy dress</li>\n"
        "<li>Material: natural human hair on fine lace base</li>\n"
        "<li>Made in Greece</li>\n"
        "</ul>"
    ),
    "desc_el": (
        "<p>Το <strong>Παχύ Μαύρο Μουστάκι</strong> είναι χειροποίητο θεατρικό μουστάκι από φυσική μαύρη τρίχα σε βάση τούλι. "
        "Το δυναμικό, πλούσιο σχήμα του κάνει ισχυρή οπτική εντύπωση — ιδανική επιλογή για θέατρο, κοστούμια χαρακτήρων, αποκριές "
        "και κάθε περίσταση που απαιτεί πειστικό, εντυπωσιακό μουστάκι.</p>\n"
        "<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. "
        "Τοποθετείται εύκολα με ειδική κόλλα θεάτρου (δεν συμπεριλαμβάνεται). "
        "Η βάση τούλι ενσωματώνεται φυσικά στο δέρμα.</p>\n"
        "<ul>\n"
        "<li>Στυλ: παχύ, πλούσιο μαύρο μουστάκι</li>\n"
        "<li>Κατάλληλο για: θέατρο, cosplay, αποκριές, Halloween, μεταμφιέσεις</li>\n"
        "<li>Υλικό: φυσική τρίχα σε βάση τούλι</li>\n"
        "<li>Κατασκευάζεται στην Ελλάδα</li>\n"
        "</ul>"
    ),
    "short_en": "<p>Thick black handmade theatrical moustache on lace. Natural human hair. Bold, dramatic look. Made in Greece.</p>",
    "short_el": "<p>Παχύ μαύρο χειροποίητο θεατρικό μουστάκι σε τούλι. Φυσική τρίχα. Εντυπωσιακό look. Κατασκευή Ελλάδα.</p>",
    "meta_en":  "Thick Black Theatrical Moustache on Lace | Natural Human Hair | Handmade in Greece | Alegro",
    "meta_el":  "Παχύ Μαύρο Θεατρικό Μουστάκι σε Τούλι | Φυσική Τρίχα | Χειροποίητο | Alegro",
},

# ─────────────────────────────────────────────────────────────────────────────
335: {  # Trader's handlebar moustache (brown)
    "desc_en": (
        "<p>The <strong>Trader's Handlebar Moustache</strong> is a handmade theatrical fake moustache crafted from natural brown human hair on a fine lace base, "
        "with a distinctive curled handlebar shape. "
        "Inspired by the flamboyant merchants and traders of the 19th century, it adds instant character and flair to any theatrical costume.</p>\n"
        "<p>Made in our workshop in Athens, Greece. "
        "Applied easily with theatrical spirit gum adhesive (not included). "
        "The lace base blends naturally with skin.</p>\n"
        "<ul>\n"
        "<li>Style: curled handlebar moustache — brown</li>\n"
        "<li>Ideal for: theatre, cosplay, Halloween, retro / vintage look, steampunk, fancy dress</li>\n"
        "<li>Material: natural human hair on fine lace base</li>\n"
        "<li>Made in Greece</li>\n"
        "</ul>"
    ),
    "desc_el": (
        "<p>Το <strong>Τσιγκελωτό Μουστάκι Trader's</strong> είναι χειροποίητο θεατρικό μουστάκι από φυσική καστανή τρίχα σε βάση τούλι, "
        "με χαρακτηριστικό τσιγκελωτό σχήμα. "
        "Εμπνευσμένο από τους φλογερούς εμπόρους του 19ου αιώνα, προσθέτει άμεσο χαρακτήρα και στυλ σε κάθε θεατρικό κοστούμι.</p>\n"
        "<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. "
        "Τοποθετείται εύκολα με ειδική κόλλα θεάτρου (δεν συμπεριλαμβάνεται). "
        "Η βάση τούλι ενσωματώνεται φυσικά στο δέρμα.</p>\n"
        "<ul>\n"
        "<li>Στυλ: τσιγκελωτό μουστάκι — καστανό</li>\n"
        "<li>Κατάλληλο για: θέατρο, cosplay, αποκριές, retro / vintage look, steampunk, μεταμφιέσεις</li>\n"
        "<li>Υλικό: φυσική τρίχα σε βάση τούλι</li>\n"
        "<li>Κατασκευάζεται στην Ελλάδα</li>\n"
        "</ul>"
    ),
    "short_en": "<p>Brown handlebar theatrical moustache on lace — Trader style. Natural human hair. Made in Greece.</p>",
    "short_el": "<p>Καστανό τσιγκελωτό θεατρικό μουστάκι σε τούλι — στυλ Trader's. Φυσική τρίχα. Κατασκευή Ελλάδα.</p>",
    "meta_en":  "Trader's Handlebar Theatrical Moustache on Lace | Natural Hair | Handmade in Greece | Alegro",
    "meta_el":  "Τσιγκελωτό Μουστάκι Trader's σε Τούλι | Φυσική Τρίχα | Χειροποίητο | Alegro",
},

# ─────────────────────────────────────────────────────────────────────────────
349: {  # Mitsos thick brown moustache
    "desc_en": (
        "<p>The <strong>Mitsos Brown Moustache</strong> is a handmade theatrical fake moustache crafted from natural brown human hair on a fine lace base. "
        "With its thick, robust shape, the Mitsos style captures the spirit of the classic Greek mustachioed man — "
        "perfect for character roles, folk costumes, and theatrical performances.</p>\n"
        "<p>Made in our workshop in Athens, Greece. "
        "Applied easily with theatrical spirit gum adhesive (not included). "
        "The lace base blends naturally with skin.</p>\n"
        "<ul>\n"
        "<li>Style: thick, full brown moustache — Mitsos style</li>\n"
        "<li>Ideal for: theatre, cosplay, Halloween, carnival, traditional Greek folk costumes</li>\n"
        "<li>Material: natural human hair on fine lace base</li>\n"
        "<li>Made in Greece</li>\n"
        "</ul>"
    ),
    "desc_el": (
        "<p>Το <strong>Μουστάκι Μήτσος καστανό</strong> είναι χειροποίητο θεατρικό μουστάκι από φυσική καστανή τρίχα σε βάση τούλι. "
        "Με το παχύ, δυναμικό σχήμα του, το στυλ Μήτσος αποτυπώνει τον χαρακτήρα του κλασικού Έλληνα μουστακαλή — "
        "ιδανικό για ρόλους χαρακτήρων, παραδοσιακές ενδυμασίες και θεατρικές παραστάσεις.</p>\n"
        "<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. "
        "Τοποθετείται εύκολα με ειδική κόλλα θεάτρου (δεν συμπεριλαμβάνεται). "
        "Η βάση τούλι ενσωματώνεται φυσικά στο δέρμα.</p>\n"
        "<ul>\n"
        "<li>Στυλ: παχύ, πλούσιο καστανό μουστάκι — στυλ Μήτσος</li>\n"
        "<li>Κατάλληλο για: θέατρο, cosplay, αποκριές, παραδοσιακές ελληνικές ενδυμασίες</li>\n"
        "<li>Υλικό: φυσική τρίχα σε βάση τούλι</li>\n"
        "<li>Κατασκευάζεται στην Ελλάδα</li>\n"
        "</ul>"
    ),
    "short_en": "<p>Thick brown handmade theatrical moustache on lace — Mitsos style. Natural human hair. Made in Greece.</p>",
    "short_el": "<p>Παχύ καστανό χειροποίητο μουστάκι σε τούλι — στυλ Μήτσος. Φυσική τρίχα. Κατασκευή Ελλάδα.</p>",
    "meta_en":  "Mitsos Brown Theatrical Moustache on Lace | Natural Human Hair | Handmade in Greece | Alegro",
    "meta_el":  "Μουστάκι Μήτσος Καστανό σε Τούλι | Φυσική Τρίχα | Χειροποίητο | Alegro",
},

# ─────────────────────────────────────────────────────────────────────────────
351: {  # Uncle (Bampas) white moustache
    "desc_en": (
        "<p>The <strong>Uncle White Moustache</strong> is a handmade theatrical fake moustache crafted from natural white human hair on a fine lace base. "
        "Its generous, distinguished shape evokes the image of the classic Greek elder — a wise, authoritative figure. "
        "Perfect for theatrical roles, elder character costumes, and any occasion requiring a dignified presence.</p>\n"
        "<p>Made in our workshop in Athens, Greece. "
        "Applied easily with theatrical spirit gum adhesive (not included). "
        "The lace base blends naturally with skin.</p>\n"
        "<ul>\n"
        "<li>Style: full, distinguished white moustache — Uncle (Bampas) style</li>\n"
        "<li>Ideal for: theatre, character roles, cosplay, Halloween, carnival, elder costumes</li>\n"
        "<li>Material: natural human hair on fine lace base</li>\n"
        "<li>Made in Greece</li>\n"
        "</ul>"
    ),
    "desc_el": (
        "<p>Το <strong>Μουστάκι Μπάρμπας λευκό</strong> είναι χειροποίητο θεατρικό μουστάκι από φυσική λευκή τρίχα σε βάση τούλι. "
        "Το πλούσιο, αξιοπρεπές σχήμα του παραπέμπει στη φιγούρα του κλασικού Έλληνα μεγαλύτερου — σοφού και γεμάτου παρουσία. "
        "Ιδανικό για θεατρικούς ρόλους και μεταμφιέσεις.</p>\n"
        "<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. "
        "Τοποθετείται εύκολα με ειδική κόλλα θεάτρου (δεν συμπεριλαμβάνεται). "
        "Η βάση τούλι ενσωματώνεται φυσικά στο δέρμα.</p>\n"
        "<ul>\n"
        "<li>Στυλ: πλούσιο, αξιοπρεπές λευκό μουστάκι — στυλ Μπάρμπας</li>\n"
        "<li>Κατάλληλο για: θέατρο, ρόλοι χαρακτήρων, cosplay, αποκριές, κοστούμια ηλικιωμένων</li>\n"
        "<li>Υλικό: φυσική τρίχα σε βάση τούλι</li>\n"
        "<li>Κατασκευάζεται στην Ελλάδα</li>\n"
        "</ul>"
    ),
    "short_en": "<p>White handmade theatrical moustache on lace — Uncle (Bampas) style. Natural human hair. Made in Greece.</p>",
    "short_el": "<p>Λευκό χειροποίητο θεατρικό μουστάκι σε τούλι — στυλ Μπάρμπας. Φυσική τρίχα. Κατασκευή Ελλάδα.</p>",
    "meta_en":  "Uncle White Theatrical Moustache on Lace | Natural Human Hair | Handmade in Greece | Alegro",
    "meta_el":  "Μουστάκι Μπάρμπας Λευκό σε Τούλι | Φυσική Τρίχα | Χειροποίητο | Alegro",
},

# ─────────────────────────────────────────────────────────────────────────────
386: {  # Kapodistrias wig
    "desc_en": (
        "<p>The <strong>Ioannis Kapodistrias Theatrical Wig</strong> is a stage-quality wig that faithfully recreates the iconic look of Greece's first Governor, "
        "as seen in the 2026 epic film <em>Kapodistrias</em> directed by Ioannis Smaragdis. "
        "Featuring voluminous silver-grey curls in authentic 18th–19th century aristocratic style, "
        "this wig is the ideal choice for theatre productions, historical reenactments, carnival costumes, and period film or TV productions.</p>\n"
        "<p>Handcrafted in Greece by <strong>Alegro</strong>. "
        "Features a comfortable elastic base that fits head circumferences from 42 to 63 cm.</p>\n"
        "<ul>\n"
        "<li>Style: voluminous silver-grey curls, mid-length</li>\n"
        "<li>Inspired by the film Kapodistrias (2026) — Ioannis Smaragdis</li>\n"
        "<li>Ideal for: theatre, reenactment, carnival, film/TV</li>\n"
        "<li>Elastic base: fits 42–63 cm head circumference</li>\n"
        "<li>Made in Greece — custom sizes available on request</li>\n"
        "</ul>"
    ),
    "desc_el": (
        "<p>Η <strong>θεατρική περούκα Ιωάννης Καποδίστριας</strong> είναι περούκα επαγγελματικής ποιότητας που αναπαράγει με πιστότητα "
        "το εμβληματικό look του πρώτου Κυβερνήτη της Ελλάδας, όπως εμφανίζεται στην επική ταινία «<em>Καποδίστριας</em>» 2026 "
        "του σκηνοθέτη Ιωάννη Σμαράγδη. "
        "Πλούσιες ασημόγκριζες μπούκλες σε αριστοκρατικό ύφος 18ου–19ου αιώνα.</p>\n"
        "<p>Κατασκευή στην Ελλάδα από την <strong>Alegro</strong>. "
        "Διαθέτει ελαστική βάση που εφαρμόζει σε περίμετρο κεφαλής από 42 έως 63 εκ.</p>\n"
        "<ul>\n"
        "<li>Στυλ: πλούσιες ασημόγκριζες μπούκλες, μεσαίο μήκος</li>\n"
        "<li>Εμπνευσμένη από την ταινία Καποδίστριας (2026) — Ι. Σμαράγδης</li>\n"
        "<li>Κατάλληλη για: θέατρο, reenactment, αποκριές, κινηματογράφο/TV</li>\n"
        "<li>Ελαστική βάση: εφαρμόζει σε περίμετρο κεφαλής 42–63 εκ.</li>\n"
        "<li>Κατασκευάζεται στην Ελλάδα — διαθέσιμη κατά παραγγελία σε ειδικά μεγέθη</li>\n"
        "</ul>"
    ),
    "short_en": "<p>Theatrical wig inspired by the 2026 film Kapodistrias by Ioannis Smaragdis. Voluminous silver-grey curls. Handmade in Greece.</p>",
    "short_el": "<p>Θεατρική περούκα εμπνευσμένη από την ταινία Καποδίστριας 2026. Ασημόγκριζες μπούκλες. Κατασκευή Ελλάδα.</p>",
    "meta_en":  "Ioannis Kapodistrias Theatrical Wig | Made in Greece | Alegro",
    "meta_el":  "Περούκα Καποδίστριας | Θεατρική Ιστορική | Alegro",
},

}  # end PRODUCTS

# ── EXCLUDE list ──────────────────────────────────────────────────────────────
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


def get_textarea(html, name):
    m = re.search(r'<textarea[^>]+name="' + re.escape(name) + r'"[^>]*>(.*?)</textarea>',
                  html, re.I | re.S)
    return html_mod.unescape(m.group(1).strip()) if m else ''


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

ok = fail = skipped = 0

for pid, c in PRODUCTS.items():
    r_edit = s.get(f'{ADMIN}/index.php/sell/catalog/products/{pid}/edit',
                   params={'_token': cat_tok}, allow_redirects=True, timeout=25)
    edit_tok = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r_edit.url).group(1)
    html = r_edit.text

    # ── Rule: skip if description already exists ───────────────────────────
    existing_en = get_textarea(html, 'product[description][description][1]')
    existing_el = get_textarea(html, 'product[description][description][2]')
    if existing_en.strip() or existing_el.strip():
        print(f'PID {pid} — SKIP (already has description)')
        skipped += 1
        continue

    print(f'PID {pid} — {c["short_en"][:60]}...')

    # Scrape inputs + selects
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

    payload['product[description][description][1]']          = c['desc_en']
    payload['product[description][description][2]']          = c['desc_el']
    payload['product[description][description_short][1]']    = c['short_en']
    payload['product[description][description_short][2]']    = c['short_el']
    payload['product[seo][meta_description][1]']             = c['meta_en']
    payload['product[seo][meta_description][2]']             = c['meta_el']
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
print(f'Done.  OK: {ok}  Skipped (already had desc): {skipped}  Failed: {fail}')
print(f'{"═"*60}')
