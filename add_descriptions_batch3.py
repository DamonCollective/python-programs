#!/usr/bin/env python3
"""
Batch 3: PIDs 118-148 (30 products)
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

def get_textarea(html, name):
    m = re.search(r'<textarea[^>]+name="' + re.escape(name) + r'"[^>]*>(.*?)</textarea>', html, re.I | re.S)
    return html_mod.unescape(m.group(1).strip()) if m else ''

# ── Templates ─────────────────────────────────────────────────────────────────

def natalie(en_color, el_fem, el_neuter):
    en = en_color.lower(); el_adj = el_fem.lower()
    return dict(
        desc_en=(
            f"<p>The <strong>Natalie {en_color} Wig</strong> is a long, straight wig with a sweeping side part — "
            f"a feminine, elegant style with a natural fall. Available in many colours, here in {en}. "
            f"A great choice for cosplay, fancy dress, Halloween, and carnival.</p>\n"
            f"<p>Made in our workshop in Athens, Greece. Features a comfortable elastic base that fits head circumferences from 42 to 63 cm. Easy to wash and comb — built to last for years.</p>\n"
            f"<ul>\n<li>Style: long straight hair with side part — {en}</li>\n"
            f"<li>Ideal for: cosplay, Halloween, carnival, retro / vintage look, fantasy costume</li>\n"
            f"<li>Elastic base: fits 42–63 cm head circumference</li>\n"
            f"<li>Made in Greece — custom sizes available on request</li>\n</ul>"
        ),
        desc_el=(
            f"<p>Η <strong>Περούκα Ναταλία {el_fem}</strong> είναι μια μακριά, ίσια περούκα με χωρίστρα στο πλάι — "
            f"θηλυκό, κομψό στυλ με φυσική πτώση. Σε πολλά χρώματα, εδώ σε {el_neuter}. "
            f"Υπέροχη επιλογή για cosplay, μεταμφιέσεις, αποκριές και Halloween.</p>\n"
            f"<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. Διαθέτει ελαστική βάση που εφαρμόζει σε περίμετρο κεφαλής από 42 έως 63 εκ. Πλένεται και χτενίζεται εύκολα — φτιαγμένη για να αντέχει χρόνια.</p>\n"
            f"<ul>\n<li>Στυλ: μακριά ίσια με χωρίστρα στο πλάι — {el_adj}</li>\n"
            f"<li>Κατάλληλη για: cosplay, Halloween, αποκριές, retro / vintage look, φαντασιακή στολή</li>\n"
            f"<li>Ελαστική βάση: εφαρμόζει σε περίμετρο κεφαλής 42–63 εκ.</li>\n"
            f"<li>Κατασκευάζεται στην Ελλάδα — διαθέσιμη κατά παραγγελία σε ειδικά μεγέθη</li>\n</ul>"
        ),
        short_en=f"<p>Long straight {en} wig with side part — Natalie style. Handmade in Greece. Elastic base, fits all.</p>",
        short_el=f"<p>Μακριά ίσια {el_adj} περούκα με χωρίστρα στο πλάι — Ναταλία. Φτιάχνεται στην Ελλάδα. Ελαστική βάση.</p>",
        meta_en=f"Natalie {en_color} Long Straight Wig Side Part | Handmade in Greece | Alegro Athens",
        meta_el=f"Ναταλία {el_fem} Μακριά Ίσια Περούκα Χωρίστρα Πλάι | Alegro Αθήνα",
    )

def ariadne(en_color, el_fem, el_neuter, center_part=False):
    en = en_color.lower(); el_adj = el_fem.lower()
    part_en = " with center part" if center_part else ""
    part_el = " με χωρίστρα στη μέση" if center_part else ""
    return dict(
        desc_en=(
            f"<p>The <strong>Ariadne {en_color} Wig</strong> is a long {en} wig with small decorative braids on the sides — "
            f"a distinctive style that combines free-flowing length with a charming boho detail. "
            f"Available in many colours, here in {en}. A great choice for cosplay, fancy dress, Halloween, and carnival.</p>\n"
            f"<p>Made in our workshop in Athens, Greece. Features a comfortable elastic base that fits head circumferences from 42 to 63 cm. Easy to wear — built to last for years.</p>\n"
            f"<ul>\n<li>Style: long {en} hair with side braids{part_en}</li>\n"
            f"<li>Ideal for: cosplay, Halloween, carnival, boho look, fantasy costume</li>\n"
            f"<li>Elastic base: fits 42–63 cm head circumference</li>\n"
            f"<li>Made in Greece — custom sizes available on request</li>\n</ul>"
        ),
        desc_el=(
            f"<p>Η <strong>Περούκα Αριάδνη {el_fem}</strong> είναι μια μακριά {el_adj} περούκα με μικρά κοτσιδάκια στο πλάι — "
            f"ξεχωριστό στυλ που συνδυάζει το ελεύθερο μήκος με ένα χαρακτηριστικό boho λεπτομέρεια. "
            f"Σε πολλά χρώματα, εδώ σε {el_neuter}. Υπέροχη επιλογή για cosplay, μεταμφιέσεις, αποκριές και Halloween.</p>\n"
            f"<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. Διαθέτει ελαστική βάση που εφαρμόζει σε περίμετρο κεφαλής από 42 έως 63 εκ. Εύκολη στη χρήση — φτιαγμένη για να αντέχει χρόνια.</p>\n"
            f"<ul>\n<li>Στυλ: μακριά {el_adj} με κοτσιδάκια στο πλάι{part_el}</li>\n"
            f"<li>Κατάλληλη για: cosplay, Halloween, αποκριές, boho look, φαντασιακή στολή</li>\n"
            f"<li>Ελαστική βάση: εφαρμόζει σε περίμετρο κεφαλής 42–63 εκ.</li>\n"
            f"<li>Κατασκευάζεται στην Ελλάδα — διαθέσιμη κατά παραγγελία σε ειδικά μεγέθη</li>\n</ul>"
        ),
        short_en=f"<p>Long {en} wig with small side braids — Ariadne style. Handmade in Greece. Elastic base, fits all.</p>",
        short_el=f"<p>Μακριά {el_adj} περούκα με κοτσιδάκια — Αριάδνη. Φτιάχνεται στην Ελλάδα. Ελαστική βάση.</p>",
        meta_en=f"Ariadne {en_color} Long Wig with Braids | Handmade in Greece | Alegro Athens",
        meta_el=f"Αριάδνη {el_fem} Μακριά Περούκα με Κοτσιδάκια | Alegro Αθήνα",
    )

def stella(en_color, el_fem, el_neuter):
    en = en_color.lower(); el_adj = el_fem.lower()
    return dict(
        desc_en=(
            f"<p>The <strong>Stella {en_color} Wig</strong> is a long, curly wig with rich, full-bodied waves — "
            f"a lively, voluminous style full of personality. Available in many colours, here in {en}. "
            f"A wonderful choice for cosplay, Halloween, carnival, and any occasion that calls for abundant, curly hair.</p>\n"
            f"<p>Made in our workshop in Athens, Greece. Features a comfortable elastic base that fits head circumferences from 42 to 63 cm. Easy to wear — built to last for years.</p>\n"
            f"<ul>\n<li>Style: long curly hair — {en}</li>\n"
            f"<li>Ideal for: cosplay, Halloween, carnival, retro / vintage look, fantasy costume</li>\n"
            f"<li>Elastic base: fits 42–63 cm head circumference</li>\n"
            f"<li>Made in Greece — custom sizes available on request</li>\n</ul>"
        ),
        desc_el=(
            f"<p>Η <strong>Περούκα Στέλλα {el_fem}</strong> είναι μια μακριά σγουρή περούκα με πλούσιες, ογκώδεις μπούκλες — "
            f"ζωηρό, εντυπωσιακό στυλ γεμάτο προσωπικότητα. Σε πολλά χρώματα, εδώ σε {el_neuter}. "
            f"Υπέροχη επιλογή για cosplay, Halloween, αποκριές και κάθε στιγμή που θέλετε πλούσια, σγουρά μαλλιά.</p>\n"
            f"<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. Διαθέτει ελαστική βάση που εφαρμόζει σε περίμετρο κεφαλής από 42 έως 63 εκ. Εύκολη στη χρήση — φτιαγμένη για να αντέχει χρόνια.</p>\n"
            f"<ul>\n<li>Στυλ: μακριά σγουρή — {el_adj}</li>\n"
            f"<li>Κατάλληλη για: cosplay, Halloween, αποκριές, retro / vintage look, φαντασιακή στολή</li>\n"
            f"<li>Ελαστική βάση: εφαρμόζει σε περίμετρο κεφαλής 42–63 εκ.</li>\n"
            f"<li>Κατασκευάζεται στην Ελλάδα — διαθέσιμη κατά παραγγελία σε ειδικά μεγέθη</li>\n</ul>"
        ),
        short_en=f"<p>Long curly {en} wig — Stella style. Rich, full-bodied waves. Handmade in Greece. Elastic base, fits all.</p>",
        short_el=f"<p>Μακριά σγουρή {el_adj} περούκα — Στέλλα. Πλούσιες μπούκλες. Φτιάχνεται στην Ελλάδα. Ελαστική βάση.</p>",
        meta_en=f"Stella {en_color} Long Curly Wig | Handmade in Greece | Alegro Athens",
        meta_el=f"Στέλλα {el_fem} Μακριά Σγουρή Περούκα | Alegro Αθήνα",
    )

def peggy(en_color, el_fem, el_neuter):
    en = en_color.lower(); el_adj = el_fem.lower()
    return dict(
        desc_en=(
            f"<p>The <strong>Peggy {en_color} Wig</strong> is a long, curly wig with a headband — "
            f"a playful, romantic style that combines voluminous curls with a neat finishing touch. "
            f"Available in many colours, here in {en}. A great choice for cosplay, Halloween, carnival, and retro looks.</p>\n"
            f"<p>Made in our workshop in Athens, Greece. Features a comfortable elastic base that fits head circumferences from 42 to 63 cm. Easy to wear — built to last for years.</p>\n"
            f"<ul>\n<li>Style: long curly hair with headband — {en}</li>\n"
            f"<li>Ideal for: cosplay, Halloween, carnival, retro / vintage look</li>\n"
            f"<li>Elastic base: fits 42–63 cm head circumference</li>\n"
            f"<li>Made in Greece — custom sizes available on request</li>\n</ul>"
        ),
        desc_el=(
            f"<p>Η <strong>Περούκα Πέγκυ {el_fem}</strong> είναι μια μακριά σγουρή περούκα με κορδέλα — "
            f"παιχνιδιάρικο, ρομαντικό στυλ που συνδυάζει ογκώδεις μπούκλες με μια τακτοποιημένη, γλυκιά λεπτομέρεια. "
            f"Σε πολλά χρώματα, εδώ σε {el_neuter}. Ιδανική για cosplay, Halloween, αποκριές και retro εμφανίσεις.</p>\n"
            f"<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. Διαθέτει ελαστική βάση που εφαρμόζει σε περίμετρο κεφαλής από 42 έως 63 εκ. Εύκολη στη χρήση — φτιαγμένη για να αντέχει χρόνια.</p>\n"
            f"<ul>\n<li>Στυλ: μακριά σγουρή με κορδέλα — {el_adj}</li>\n"
            f"<li>Κατάλληλη για: cosplay, Halloween, αποκριές, retro / vintage look</li>\n"
            f"<li>Ελαστική βάση: εφαρμόζει σε περίμετρο κεφαλής 42–63 εκ.</li>\n"
            f"<li>Κατασκευάζεται στην Ελλάδα — διαθέσιμη κατά παραγγελία σε ειδικά μεγέθη</li>\n</ul>"
        ),
        short_en=f"<p>Long curly {en} wig with headband — Peggy style. Handmade in Greece. Elastic base, fits all.</p>",
        short_el=f"<p>Μακριά σγουρή {el_adj} περούκα με κορδέλα — Πέγκυ. Φτιάχνεται στην Ελλάδα. Ελαστική βάση.</p>",
        meta_en=f"Peggy {en_color} Long Curly Wig with Headband | Handmade in Greece | Alegro Athens",
        meta_el=f"Πέγκυ {el_fem} Μακριά Σγουρή Περούκα με Κορδέλα | Alegro Αθήνα",
    )

def daphne(en_color, el_fem, el_neuter):
    en = en_color.lower(); el_adj = el_fem.lower()
    return dict(
        desc_en=(
            f"<p>The <strong>Daphne {en_color} Wig</strong> is a full, voluminous wig with a big, puffed-out shape — "
            f"a bold style with plenty of body and presence. Available in many colours, here in {en}. "
            f"A fun choice for cosplay, Halloween, carnival, and any occasion that calls for a striking, high-volume look.</p>\n"
            f"<p>Made in our workshop in Athens, Greece. Features a comfortable elastic base that fits head circumferences from 42 to 63 cm. Easy to wear — built to last for years.</p>\n"
            f"<ul>\n<li>Style: full voluminous wig — {en}</li>\n"
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
        short_en=f"<p>Full voluminous {en} wig — Daphne style. Bold, high-volume look. Handmade in Greece. Elastic base, fits all.</p>",
        short_el=f"<p>Σγουρή {el_adj} περούκα — Δάφνη. Τολμηρό, ογκώδες στυλ. Φτιάχνεται στην Ελλάδα. Ελαστική βάση.</p>",
        meta_en=f"Daphne {en_color} Voluminous Wig | Handmade in Greece | Alegro Athens",
        meta_el=f"Δάφνη {el_fem} Σγουρή Περούκα | Alegro Αθήνα",
    )

def samantha(en_color, el_fem, el_neuter):
    en = en_color.lower(); el_adj = el_fem.lower()
    return dict(
        desc_en=(
            f"<p>The <strong>Samantha {en_color} Wig</strong> is a long, straight {en} wig — "
            f"a clean, versatile style that suits many face shapes and occasions. "
            f"A great everyday choice for cosplay, Halloween, carnival, and fancy dress.</p>\n"
            f"<p>Made in our workshop in Athens, Greece. Features a comfortable elastic base that fits head circumferences from 42 to 63 cm. Easy to wash and comb — built to last for years.</p>\n"
            f"<ul>\n<li>Style: long straight {en} wig</li>\n"
            f"<li>Ideal for: cosplay, Halloween, carnival, retro / vintage look</li>\n"
            f"<li>Elastic base: fits 42–63 cm head circumference</li>\n"
            f"<li>Made in Greece — custom sizes available on request</li>\n</ul>"
        ),
        desc_el=(
            f"<p>Η <strong>Περούκα Σαμάνθα {el_fem}</strong> είναι μια μακριά, ίσια {el_adj} περούκα — "
            f"καθαρό, ευέλικτο στυλ που ταιριάζει σε πολλά σχήματα προσώπου και περιστάσεις. "
            f"Ωραία επιλογή για cosplay, Halloween, αποκριές και μεταμφιέσεις.</p>\n"
            f"<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. Διαθέτει ελαστική βάση που εφαρμόζει σε περίμετρο κεφαλής από 42 έως 63 εκ. Πλένεται και χτενίζεται εύκολα — φτιαγμένη για να αντέχει χρόνια.</p>\n"
            f"<ul>\n<li>Στυλ: μακριά ίσια {el_adj} περούκα</li>\n"
            f"<li>Κατάλληλη για: cosplay, Halloween, αποκριές, retro / vintage look</li>\n"
            f"<li>Ελαστική βάση: εφαρμόζει σε περίμετρο κεφαλής 42–63 εκ.</li>\n"
            f"<li>Κατασκευάζεται στην Ελλάδα — διαθέσιμη κατά παραγγελία σε ειδικά μεγέθη</li>\n</ul>"
        ),
        short_en=f"<p>Long straight {en} wig — Samantha style. Handmade in Greece. Elastic base, fits all.</p>",
        short_el=f"<p>Μακριά ίσια {el_adj} περούκα — Σαμάνθα. Φτιάχνεται στην Ελλάδα. Ελαστική βάση.</p>",
        meta_en=f"Samantha {en_color} Long Straight Wig | Handmade in Greece | Alegro Athens",
        meta_el=f"Σαμάνθα {el_fem} Μακριά Ίσια Περούκα | Alegro Αθήνα",
    )

def nora(en_color, el_fem, el_neuter):
    en = en_color.lower(); el_adj = el_fem.lower()
    return dict(
        desc_en=(
            f"<p>The <strong>Nora {en_color} Wig</strong> is a medium-length {en} wig — "
            f"a practical, wearable style that fits naturally and comfortably. Available in many colours, here in {en}. "
            f"A versatile choice for cosplay, Halloween, carnival, and everyday use.</p>\n"
            f"<p>Made in our workshop in Athens, Greece. Features a comfortable elastic base that fits head circumferences from 42 to 63 cm. Easy to wash and comb — built to last for years.</p>\n"
            f"<ul>\n<li>Style: medium-length {en} wig</li>\n"
            f"<li>Ideal for: cosplay, Halloween, carnival, retro / vintage look</li>\n"
            f"<li>Elastic base: fits 42–63 cm head circumference</li>\n"
            f"<li>Made in Greece — custom sizes available on request</li>\n</ul>"
        ),
        desc_el=(
            f"<p>Η <strong>Περούκα Νόρα {el_fem}</strong> είναι μια μεσαία {el_adj} περούκα — "
            f"πρακτικό, άνετο στυλ που εφαρμόζει φυσικά και άνετα. Σε πολλά χρώματα, εδώ σε {el_neuter}. "
            f"Ευέλικτη επιλογή για cosplay, Halloween, αποκριές και καθημερινή χρήση.</p>\n"
            f"<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. Διαθέτει ελαστική βάση που εφαρμόζει σε περίμετρο κεφαλής από 42 έως 63 εκ. Πλένεται και χτενίζεται εύκολα — φτιαγμένη για να αντέχει χρόνια.</p>\n"
            f"<ul>\n<li>Στυλ: μεσαία {el_adj} περούκα</li>\n"
            f"<li>Κατάλληλη για: cosplay, Halloween, αποκριές, retro / vintage look</li>\n"
            f"<li>Ελαστική βάση: εφαρμόζει σε περίμετρο κεφαλής 42–63 εκ.</li>\n"
            f"<li>Κατασκευάζεται στην Ελλάδα — διαθέσιμη κατά παραγγελία σε ειδικά μεγέθη</li>\n</ul>"
        ),
        short_en=f"<p>Medium-length {en} wig — Nora style. Handmade in Greece. Elastic base, fits all.</p>",
        short_el=f"<p>Μεσαία {el_adj} περούκα — Νόρα. Φτιάχνεται στην Ελλάδα. Ελαστική βάση, εφαρμόζει σε όλους.</p>",
        meta_en=f"Nora {en_color} Medium Wig | Handmade in Greece | Alegro Athens",
        meta_el=f"Νόρα {el_fem} Μεσαία Περούκα | Alegro Αθήνα",
    )

# ── Product catalogue ─────────────────────────────────────────────────────────

PRODUCTS = {

    # 118 — HERMES: short blonde curly (just a name)
    118: dict(
        desc_en=(
            "<p>The <strong>Hermes Blonde Curly Wig</strong> is a short, cheerful wig with light blonde curls — "
            "a fun, youthful style that adds an instant lift to any look. "
            "A great choice for cosplay, Halloween, carnival, and retro fancy dress.</p>\n"
            "<p>Made in our workshop in Athens, Greece. Features a comfortable elastic base that fits head circumferences from 42 to 63 cm. Easy to wear — built to last for years.</p>\n"
            "<ul>\n<li>Style: short blonde curly wig</li>\n"
            "<li>Ideal for: cosplay, Halloween, carnival, retro / vintage look</li>\n"
            "<li>Elastic base: fits 42–63 cm head circumference</li>\n"
            "<li>Made in Greece — custom sizes available on request</li>\n</ul>"
        ),
        desc_el=(
            "<p>Η <strong>Περούκα Ερμής Ξανθιά Σγουρή</strong> είναι μια κοντή, εύθυμη περούκα με ανοιχτόχρωμες ξανθές μπούκλες — "
            "διασκεδαστικό, νεανικό στυλ που αλλάζει αμέσως την εμφάνιση. "
            "Ωραία επιλογή για cosplay, Halloween, αποκριές και retro μεταμφιέσεις.</p>\n"
            "<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. Διαθέτει ελαστική βάση που εφαρμόζει σε περίμετρο κεφαλής από 42 έως 63 εκ. Εύκολη στη χρήση — φτιαγμένη για να αντέχει χρόνια.</p>\n"
            "<ul>\n<li>Στυλ: κοντή ξανθιά σγουρή περούκα</li>\n"
            "<li>Κατάλληλη για: cosplay, Halloween, αποκριές, retro / vintage look</li>\n"
            "<li>Ελαστική βάση: εφαρμόζει σε περίμετρο κεφαλής 42–63 εκ.</li>\n"
            "<li>Κατασκευάζεται στην Ελλάδα — διαθέσιμη κατά παραγγελία σε ειδικά μεγέθη</li>\n</ul>"
        ),
        short_en="<p>Short blonde curly wig — Hermes. Fun, youthful style. Handmade in Greece. Elastic base, fits all.</p>",
        short_el="<p>Κοντή ξανθιά σγουρή περούκα — Ερμής. Διασκεδαστικό στυλ. Φτιάχνεται στην Ελλάδα. Ελαστική βάση.</p>",
        meta_en="Hermes Short Blonde Curly Wig | Handmade in Greece | Alegro Athens",
        meta_el="Ερμής Κοντή Ξανθιά Σγουρή Περούκα | Alegro Αθήνα",
    ),

    # 119 — MARK: short gray (just a name)
    119: dict(
        desc_en=(
            "<p>The <strong>Mark Gray Wig</strong> is a short, natural-looking gray wig — "
            "a clean, everyday style that works well for mature character roles, cosplay, and theatrical performances. "
            "Comfortable and convincing for any face shape.</p>\n"
            "<p>Made in our workshop in Athens, Greece. Features a comfortable elastic base that fits head circumferences from 42 to 63 cm. Easy to wear — built to last for years.</p>\n"
            "<ul>\n<li>Style: short gray wig — natural look</li>\n"
            "<li>Ideal for: theatre, cosplay, Halloween, character roles, fancy dress</li>\n"
            "<li>Elastic base: fits 42–63 cm head circumference</li>\n"
            "<li>Made in Greece — custom sizes available on request</li>\n</ul>"
        ),
        desc_el=(
            "<p>Η <strong>Περούκα Μαρκ Γκρι</strong> είναι μια κοντή, φυσικού τύπου γκρι περούκα — "
            "καθαρό, καθημερινό στυλ που ταιριάζει σε ώριμους χαρακτήρες, cosplay και θεατρικές παραστάσεις. "
            "Άνετη και πειστική για κάθε σχήμα προσώπου.</p>\n"
            "<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. Διαθέτει ελαστική βάση που εφαρμόζει σε περίμετρο κεφαλής από 42 έως 63 εκ. Εύκολη στη χρήση — φτιαγμένη για να αντέχει χρόνια.</p>\n"
            "<ul>\n<li>Στυλ: κοντή γκρι περούκα — φυσικό αποτέλεσμα</li>\n"
            "<li>Κατάλληλη για: θέατρο, cosplay, Halloween, χαρακτήρες ρόλου, μεταμφιέσεις</li>\n"
            "<li>Ελαστική βάση: εφαρμόζει σε περίμετρο κεφαλής 42–63 εκ.</li>\n"
            "<li>Κατασκευάζεται στην Ελλάδα — διαθέσιμη κατά παραγγελία σε ειδικά μεγέθη</li>\n</ul>"
        ),
        short_en="<p>Short gray wig — Mark. Natural look. Handmade in Greece. Elastic base, fits all.</p>",
        short_el="<p>Κοντή γκρι περούκα — Μαρκ. Φυσικό αποτέλεσμα. Φτιάχνεται στην Ελλάδα. Ελαστική βάση.</p>",
        meta_en="Mark Short Gray Wig | Handmade in Greece | Alegro Athens",
        meta_el="Μαρκ Κοντή Γκρι Περούκα | Alegro Αθήνα",
    ),

    # 120 — STEFANY BLACK AND RED
    120: dict(
        desc_en=(
            "<p>The <strong>Stefany Black and Red Wig</strong> is a bold two-tone wig combining deep black with vivid red — "
            "a striking contrast that makes an immediate impression. A single style with a strong personality, "
            "perfect for cosplay, Halloween, and any occasion where you want a truly eye-catching look.</p>\n"
            "<p>Made in our workshop in Athens, Greece. Features a comfortable elastic base that fits head circumferences from 42 to 63 cm. Easy to wear — built to last for years.</p>\n"
            "<ul>\n<li>Style: two-tone wig — black and red</li>\n"
            "<li>Ideal for: cosplay, Halloween, carnival, fantasy costume</li>\n"
            "<li>Elastic base: fits 42–63 cm head circumference</li>\n"
            "<li>Made in Greece — custom sizes available on request</li>\n</ul>"
        ),
        desc_el=(
            "<p>Η <strong>Περούκα Στέφανυ Μαύρη και Κόκκινη</strong> είναι μια τολμηρή δίχρωμη περούκα που συνδυάζει βαθύ μαύρο με ζωηρό κόκκινο — "
            "εντυπωσιακή αντίθεση που τραβάει αμέσως το βλέμμα. Μοναδικό στυλ με δυναμική προσωπικότητα, "
            "ιδανικό για cosplay, Halloween και κάθε στιγμή που θέλετε να ξεχωρίζετε.</p>\n"
            "<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. Διαθέτει ελαστική βάση που εφαρμόζει σε περίμετρο κεφαλής από 42 έως 63 εκ. Εύκολη στη χρήση — φτιαγμένη για να αντέχει χρόνια.</p>\n"
            "<ul>\n<li>Στυλ: δίχρωμη περούκα — μαύρο και κόκκινο</li>\n"
            "<li>Κατάλληλη για: cosplay, Halloween, αποκριές, φαντασιακή στολή</li>\n"
            "<li>Ελαστική βάση: εφαρμόζει σε περίμετρο κεφαλής 42–63 εκ.</li>\n"
            "<li>Κατασκευάζεται στην Ελλάδα — διαθέσιμη κατά παραγγελία σε ειδικά μεγέθη</li>\n</ul>"
        ),
        short_en="<p>Two-tone black and red wig — Stefany. Bold contrast. Handmade in Greece. Elastic base, fits all.</p>",
        short_el="<p>Δίχρωμη μαύρη και κόκκινη περούκα — Στέφανυ. Τολμηρή αντίθεση. Φτιάχνεται στην Ελλάδα. Ελαστική βάση.</p>",
        meta_en="Stefany Black Red Two-Tone Wig | Handmade in Greece | Alegro Athens",
        meta_el="Στέφανυ Μαύρη Κόκκινη Δίχρωμη Περούκα | Alegro Αθήνα",
    ),

    # 121 — STEFANY PLATINUM BLONDE
    121: dict(
        desc_en=(
            "<p>The <strong>Stefany Platinum Blonde Wig</strong> is a striking wig in luminous platinum blonde — "
            "a cool, high-impact colour that gives an elegant and eye-catching result. "
            "Perfect for cosplay, Halloween, carnival, and any occasion where platinum blonde makes a statement.</p>\n"
            "<p>Made in our workshop in Athens, Greece. Features a comfortable elastic base that fits head circumferences from 42 to 63 cm. Easy to wear — built to last for years.</p>\n"
            "<ul>\n<li>Style: platinum blonde wig — cool and luminous</li>\n"
            "<li>Ideal for: cosplay, Halloween, carnival, fantasy costume</li>\n"
            "<li>Elastic base: fits 42–63 cm head circumference</li>\n"
            "<li>Made in Greece — custom sizes available on request</li>\n</ul>"
        ),
        desc_el=(
            "<p>Η <strong>Περούκα Στέφανυ Πλατινέ Ξανθιά</strong> είναι μια εντυπωσιακή περούκα σε φωτεινό πλατινέ ξανθό — "
            "δροσερό, ζωηρό χρώμα που δίνει κομψό και εντυπωσιακό αποτέλεσμα. "
            "Ιδανική για cosplay, Halloween, αποκριές και κάθε στιγμή που το πλατινέ ξανθό κάνει τη διαφορά.</p>\n"
            "<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. Διαθέτει ελαστική βάση που εφαρμόζει σε περίμετρο κεφαλής από 42 έως 63 εκ. Εύκολη στη χρήση — φτιαγμένη για να αντέχει χρόνια.</p>\n"
            "<ul>\n<li>Στυλ: πλατινέ ξανθιά περούκα — φωτεινή και κομψή</li>\n"
            "<li>Κατάλληλη για: cosplay, Halloween, αποκριές, φαντασιακή στολή</li>\n"
            "<li>Ελαστική βάση: εφαρμόζει σε περίμετρο κεφαλής 42–63 εκ.</li>\n"
            "<li>Κατασκευάζεται στην Ελλάδα — διαθέσιμη κατά παραγγελία σε ειδικά μεγέθη</li>\n</ul>"
        ),
        short_en="<p>Platinum blonde wig — Stefany. Luminous and striking. Handmade in Greece. Elastic base, fits all.</p>",
        short_el="<p>Πλατινέ ξανθιά περούκα — Στέφανυ. Φωτεινή και εντυπωσιακή. Φτιάχνεται στην Ελλάδα. Ελαστική βάση.</p>",
        meta_en="Stefany Platinum Blonde Wig | Handmade in Greece | Alegro Athens",
        meta_el="Στέφανυ Πλατινέ Ξανθιά Περούκα | Alegro Αθήνα",
    ),

    # 122-125 — NATALIE (long with side part)
    122: natalie("Black",       "Μαύρη",           "μαύρο"),
    123: natalie("Dark Blonde", "Σκούρα Ξανθιά",   "σκούρο ξανθό"),
    124: natalie("Honey Blonde","Μελί",             "μελί"),
    125: natalie("Dark Auburn", "Σκούρα Ακαζού",   "σκούρο ακαζού"),

    # 126-128 — ARIADNE (long with small braids)
    126: ariadne("Black",  "Μαύρη",   "μαύρο"),
    127: ariadne("Red",    "Κόκκινη", "κόκκινο"),
    128: ariadne("Blonde", "Ξανθιά",  "ξανθό", center_part=True),

    # 129-131 — NORA (medium)
    129: nora("Black",  "Μαύρη",   "μαύρο"),
    130: nora("Blonde", "Ξανθιά",  "ξανθό"),
    131: nora("Auburn", "Ακαζού",  "ακαζού"),

    # 132-134 — STELLA (long curly)
    132: stella("Black",  "Μαύρη",   "μαύρο"),
    133: stella("Blonde", "Ξανθιά",  "ξανθό"),
    134: stella("Brown",  "Καστανή", "καστανό"),

    # 135-137 — PEGGY (long curly with headband)
    135: peggy("Black",  "Μαύρη",   "μαύρο"),
    136: peggy("Blonde", "Ξανθιά",  "ξανθό"),
    137: peggy("Auburn", "Ακαζού",  "ακαζού"),

    # 139-142 — DAPHNE (voluminous)
    139: daphne("Black",       "Μαύρη",           "μαύρο"),
    140: daphne("Blonde",      "Ξανθιά",          "ξανθό"),
    141: daphne("Red",         "Κόκκινη",         "κόκκινο"),
    142: daphne("Light Brown", "Ανοιχτή Καστανή", "ανοιχτό καστανό"),

    # 143-144 — SAMANTHA (long straight)
    143: samantha("Blonde", "Ξανθιά", "ξανθό"),
    144: samantha("Black",  "Μαύρη",  "μαύρο"),

    # 145 — ANCIENT GREEK GIRL BLACK
    145: dict(
        desc_en=(
            "<p>The <strong>Ancient Greek Girl Black Wig</strong> is a tall, upswept theatrical wig styled in the manner "
            "of ancient Greek women, complete with a decorative headband. An authentic and elegant look for historical "
            "theatre, school celebrations of the 25th March, cultural events, and costume parties.</p>\n"
            "<p>Made in our workshop in Athens, Greece. Features a comfortable elastic base that fits head circumferences from 42 to 63 cm. Easy to wear — built to last for years.</p>\n"
            "<ul>\n<li>Style: tall upswept black wig with headband — ancient Greek style</li>\n"
            "<li>Ideal for: theatre, 25th March celebrations, school events, historical costume</li>\n"
            "<li>Elastic base: fits 42–63 cm head circumference</li>\n"
            "<li>Made in Greece — custom sizes available on request</li>\n</ul>"
        ),
        desc_el=(
            "<p>Η <strong>Ψηλή Μαύρη Περούκα Αρχαίας Ελληνίδας</strong> είναι μια ψηλή θεατρική περούκα με ανεβασμένο χτένισμα "
            "στο ύφος της αρχαίας Ελληνίδας, με διακοσμητική κορδέλα. Αυθεντική και κομψή εμφάνιση για ιστορικό θέατρο, "
            "σχολικές εορτές της 25ης Μαρτίου, πολιτιστικές εκδηλώσεις και αποκριάτικες παρελάσεις.</p>\n"
            "<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. Διαθέτει ελαστική βάση που εφαρμόζει σε περίμετρο κεφαλής από 42 έως 63 εκ. Εύκολη στη χρήση — φτιαγμένη για να αντέχει χρόνια.</p>\n"
            "<ul>\n<li>Στυλ: ψηλή μαύρη περούκα με κορδέλα — αρχαία ελληνική εμφάνιση</li>\n"
            "<li>Κατάλληλη για: θέατρο, 25η Μαρτίου, σχολικές εκδηλώσεις, ιστορική στολή</li>\n"
            "<li>Ελαστική βάση: εφαρμόζει σε περίμετρο κεφαλής 42–63 εκ.</li>\n"
            "<li>Κατασκευάζεται στην Ελλάδα — διαθέσιμη κατά παραγγελία σε ειδικά μεγέθη</li>\n</ul>"
        ),
        short_en="<p>Tall upswept black theatrical wig with headband — Ancient Greek woman style. Handmade in Greece. Elastic base.</p>",
        short_el="<p>Ψηλή μαύρη θεατρική περούκα αρχαίας Ελληνίδας με κορδέλα. Φτιάχνεται στην Ελλάδα. Ελαστική βάση.</p>",
        meta_en="Ancient Greek Girl Black Theatrical Wig with Headband | Handmade in Greece | Alegro Athens",
        meta_el="Ψηλή Μαύρη Περούκα Αρχαίας Ελληνίδας με Κορδέλα | Alegro Αθήνα",
    ),

    # 146 — ANCIENT GREEK GIRL BLONDE
    146: dict(
        desc_en=(
            "<p>The <strong>Ancient Greek Girl Blonde Wig</strong> is a tall, upswept theatrical wig styled in the manner "
            "of ancient Greek women, complete with a decorative headband. An authentic and elegant look for historical "
            "theatre, school celebrations of the 25th March, cultural events, and costume parties.</p>\n"
            "<p>Made in our workshop in Athens, Greece. Features a comfortable elastic base that fits head circumferences from 42 to 63 cm. Easy to wear — built to last for years.</p>\n"
            "<ul>\n<li>Style: tall upswept blonde wig with headband — ancient Greek style</li>\n"
            "<li>Ideal for: theatre, 25th March celebrations, school events, historical costume</li>\n"
            "<li>Elastic base: fits 42–63 cm head circumference</li>\n"
            "<li>Made in Greece — custom sizes available on request</li>\n</ul>"
        ),
        desc_el=(
            "<p>Η <strong>Ψηλή Ξανθιά Περούκα Αρχαίας Ελληνίδας</strong> είναι μια ψηλή θεατρική περούκα με ανεβασμένο χτένισμα "
            "στο ύφος της αρχαίας Ελληνίδας, με διακοσμητική κορδέλα. Αυθεντική και κομψή εμφάνιση για ιστορικό θέατρο, "
            "σχολικές εορτές της 25ης Μαρτίου, πολιτιστικές εκδηλώσεις και αποκριάτικες παρελάσεις.</p>\n"
            "<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. Διαθέτει ελαστική βάση που εφαρμόζει σε περίμετρο κεφαλής από 42 έως 63 εκ. Εύκολη στη χρήση — φτιαγμένη για να αντέχει χρόνια.</p>\n"
            "<ul>\n<li>Στυλ: ψηλή ξανθιά περούκα με κορδέλα — αρχαία ελληνική εμφάνιση</li>\n"
            "<li>Κατάλληλη για: θέατρο, 25η Μαρτίου, σχολικές εκδηλώσεις, ιστορική στολή</li>\n"
            "<li>Ελαστική βάση: εφαρμόζει σε περίμετρο κεφαλής 42–63 εκ.</li>\n"
            "<li>Κατασκευάζεται στην Ελλάδα — διαθέσιμη κατά παραγγελία σε ειδικά μεγέθη</li>\n</ul>"
        ),
        short_en="<p>Tall upswept blonde theatrical wig with headband — Ancient Greek woman style. Handmade in Greece. Elastic base.</p>",
        short_el="<p>Ψηλή ξανθιά θεατρική περούκα αρχαίας Ελληνίδας με κορδέλα. Φτιάχνεται στην Ελλάδα. Ελαστική βάση.</p>",
        meta_en="Ancient Greek Girl Blonde Theatrical Wig with Headband | Handmade in Greece | Alegro Athens",
        meta_el="Ψηλή Ξανθιά Περούκα Αρχαίας Ελληνίδας με Κορδέλα | Alegro Αθήνα",
    ),

    # 147 — COUNT: white with ponytail (aristocratic/noble character)
    147: dict(
        desc_en=(
            "<p>The <strong>Count White Wig with Ponytail</strong> is a theatrical wig in powdered white, styled with a neat "
            "ponytail — the classic look of 18th-century European nobility. Perfect for Count, Marquis, or aristocratic "
            "character roles in theatre, carnival, and fancy dress events.</p>\n"
            "<p>Made in our workshop in Athens, Greece. Features a comfortable elastic base that fits head circumferences from 42 to 63 cm. Easy to wear — built to last for years.</p>\n"
            "<ul>\n<li>Style: white powdered wig with ponytail — 18th-century aristocratic</li>\n"
            "<li>Ideal for: theatre, carnival, fancy dress, Count / Marquis character</li>\n"
            "<li>Elastic base: fits 42–63 cm head circumference</li>\n"
            "<li>Made in Greece — custom sizes available on request</li>\n</ul>"
        ),
        desc_el=(
            "<p>Η <strong>Λευκή Περούκα Κόμης με Αλογοουρά</strong> είναι μια θεατρική περούκα σε πουδρέ λευκό, με τακτοποιημένη αλογοουρά — "
            "κλασική εμφάνιση της ευρωπαϊκής αριστοκρατίας του 18ου αιώνα. Ιδανική για ρόλους Κόμη, Μαρκήσιου ή ευγενούς "
            "σε θεατρικές παραστάσεις, αποκριές και αποκριάτικες εκδηλώσεις.</p>\n"
            "<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. Διαθέτει ελαστική βάση που εφαρμόζει σε περίμετρο κεφαλής από 42 έως 63 εκ. Εύκολη στη χρήση — φτιαγμένη για να αντέχει χρόνια.</p>\n"
            "<ul>\n<li>Στυλ: πουδρέ λευκή περούκα με αλογοουρά — αριστοκρατική, 18ος αιώνας</li>\n"
            "<li>Κατάλληλη για: θέατρο, αποκριές, μεταμφιέσεις, χαρακτήρας Κόμη / Μαρκήσιου</li>\n"
            "<li>Ελαστική βάση: εφαρμόζει σε περίμετρο κεφαλής 42–63 εκ.</li>\n"
            "<li>Κατασκευάζεται στην Ελλάδα — διαθέσιμη κατά παραγγελία σε ειδικά μεγέθη</li>\n</ul>"
        ),
        short_en="<p>White powdered wig with ponytail — Count. 18th-century aristocratic style. Handmade in Greece. Elastic base.</p>",
        short_el="<p>Λευκή πουδρέ περούκα με αλογοουρά — Κόμης. Αριστοκρατικό στυλ 18ου αιώνα. Φτιάχνεται στην Ελλάδα.</p>",
        meta_en="Count White Theatrical Wig with Ponytail | Handmade in Greece | Alegro Athens",
        meta_el="Κόμης Λευκή Θεατρική Περούκα με Αλογοουρά | Alegro Αθήνα",
    ),

    # 148 — JUDGE: long gray
    148: dict(
        desc_en=(
            "<p>The <strong>Judge Long Gray Wig</strong> is a theatrical wig in the classic style of a court judge — "
            "long, gray, and formal. The traditional judge's wig as worn in British and European courts, perfect for "
            "theatre, legal-themed fancy dress, carnival, and costume events.</p>\n"
            "<p>Made in our workshop in Athens, Greece. Features a comfortable elastic base that fits head circumferences from 42 to 63 cm. Easy to wear — built to last for years.</p>\n"
            "<ul>\n<li>Style: long gray judge's wig — formal and traditional</li>\n"
            "<li>Ideal for: theatre, carnival, fancy dress, judge / barrister character</li>\n"
            "<li>Elastic base: fits 42–63 cm head circumference</li>\n"
            "<li>Made in Greece — custom sizes available on request</li>\n</ul>"
        ),
        desc_el=(
            "<p>Η <strong>Γκρι Μακριά Περούκα Δικαστής</strong> είναι μια θεατρική περούκα στο κλασικό στυλ δικαστή — "
            "μακριά, γκρι και επίσημη. Το παραδοσιακό ύφος των δικαστών όπως φοριέται στα βρετανικά και ευρωπαϊκά δικαστήρια, "
            "ιδανική για θέατρο, νομικές μεταμφιέσεις, αποκριές και εκδηλώσεις κοστουμιών.</p>\n"
            "<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. Διαθέτει ελαστική βάση που εφαρμόζει σε περίμετρο κεφαλής από 42 έως 63 εκ. Εύκολη στη χρήση — φτιαγμένη για να αντέχει χρόνια.</p>\n"
            "<ul>\n<li>Στυλ: μακριά γκρι περούκα δικαστή — επίσημη και παραδοσιακή</li>\n"
            "<li>Κατάλληλη για: θέατρο, αποκριές, μεταμφιέσεις, χαρακτήρας δικαστή</li>\n"
            "<li>Ελαστική βάση: εφαρμόζει σε περίμετρο κεφαλής 42–63 εκ.</li>\n"
            "<li>Κατασκευάζεται στην Ελλάδα — διαθέσιμη κατά παραγγελία σε ειδικά μεγέθη</li>\n</ul>"
        ),
        short_en="<p>Long gray theatrical judge's wig. Classic court style. Handmade in Greece. Elastic base, fits all.</p>",
        short_el="<p>Γκρι μακριά θεατρική περούκα δικαστή. Κλασικό επίσημο στυλ. Φτιάχνεται στην Ελλάδα. Ελαστική βάση.</p>",
        meta_en="Judge Long Gray Theatrical Wig | Handmade in Greece | Alegro Athens",
        meta_el="Δικαστής Γκρι Μακριά Θεατρική Περούκα | Alegro Αθήνα",
    ),
}

# ── Session factory ───────────────────────────────────────────────────────────

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

        existing = get_textarea(html, 'product[description][description][1]') or \
                   get_textarea(html, 'product[description][description][2]')
        if existing.strip():
            return pid, 'SKIP', 'already has description'

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
log(f'All {WORKERS} sessions ready. Processing {len(PRODUCTS)} products.\n')

pids = sorted(PRODUCTS.keys())
tasks = [(i % WORKERS, pid) for i, pid in enumerate(pids)]

def worker(args):
    idx, pid = args
    s, cat = sessions[idx]
    return update_product(s, cat, pid, PRODUCTS[pid])

ok = skip = fail = done = 0
with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    futures = {ex.submit(worker, t): t[1] for t in tasks}
    for fut in as_completed(futures):
        pid, status, msg = fut.result()
        done += 1
        if status == 'OK':
            ok += 1
            log(f'[{done:2d}/{len(pids)}] PID {pid}: OK')
        elif status == 'SKIP':
            skip += 1
            log(f'[{done:2d}/{len(pids)}] PID {pid}: SKIP — {msg}')
        else:
            fail += 1
            log(f'[{done:2d}/{len(pids)}] PID {pid}: {status} — {msg}')

log(f'\nDone — {ok} written, {skip} skipped, {fail} failed')
