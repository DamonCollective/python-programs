#!/usr/bin/env python3
"""
Batch 2: PIDs 88-117 (30 products)
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

def sylvia(en_color, el_fem, el_neuter):
    en = en_color.lower(); el_adj = el_fem.lower()
    return dict(
        desc_en=(
            f"<p>The <strong>Sylvia {en_color} Wig</strong> is a long, straight wig with a clean center part — "
            f"a timeless, romantic style with a natural-looking flow. Available in many colours, here in {en}. "
            f"A versatile choice for cosplay, fancy dress, Halloween, carnival, and any occasion that calls for long, beautiful hair.</p>\n"
            f"<p>Made in our workshop in Athens, Greece. Features a comfortable elastic base that fits head circumferences from 42 to 63 cm. Easy to wash and comb — built to last for years.</p>\n"
            f"<ul>\n<li>Style: long straight hair with center part — {en}</li>\n"
            f"<li>Ideal for: cosplay, Halloween, carnival, retro / vintage look, fantasy costume</li>\n"
            f"<li>Elastic base: fits 42–63 cm head circumference</li>\n"
            f"<li>Made in Greece — custom sizes available on request</li>\n</ul>"
        ),
        desc_el=(
            f"<p>Η <strong>Περούκα Σύλβια {el_fem}</strong> είναι μια μακριά, ίσια περούκα με χωρίστρα στη μέση — "
            f"διαχρονικό, ρομαντικό στυλ με φυσικό αποτέλεσμα. Σε πολλά χρώματα, εδώ σε {el_neuter}. "
            f"Ευέλικτη επιλογή για cosplay, μεταμφιέσεις, απόκριες, Halloween και κάθε στιγμή που θέλετε πλούσια, μακριά μαλλιά.</p>\n"
            f"<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. Διαθέτει ελαστική βάση που εφαρμόζει σε περίμετρο κεφαλής από 42 έως 63 εκ. Πλένεται και χτενίζεται εύκολα — φτιαγμένη για να αντέχει χρόνια.</p>\n"
            f"<ul>\n<li>Στυλ: μακριά ίσια με χωρίστρα στη μέση — {el_adj}</li>\n"
            f"<li>Κατάλληλη για: cosplay, Halloween, απόκριες, retro / vintage look, φαντασιακή στολή</li>\n"
            f"<li>Ελαστική βάση: εφαρμόζει σε περίμετρο κεφαλής 42–63 εκ.</li>\n"
            f"<li>Κατασκευάζεται στην Ελλάδα — διαθέσιμη κατά παραγγελία σε ειδικά μεγέθη</li>\n</ul>"
        ),
        short_en=f"<p>Long straight {en} wig with center part — Sylvia style. Handmade in Greece. Elastic base, fits all.</p>",
        short_el=f"<p>Μακριά ίσια {el_adj} περούκα με χωρίστρα στη μέση — Σύλβια. Φτιάχνεται στην Ελλάδα. Ελαστική βάση.</p>",
        meta_en=f"Sylvia {en_color} Long Straight Wig Center Part | Handmade in Greece | Alegro Athens",
        meta_el=f"Σύλβια {el_fem} Μακριά Ίσια Περούκα Χωρίστρα Μέση | Alegro Αθήνα",
    )

def danae(en_color, el_fem, el_neuter):
    en = en_color.lower(); el_adj = el_fem.lower()
    return dict(
        desc_en=(
            f"<p>The <strong>Danae {en_color} Wig</strong> is a long, straight wig with a sweeping side part — "
            f"an elegant, feminine style that adds instant grace to any look. Available in many colours, here in {en}. "
            f"A beautiful choice for cosplay, fancy dress, Halloween, and carnival.</p>\n"
            f"<p>Made in our workshop in Athens, Greece. Features a comfortable elastic base that fits head circumferences from 42 to 63 cm. Easy to wash and comb — built to last for years.</p>\n"
            f"<ul>\n<li>Style: long straight hair with side part — {en}</li>\n"
            f"<li>Ideal for: cosplay, Halloween, carnival, retro / vintage look, fantasy costume</li>\n"
            f"<li>Elastic base: fits 42–63 cm head circumference</li>\n"
            f"<li>Made in Greece — custom sizes available on request</li>\n</ul>"
        ),
        desc_el=(
            f"<p>Η <strong>Περούκα Δανάη {el_fem}</strong> είναι μια μακριά, ίσια περούκα με χωρίστρα στο πλάι — "
            f"κομψό, θηλυκό στυλ που δίνει αμέσως χάρη σε κάθε εμφάνιση. Σε πολλά χρώματα, εδώ σε {el_neuter}. "
            f"Υπέροχη επιλογή για cosplay, μεταμφιέσεις, απόκριες και Halloween.</p>\n"
            f"<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. Διαθέτει ελαστική βάση που εφαρμόζει σε περίμετρο κεφαλής από 42 έως 63 εκ. Πλένεται και χτενίζεται εύκολα — φτιαγμένη για να αντέχει χρόνια.</p>\n"
            f"<ul>\n<li>Στυλ: μακριά ίσια με χωρίστρα στο πλάι — {el_adj}</li>\n"
            f"<li>Κατάλληλη για: cosplay, Halloween, απόκριες, retro / vintage look, φαντασιακή στολή</li>\n"
            f"<li>Ελαστική βάση: εφαρμόζει σε περίμετρο κεφαλής 42–63 εκ.</li>\n"
            f"<li>Κατασκευάζεται στην Ελλάδα — διαθέσιμη κατά παραγγελία σε ειδικά μεγέθη</li>\n</ul>"
        ),
        short_en=f"<p>Long straight {en} wig with side part — Danae style. Handmade in Greece. Elastic base, fits all.</p>",
        short_el=f"<p>Μακριά ίσια {el_adj} περούκα με χωρίστρα στο πλάι — Δανάη. Φτιάχνεται στην Ελλάδα. Ελαστική βάση.</p>",
        meta_en=f"Danae {en_color} Long Straight Wig Side Part | Handmade in Greece | Alegro Athens",
        meta_el=f"Δανάη {el_fem} Μακριά Ίσια Περούκα Χωρίστρα Πλάι | Alegro Αθήνα",
    )

def pauline(en_color, el_fem, el_neuter):
    en = en_color.lower(); el_adj = el_fem.lower()
    return dict(
        desc_en=(
            f"<p>The <strong>Pauline {en_color} Wig</strong> is a medium-length, layered wig with a neat fringe — "
            f"a lively, voluminous style that frames the face beautifully. Available in many colours, here in {en}. "
            f"A great choice for cosplay, fancy dress, Halloween, retro looks, and any occasion that calls for fun, textured hair.</p>\n"
            f"<p>Made in our workshop in Athens, Greece. Features a comfortable elastic base that fits head circumferences from 42 to 63 cm. Easy to wash and comb — built to last for years.</p>\n"
            f"<ul>\n<li>Style: medium-length layered hair with fringe — {en}</li>\n"
            f"<li>Ideal for: cosplay, Halloween, carnival, retro / vintage look</li>\n"
            f"<li>Elastic base: fits 42–63 cm head circumference</li>\n"
            f"<li>Made in Greece — custom sizes available on request</li>\n</ul>"
        ),
        desc_el=(
            f"<p>Η <strong>Περούκα Πωλίν {el_fem}</strong> είναι μια μεσαία φιλαριστή περούκα με φράντζα — "
            f"ζωντανό, ογκώδες στυλ που πλαισιώνει όμορφα το πρόσωπο. Σε πολλά χρώματα, εδώ σε {el_neuter}. "
            f"Ωραία επιλογή για cosplay, μεταμφιέσεις, απόκριες, Halloween και retro εμφανίσεις.</p>\n"
            f"<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. Διαθέτει ελαστική βάση που εφαρμόζει σε περίμετρο κεφαλής από 42 έως 63 εκ. Πλένεται και χτενίζεται εύκολα — φτιαγμένη για να αντέχει χρόνια.</p>\n"
            f"<ul>\n<li>Στυλ: μεσαία φιλαριστή με φράντζα — {el_adj}</li>\n"
            f"<li>Κατάλληλη για: cosplay, Halloween, απόκριες, retro / vintage look</li>\n"
            f"<li>Ελαστική βάση: εφαρμόζει σε περίμετρο κεφαλής 42–63 εκ.</li>\n"
            f"<li>Κατασκευάζεται στην Ελλάδα — διαθέσιμη κατά παραγγελία σε ειδικά μεγέθη</li>\n</ul>"
        ),
        short_en=f"<p>Medium layered {en} wig with fringe — Pauline style. Handmade in Greece. Elastic base, fits all.</p>",
        short_el=f"<p>Μεσαία φιλαριστή {el_adj} περούκα με φράντζα — Πωλίν. Φτιάχνεται στην Ελλάδα. Ελαστική βάση.</p>",
        meta_en=f"Pauline {en_color} Medium Layered Wig Fringe | Handmade in Greece | Alegro Athens",
        meta_el=f"Πωλίν {el_fem} Μεσαία Φιλαριστή Περούκα Φράντζα | Alegro Αθήνα",
    )

def john(en_color, el_fem, el_neuter):
    en = en_color.lower(); el_adj = el_fem.lower()
    return dict(
        desc_en=(
            f"<p>The <strong>John {en_color} Wig</strong> is a short, natural-looking wig designed for men — "
            f"a classic everyday style in {en}. Comfortable and convincing, it suits theatrical performances, "
            f"cosplay, fancy dress, and Halloween equally well.</p>\n"
            f"<p>Made in our workshop in Athens, Greece. Features a comfortable elastic base that fits head circumferences from 42 to 63 cm. Easy to wear — built to last for years.</p>\n"
            f"<ul>\n<li>Style: short natural men's wig — {en}</li>\n"
            f"<li>Ideal for: theatre, cosplay, Halloween, carnival, fancy dress</li>\n"
            f"<li>Elastic base: fits 42–63 cm head circumference</li>\n"
            f"<li>Made in Greece — custom sizes available on request</li>\n</ul>"
        ),
        desc_el=(
            f"<p>Η <strong>Περούκα Τζον {el_fem}</strong> είναι μια κοντή, φυσικού τύπου ανδρική περούκα — "
            f"κλασικό, καθημερινό στυλ σε {el_neuter}. Άνετη και πειστική, κατάλληλη για θεατρικές παραστάσεις, "
            f"cosplay, μεταμφιέσεις και Halloween.</p>\n"
            f"<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. Διαθέτει ελαστική βάση που εφαρμόζει σε περίμετρο κεφαλής από 42 έως 63 εκ. Εύκολη στη χρήση — φτιαγμένη για να αντέχει χρόνια.</p>\n"
            f"<ul>\n<li>Στυλ: κοντή ανδρική — {el_adj}</li>\n"
            f"<li>Κατάλληλη για: θέατρο, cosplay, Halloween, απόκριες, μεταμφιέσεις</li>\n"
            f"<li>Ελαστική βάση: εφαρμόζει σε περίμετρο κεφαλής 42–63 εκ.</li>\n"
            f"<li>Κατασκευάζεται στην Ελλάδα — διαθέσιμη κατά παραγγελία σε ειδικά μεγέθη</li>\n</ul>"
        ),
        short_en=f"<p>Short natural men's wig — John style, {en}. Handmade in Greece. Elastic base, fits all.</p>",
        short_el=f"<p>Κοντή ανδρική περούκα {el_adj} — Τζον. Φτιάχνεται στην Ελλάδα. Ελαστική βάση, εφαρμόζει σε όλους.</p>",
        meta_en=f"John {en_color} Short Men's Wig | Handmade in Greece | Alegro Athens",
        meta_el=f"Τζον {el_fem} Κοντή Ανδρική Περούκα | Alegro Αθήνα",
    )

def jim(en_color, el_fem, el_neuter):
    en = en_color.lower(); el_adj = el_fem.lower()
    return dict(
        desc_en=(
            f"<p>The <strong>Jim {en_color} Wig</strong> is a distinctive wig featuring a styled ponytail — "
            f"a characterful look perfect for theatrical roles, cosplay characters, and creative fancy dress. "
            f"In {en}, with a neat ponytail that adds an authentic touch to any costume.</p>\n"
            f"<p>Made in our workshop in Athens, Greece. Features a comfortable elastic base that fits head circumferences from 42 to 63 cm. Easy to wear — built to last for years.</p>\n"
            f"<ul>\n<li>Style: wig with ponytail — {en}</li>\n"
            f"<li>Ideal for: theatre, cosplay, Halloween, carnival, character roles</li>\n"
            f"<li>Elastic base: fits 42–63 cm head circumference</li>\n"
            f"<li>Made in Greece — custom sizes available on request</li>\n</ul>"
        ),
        desc_el=(
            f"<p>Η <strong>Περούκα Τζιμ {el_fem}</strong> είναι μια χαρακτηριστική περούκα με κοτσίδα — "
            f"ξεχωριστό στυλ ιδανικό για θεατρικούς ρόλους, cosplay χαρακτήρες και δημιουργικές μεταμφιέσεις. "
            f"Σε {el_neuter}, με τακτοποιημένη κοτσίδα που δίνει αυθεντική πινελιά σε κάθε στολή.</p>\n"
            f"<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. Διαθέτει ελαστική βάση που εφαρμόζει σε περίμετρο κεφαλής από 42 έως 63 εκ. Εύκολη στη χρήση — φτιαγμένη για να αντέχει χρόνια.</p>\n"
            f"<ul>\n<li>Στυλ: περούκα με κοτσίδα — {el_adj}</li>\n"
            f"<li>Κατάλληλη για: θέατρο, cosplay, Halloween, απόκριες, χαρακτήρες ρόλου</li>\n"
            f"<li>Ελαστική βάση: εφαρμόζει σε περίμετρο κεφαλής 42–63 εκ.</li>\n"
            f"<li>Κατασκευάζεται στην Ελλάδα — διαθέσιμη κατά παραγγελία σε ειδικά μεγέθη</li>\n</ul>"
        ),
        short_en=f"<p>{en_color} wig with ponytail — Jim style. Handmade in Greece. Elastic base, fits all.</p>",
        short_el=f"<p>{el_fem} περούκα με κοτσίδα — Τζιμ. Φτιάχνεται στην Ελλάδα. Ελαστική βάση, εφαρμόζει σε όλους.</p>",
        meta_en=f"Jim {en_color} Wig with Ponytail | Handmade in Greece | Alegro Athens",
        meta_el=f"Τζιμ {el_fem} Περούκα με Κοτσίδα | Alegro Αθήνα",
    )

# ── Product catalogue ─────────────────────────────────────────────────────────

PRODUCTS = {

    # 88 — Sylvia Blue with Streaks
    88: sylvia("Blue with Streaks", "Μπλε με Ανταύγειες", "μπλε με ανταύγειες"),

    # 89 — Valeria: platinum blonde with black streaks
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
            "εντυπωσιακή αντίθεση που δίνει δραματικό, τολμηρό αποτέλεσμα. Μοναδικό στυλ με ξεχωριστή προσωπικότητα, "
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

    # 90 — FIRE: long red
    90: dict(
        desc_en=(
            "<p>The <strong>Fire Wig</strong> is a long, flowing red wig — vivid, intense, and impossible to ignore. "
            "Inspired by the elemental force of fire, this wig brings drama and energy to any costume. "
            "An outstanding choice for Halloween, carnival, fantasy cosplay, and theatrical performances.</p>\n"
            "<p>Made in our workshop in Athens, Greece. Features a comfortable elastic base that fits head circumferences from 42 to 63 cm. Easy to wash and comb — built to last for years.</p>\n"
            "<ul>\n<li>Style: long flowing red wig — bold and dramatic</li>\n"
            "<li>Ideal for: Halloween, cosplay, carnival, theatre, fantasy costume</li>\n"
            "<li>Elastic base: fits 42–63 cm head circumference</li>\n"
            "<li>Made in Greece — custom sizes available on request</li>\n</ul>"
        ),
        desc_el=(
            "<p>Η <strong>Περούκα Φωτιά</strong> είναι μια μακριά, ρέουσα κόκκινη περούκα — ζωηρή, έντονη και αδύνατο να περάσει απαρατήρητη. "
            "Εμπνευσμένη από το στοιχείο της φωτιάς, αυτή η περούκα φέρνει δράμα και ενέργεια σε κάθε στολή. "
            "Εξαιρετική επιλογή για Halloween, αποκριές, fantasy cosplay και θεατρικές παραστάσεις.</p>\n"
            "<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. Διαθέτει ελαστική βάση που εφαρμόζει σε περίμετρο κεφαλής από 42 έως 63 εκ. Πλένεται και χτενίζεται εύκολα — φτιαγμένη για να αντέχει χρόνια.</p>\n"
            "<ul>\n<li>Στυλ: μακριά κόκκινη περούκα — τολμηρή και εντυπωσιακή</li>\n"
            "<li>Κατάλληλη για: Halloween, cosplay, αποκριές, θέατρο, φαντασιακή στολή</li>\n"
            "<li>Ελαστική βάση: εφαρμόζει σε περίμετρο κεφαλής 42–63 εκ.</li>\n"
            "<li>Κατασκευάζεται στην Ελλάδα — διαθέσιμη κατά παραγγελία σε ειδικά μεγέθη</li>\n</ul>"
        ),
        short_en="<p>Long vivid red wig — Fire. Bold elemental style. Handmade in Greece. Elastic base, fits all.</p>",
        short_el="<p>Μακριά ζωηρή κόκκινη περούκα — Φωτιά. Τολμηρό στυλ. Φτιάχνεται στην Ελλάδα. Ελαστική βάση.</p>",
        meta_en="Fire Long Red Theatrical Wig | Handmade in Greece | Alegro Athens",
        meta_el="Φωτιά Μακριά Κόκκινη Θεατρική Περούκα | Alegro Αθήνα",
    ),

    # 91 — WIND: long white
    91: dict(
        desc_en=(
            "<p>The <strong>Wind Wig</strong> is a long, flowing white wig — light, ethereal, and effortlessly dramatic. "
            "Inspired by the elemental force of wind, it evokes a ghostly, mystical presence. "
            "Perfect for Halloween, fantasy cosplay, theatrical performances, and any costume calling for an otherworldly look.</p>\n"
            "<p>Made in our workshop in Athens, Greece. Features a comfortable elastic base that fits head circumferences from 42 to 63 cm. Easy to wash and comb — built to last for years.</p>\n"
            "<ul>\n<li>Style: long flowing white wig — ethereal and striking</li>\n"
            "<li>Ideal for: Halloween, cosplay, carnival, theatre, ghost / spirit costume</li>\n"
            "<li>Elastic base: fits 42–63 cm head circumference</li>\n"
            "<li>Made in Greece — custom sizes available on request</li>\n</ul>"
        ),
        desc_el=(
            "<p>Η <strong>Περούκα Αέρας</strong> είναι μια μακριά, ρέουσα λευκή περούκα — ελαφριά, αιθέρια και εντυπωσιακή. "
            "Εμπνευσμένη από το στοιχείο του αέρα, δίνει μια φαντασματική, μυστηριακή παρουσία. "
            "Ιδανική για Halloween, fantasy cosplay, θεατρικές παραστάσεις και κάθε στολή που χρειάζεται έναν υπερκόσμιο χαρακτήρα.</p>\n"
            "<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. Διαθέτει ελαστική βάση που εφαρμόζει σε περίμετρο κεφαλής από 42 έως 63 εκ. Πλένεται και χτενίζεται εύκολα — φτιαγμένη για να αντέχει χρόνια.</p>\n"
            "<ul>\n<li>Στυλ: μακριά λευκή περούκα — αιθέρια και εντυπωσιακή</li>\n"
            "<li>Κατάλληλη για: Halloween, cosplay, αποκριές, θέατρο, στολή φαντάσματος</li>\n"
            "<li>Ελαστική βάση: εφαρμόζει σε περίμετρο κεφαλής 42–63 εκ.</li>\n"
            "<li>Κατασκευάζεται στην Ελλάδα — διαθέσιμη κατά παραγγελία σε ειδικά μεγέθη</li>\n</ul>"
        ),
        short_en="<p>Long flowing white wig — Wind. Ethereal style. Handmade in Greece. Elastic base, fits all.</p>",
        short_el="<p>Μακριά ρέουσα λευκή περούκα — Αέρας. Αιθέριο στυλ. Φτιάχνεται στην Ελλάδα. Ελαστική βάση.</p>",
        meta_en="Wind Long White Theatrical Wig | Handmade in Greece | Alegro Athens",
        meta_el="Αέρας Μακριά Λευκή Θεατρική Περούκα | Alegro Αθήνα",
    ),

    # 92 — EARTH: long brown
    92: dict(
        desc_en=(
            "<p>The <strong>Earth Wig</strong> is a long, flowing brown wig — warm, natural, and grounded. "
            "Inspired by the elemental force of earth, it brings a rich, organic warmth to any costume. "
            "A versatile choice for cosplay, Halloween, fantasy events, and theatrical performances.</p>\n"
            "<p>Made in our workshop in Athens, Greece. Features a comfortable elastic base that fits head circumferences from 42 to 63 cm. Easy to wash and comb — built to last for years.</p>\n"
            "<ul>\n<li>Style: long flowing brown wig — warm and natural</li>\n"
            "<li>Ideal for: cosplay, Halloween, carnival, theatre, fantasy costume</li>\n"
            "<li>Elastic base: fits 42–63 cm head circumference</li>\n"
            "<li>Made in Greece — custom sizes available on request</li>\n</ul>"
        ),
        desc_el=(
            "<p>Η <strong>Περούκα Γη</strong> είναι μια μακριά, ρέουσα καστανή περούκα — ζεστή, φυσική και γεμάτη χαρακτήρα. "
            "Εμπνευσμένη από το στοιχείο της γης, προσθέτει οργανική θαλπωρή σε κάθε στολή. "
            "Ευέλικτη επιλογή για cosplay, Halloween, fantasy εκδηλώσεις και θεατρικές παραστάσεις.</p>\n"
            "<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. Διαθέτει ελαστική βάση που εφαρμόζει σε περίμετρο κεφαλής από 42 έως 63 εκ. Πλένεται και χτενίζεται εύκολα — φτιαγμένη για να αντέχει χρόνια.</p>\n"
            "<ul>\n<li>Στυλ: μακριά καστανή περούκα — ζεστή και φυσική</li>\n"
            "<li>Κατάλληλη για: cosplay, Halloween, αποκριές, θέατρο, φαντασιακή στολή</li>\n"
            "<li>Ελαστική βάση: εφαρμόζει σε περίμετρο κεφαλής 42–63 εκ.</li>\n"
            "<li>Κατασκευάζεται στην Ελλάδα — διαθέσιμη κατά παραγγελία σε ειδικά μεγέθη</li>\n</ul>"
        ),
        short_en="<p>Long flowing brown wig — Earth. Warm natural style. Handmade in Greece. Elastic base, fits all.</p>",
        short_el="<p>Μακριά ρέουσα καστανή περούκα — Γη. Ζεστό, φυσικό στυλ. Φτιάχνεται στην Ελλάδα. Ελαστική βάση.</p>",
        meta_en="Earth Long Brown Theatrical Wig | Handmade in Greece | Alegro Athens",
        meta_el="Γη Μακριά Καστανή Θεατρική Περούκα | Alegro Αθήνα",
    ),

    # 93 — SEA: long blue
    93: dict(
        desc_en=(
            "<p>The <strong>Sea Wig</strong> is a long, flowing blue wig — deep, vivid, and full of movement. "
            "Inspired by the elemental force of the sea, it evokes ocean depths and mythological sea creatures. "
            "An exceptional choice for Halloween, fantasy cosplay, carnival, and any water or ocean-themed costume.</p>\n"
            "<p>Made in our workshop in Athens, Greece. Features a comfortable elastic base that fits head circumferences from 42 to 63 cm. Easy to wash and comb — built to last for years.</p>\n"
            "<ul>\n<li>Style: long flowing blue wig — deep and vivid</li>\n"
            "<li>Ideal for: Halloween, cosplay, carnival, theatre, ocean / mermaid costume</li>\n"
            "<li>Elastic base: fits 42–63 cm head circumference</li>\n"
            "<li>Made in Greece — custom sizes available on request</li>\n</ul>"
        ),
        desc_el=(
            "<p>Η <strong>Περούκα Θάλασσα</strong> είναι μια μακριά, ρέουσα μπλε περούκα — βαθιά, ζωηρή και γεμάτη κίνηση. "
            "Εμπνευσμένη από το στοιχείο της θάλασσας, παραπέμπει στα βάθη του ωκεανού και στα μυθολογικά πλάσματα της θάλασσας. "
            "Εξαιρετική επιλογή για Halloween, fantasy cosplay, αποκριές και κάθε θαλάσσια ή υδάτινη στολή.</p>\n"
            "<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. Διαθέτει ελαστική βάση που εφαρμόζει σε περίμετρο κεφαλής από 42 έως 63 εκ. Πλένεται και χτενίζεται εύκολα — φτιαγμένη για να αντέχει χρόνια.</p>\n"
            "<ul>\n<li>Στυλ: μακριά μπλε περούκα — βαθιά και ζωηρή</li>\n"
            "<li>Κατάλληλη για: Halloween, cosplay, αποκριές, θέατρο, στολή γοργόνας / θάλασσας</li>\n"
            "<li>Ελαστική βάση: εφαρμόζει σε περίμετρο κεφαλής 42–63 εκ.</li>\n"
            "<li>Κατασκευάζεται στην Ελλάδα — διαθέσιμη κατά παραγγελία σε ειδικά μεγέθη</li>\n</ul>"
        ),
        short_en="<p>Long flowing blue wig — Sea. Deep vivid colour. Handmade in Greece. Elastic base, fits all.</p>",
        short_el="<p>Μακριά ρέουσα μπλε περούκα — Θάλασσα. Βαθύ ζωηρό χρώμα. Φτιάχνεται στην Ελλάδα. Ελαστική βάση.</p>",
        meta_en="Sea Long Blue Theatrical Wig | Handmade in Greece | Alegro Athens",
        meta_el="Θάλασσα Μακριά Μπλε Θεατρική Περούκα | Alegro Αθήνα",
    ),

    # 94 — AMPHITRITE BLACK
    94: dict(
        desc_en=(
            "<p>The <strong>Amphitrite Black Wig</strong> is a long, flowing black wig named after Amphitrite — "
            "the majestic Greek sea goddess, queen of the oceans and consort of Poseidon. "
            "Timeless and dramatic, this wig is perfect for mythology-themed costumes, cosplay, Halloween, and theatrical performances.</p>\n"
            "<p>Made in our workshop in Athens, Greece. Features a comfortable elastic base that fits head circumferences from 42 to 63 cm. Easy to wash and comb — built to last for years.</p>\n"
            "<ul>\n<li>Style: long flowing black wig — elegant and dramatic</li>\n"
            "<li>Ideal for: mythology cosplay, Halloween, carnival, theatre</li>\n"
            "<li>Elastic base: fits 42–63 cm head circumference</li>\n"
            "<li>Made in Greece — custom sizes available on request</li>\n</ul>"
        ),
        desc_el=(
            "<p>Η <strong>Περούκα Αμφιτρίτη Μαύρη</strong> είναι μια μακριά, ρέουσα μαύρη περούκα εμπνευσμένη από την Αμφιτρίτη — "
            "τη μεγαλοπρεπή θεά της θάλασσας στην ελληνική μυθολογία, βασίλισσα των ωκεανών και σύζυγο του Ποσειδώνα. "
            "Διαχρονική και δραματική, ιδανική για μυθολογικές στολές, cosplay, Halloween και θεατρικές παραστάσεις.</p>\n"
            "<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. Διαθέτει ελαστική βάση που εφαρμόζει σε περίμετρο κεφαλής από 42 έως 63 εκ. Πλένεται και χτενίζεται εύκολα — φτιαγμένη για να αντέχει χρόνια.</p>\n"
            "<ul>\n<li>Στυλ: μακριά ρέουσα μαύρη περούκα — κομψή και δραματική</li>\n"
            "<li>Κατάλληλη για: μυθολογικό cosplay, Halloween, αποκριές, θέατρο</li>\n"
            "<li>Ελαστική βάση: εφαρμόζει σε περίμετρο κεφαλής 42–63 εκ.</li>\n"
            "<li>Κατασκευάζεται στην Ελλάδα — διαθέσιμη κατά παραγγελία σε ειδικά μεγέθη</li>\n</ul>"
        ),
        short_en="<p>Long flowing black wig — Amphitrite, Greek sea goddess. Handmade in Greece. Elastic base, fits all.</p>",
        short_el="<p>Μακριά ρέουσα μαύρη περούκα — Αμφιτρίτη, ελληνική θεά της θάλασσας. Φτιάχνεται στην Ελλάδα. Ελαστική βάση.</p>",
        meta_en="Amphitrite Black Long Wig Greek Goddess | Handmade in Greece | Alegro Athens",
        meta_el="Αμφιτρίτη Μαύρη Μακριά Περούκα Ελληνική Θεά | Alegro Αθήνα",
    ),

    # 95 — AMPHITRITE BLONDE
    95: dict(
        desc_en=(
            "<p>The <strong>Amphitrite Blonde Wig</strong> is a long, flowing blonde wig named after Amphitrite — "
            "the majestic Greek sea goddess, queen of the oceans and consort of Poseidon. "
            "Luminous and graceful, this wig is perfect for mythology-themed costumes, cosplay, Halloween, and theatrical performances.</p>\n"
            "<p>Made in our workshop in Athens, Greece. Features a comfortable elastic base that fits head circumferences from 42 to 63 cm. Easy to wash and comb — built to last for years.</p>\n"
            "<ul>\n<li>Style: long flowing blonde wig — luminous and graceful</li>\n"
            "<li>Ideal for: mythology cosplay, Halloween, carnival, theatre</li>\n"
            "<li>Elastic base: fits 42–63 cm head circumference</li>\n"
            "<li>Made in Greece — custom sizes available on request</li>\n</ul>"
        ),
        desc_el=(
            "<p>Η <strong>Περούκα Αμφιτρίτη Ξανθιά</strong> είναι μια μακριά, ρέουσα ξανθιά περούκα εμπνευσμένη από την Αμφιτρίτη — "
            "τη μεγαλοπρεπή θεά της θάλασσας στην ελληνική μυθολογία, βασίλισσα των ωκεανών και σύζυγο του Ποσειδώνα. "
            "Λαμπερή και χαριτωμένη, ιδανική για μυθολογικές στολές, cosplay, Halloween και θεατρικές παραστάσεις.</p>\n"
            "<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. Διαθέτει ελαστική βάση που εφαρμόζει σε περίμετρο κεφαλής από 42 έως 63 εκ. Πλένεται και χτενίζεται εύκολα — φτιαγμένη για να αντέχει χρόνια.</p>\n"
            "<ul>\n<li>Στυλ: μακριά ρέουσα ξανθιά περούκα — λαμπερή και χαριτωμένη</li>\n"
            "<li>Κατάλληλη για: μυθολογικό cosplay, Halloween, αποκριές, θέατρο</li>\n"
            "<li>Ελαστική βάση: εφαρμόζει σε περίμετρο κεφαλής 42–63 εκ.</li>\n"
            "<li>Κατασκευάζεται στην Ελλάδα — διαθέσιμη κατά παραγγελία σε ειδικά μεγέθη</li>\n</ul>"
        ),
        short_en="<p>Long flowing blonde wig — Amphitrite, Greek sea goddess. Handmade in Greece. Elastic base, fits all.</p>",
        short_el="<p>Μακριά ρέουσα ξανθιά περούκα — Αμφιτρίτη, ελληνική θεά της θάλασσας. Φτιάχνεται στην Ελλάδα. Ελαστική βάση.</p>",
        meta_en="Amphitrite Blonde Long Wig Greek Goddess | Handmade in Greece | Alegro Athens",
        meta_el="Αμφιτρίτη Ξανθιά Μακριά Περούκα Ελληνική Θεά | Alegro Αθήνα",
    ),

    # 96 — Jessica Red Long Straight Wig
    96: dict(
        desc_en=(
            "<p>The <strong>Jessica Red Wig</strong> is a long, straight vivid red wig — bold, confident, and full of character. "
            "A great choice for cosplay characters, Halloween, carnival, retro looks, and any occasion where you want long, striking red hair.</p>\n"
            "<p>Made in our workshop in Athens, Greece. Features a comfortable elastic base that fits head circumferences from 42 to 63 cm. Easy to wash and comb — built to last for years.</p>\n"
            "<ul>\n<li>Style: long straight vivid red hair</li>\n"
            "<li>Ideal for: cosplay, Halloween, carnival, retro / vintage look</li>\n"
            "<li>Elastic base: fits 42–63 cm head circumference</li>\n"
            "<li>Made in Greece — custom sizes available on request</li>\n</ul>"
        ),
        desc_el=(
            "<p>Η <strong>Περούκα Τζέσικα Κόκκινη</strong> είναι μια μακριά, ίσια ζωηρή κόκκινη περούκα — τολμηρή, δυναμική και γεμάτη χαρακτήρα. "
            "Υπέροχη επιλογή για cosplay χαρακτήρες, Halloween, αποκριές, retro εμφανίσεις και κάθε στιγμή που θέλετε εντυπωσιακά κόκκινα μαλλιά.</p>\n"
            "<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. Διαθέτει ελαστική βάση που εφαρμόζει σε περίμετρο κεφαλής από 42 έως 63 εκ. Πλένεται και χτενίζεται εύκολα — φτιαγμένη για να αντέχει χρόνια.</p>\n"
            "<ul>\n<li>Στυλ: μακριά ίσια ζωηρή κόκκινη</li>\n"
            "<li>Κατάλληλη για: cosplay, Halloween, αποκριές, retro / vintage look</li>\n"
            "<li>Ελαστική βάση: εφαρμόζει σε περίμετρο κεφαλής 42–63 εκ.</li>\n"
            "<li>Κατασκευάζεται στην Ελλάδα — διαθέσιμη κατά παραγγελία σε ειδικά μεγέθη</li>\n</ul>"
        ),
        short_en="<p>Long straight vivid red wig — Jessica. Bold and striking. Handmade in Greece. Elastic base, fits all.</p>",
        short_el="<p>Μακριά ίσια ζωηρή κόκκινη περούκα — Τζέσικα. Φτιάχνεται στην Ελλάδα. Ελαστική βάση, εφαρμόζει σε όλους.</p>",
        meta_en="Jessica Red Long Straight Wig | Handmade in Greece | Alegro Athens",
        meta_el="Τζέσικα Κόκκινη Μακριά Ίσια Περούκα | Alegro Αθήνα",
    ),

    # 97 — LEDA BLACK
    97: dict(
        desc_en=(
            "<p>The <strong>Leda Black Wig</strong> is a long, flowing black wig named after Leda — "
            "the legendary queen of Sparta in Greek mythology, celebrated for her timeless beauty. "
            "Elegant and dramatic, this wig is perfect for mythology-themed costumes, cosplay, Halloween, and theatrical performances.</p>\n"
            "<p>Made in our workshop in Athens, Greece. Features a comfortable elastic base that fits head circumferences from 42 to 63 cm. Easy to wash and comb — built to last for years.</p>\n"
            "<ul>\n<li>Style: long flowing black wig — elegant and dramatic</li>\n"
            "<li>Ideal for: mythology cosplay, Halloween, carnival, theatre</li>\n"
            "<li>Elastic base: fits 42–63 cm head circumference</li>\n"
            "<li>Made in Greece — custom sizes available on request</li>\n</ul>"
        ),
        desc_el=(
            "<p>Η <strong>Περούκα Λήδα Μαύρη</strong> είναι μια μακριά, ρέουσα μαύρη περούκα εμπνευσμένη από τη Λήδα — "
            "τη θρυλική βασίλισσα της Σπάρτης στην ελληνική μυθολογία, γνωστή για την αθάνατη ομορφιά της. "
            "Κομψή και δραματική, ιδανική για μυθολογικές στολές, cosplay, Halloween και θεατρικές παραστάσεις.</p>\n"
            "<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. Διαθέτει ελαστική βάση που εφαρμόζει σε περίμετρο κεφαλής από 42 έως 63 εκ. Πλένεται και χτενίζεται εύκολα — φτιαγμένη για να αντέχει χρόνια.</p>\n"
            "<ul>\n<li>Στυλ: μακριά ρέουσα μαύρη περούκα — κομψή και δραματική</li>\n"
            "<li>Κατάλληλη για: μυθολογικό cosplay, Halloween, αποκριές, θέατρο</li>\n"
            "<li>Ελαστική βάση: εφαρμόζει σε περίμετρο κεφαλής 42–63 εκ.</li>\n"
            "<li>Κατασκευάζεται στην Ελλάδα — διαθέσιμη κατά παραγγελία σε ειδικά μεγέθη</li>\n</ul>"
        ),
        short_en="<p>Long flowing black wig — Leda, queen of Sparta. Handmade in Greece. Elastic base, fits all.</p>",
        short_el="<p>Μακριά ρέουσα μαύρη περούκα — Λήδα, βασίλισσα της Σπάρτης. Φτιάχνεται στην Ελλάδα. Ελαστική βάση.</p>",
        meta_en="Leda Black Long Wig Greek Mythology | Handmade in Greece | Alegro Athens",
        meta_el="Λήδα Μαύρη Μακριά Περούκα Ελληνική Μυθολογία | Alegro Αθήνα",
    ),

    # 98 — LEDA BLONDE
    98: dict(
        desc_en=(
            "<p>The <strong>Leda Blonde Wig</strong> is a long, flowing blonde wig named after Leda — "
            "the legendary queen of Sparta in Greek mythology, celebrated for her timeless beauty. "
            "Luminous and graceful, this wig is perfect for mythology-themed costumes, cosplay, Halloween, and theatrical performances.</p>\n"
            "<p>Made in our workshop in Athens, Greece. Features a comfortable elastic base that fits head circumferences from 42 to 63 cm. Easy to wash and comb — built to last for years.</p>\n"
            "<ul>\n<li>Style: long flowing blonde wig — luminous and graceful</li>\n"
            "<li>Ideal for: mythology cosplay, Halloween, carnival, theatre</li>\n"
            "<li>Elastic base: fits 42–63 cm head circumference</li>\n"
            "<li>Made in Greece — custom sizes available on request</li>\n</ul>"
        ),
        desc_el=(
            "<p>Η <strong>Περούκα Λήδα Ξανθιά</strong> είναι μια μακριά, ρέουσα ξανθιά περούκα εμπνευσμένη από τη Λήδα — "
            "τη θρυλική βασίλισσα της Σπάρτης στην ελληνική μυθολογία, γνωστή για την αθάνατη ομορφιά της. "
            "Λαμπερή και χαριτωμένη, ιδανική για μυθολογικές στολές, cosplay, Halloween και θεατρικές παραστάσεις.</p>\n"
            "<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. Διαθέτει ελαστική βάση που εφαρμόζει σε περίμετρο κεφαλής από 42 έως 63 εκ. Πλένεται και χτενίζεται εύκολα — φτιαγμένη για να αντέχει χρόνια.</p>\n"
            "<ul>\n<li>Στυλ: μακριά ρέουσα ξανθιά περούκα — λαμπερή και χαριτωμένη</li>\n"
            "<li>Κατάλληλη για: μυθολογικό cosplay, Halloween, αποκριές, θέατρο</li>\n"
            "<li>Ελαστική βάση: εφαρμόζει σε περίμετρο κεφαλής 42–63 εκ.</li>\n"
            "<li>Κατασκευάζεται στην Ελλάδα — διαθέσιμη κατά παραγγελία σε ειδικά μεγέθη</li>\n</ul>"
        ),
        short_en="<p>Long flowing blonde wig — Leda, queen of Sparta. Handmade in Greece. Elastic base, fits all.</p>",
        short_el="<p>Μακριά ρέουσα ξανθιά περούκα — Λήδα, βασίλισσα της Σπάρτης. Φτιάχνεται στην Ελλάδα. Ελαστική βάση.</p>",
        meta_en="Leda Blonde Long Wig Greek Mythology | Handmade in Greece | Alegro Athens",
        meta_el="Λήδα Ξανθιά Μακριά Περούκα Ελληνική Μυθολογία | Alegro Αθήνα",
    ),

    # 99 — LONG BLACK CURLY
    99: dict(
        desc_en=(
            "<p>The <strong>Long Black Curly Wig</strong> is a full, voluminous wig with long, loose curls in deep black — "
            "a bold, dramatic style that makes an immediate impression. "
            "An excellent choice for cosplay, Halloween, carnival, theatrical performances, and any occasion calling for abundant, curly hair.</p>\n"
            "<p>Made in our workshop in Athens, Greece. Features a comfortable elastic base that fits head circumferences from 42 to 63 cm. Easy to wear — built to last for years.</p>\n"
            "<ul>\n<li>Style: long loose curls — deep black</li>\n"
            "<li>Ideal for: cosplay, Halloween, carnival, theatre, fantasy costume</li>\n"
            "<li>Elastic base: fits 42–63 cm head circumference</li>\n"
            "<li>Made in Greece — custom sizes available on request</li>\n</ul>"
        ),
        desc_el=(
            "<p>Η <strong>Μακριά Μαύρη Σγουρή Περούκα</strong> είναι μια πλούσια, ογκώδης περούκα με μακριές, ελεύθερες μπούκλες σε βαθύ μαύρο — "
            "τολμηρό, δραματικό στυλ που τραβάει αμέσως το βλέμμα. "
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

    # 100 — LONG BLONDE CURLY
    100: dict(
        desc_en=(
            "<p>The <strong>Long Blonde Curly Wig</strong> is a full, voluminous wig with long, loose curls in warm blonde — "
            "a radiant, romantic style that turns heads. "
            "A wonderful choice for cosplay, Halloween, carnival, theatrical performances, and any occasion calling for abundant, curly hair.</p>\n"
            "<p>Made in our workshop in Athens, Greece. Features a comfortable elastic base that fits head circumferences from 42 to 63 cm. Easy to wear — built to last for years.</p>\n"
            "<ul>\n<li>Style: long loose curls — warm blonde</li>\n"
            "<li>Ideal for: cosplay, Halloween, carnival, theatre, fantasy costume</li>\n"
            "<li>Elastic base: fits 42–63 cm head circumference</li>\n"
            "<li>Made in Greece — custom sizes available on request</li>\n</ul>"
        ),
        desc_el=(
            "<p>Η <strong>Μακριά Ξανθιά Σγουρή Περούκα</strong> είναι μια πλούσια, ογκώδης περούκα με μακριές, ελεύθερες μπούκλες σε ζεστό ξανθό — "
            "λαμπερό, ρομαντικό στυλ που τραβάει βλέμματα. "
            "Υπέροχη επιλογή για cosplay, Halloween, αποκριές, θεατρικές παραστάσεις και κάθε στιγμή που θέλετε πλούσια, σγουρά μαλλιά.</p>\n"
            "<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. Διαθέτει ελαστική βάση που εφαρμόζει σε περίμετρο κεφαλής από 42 έως 63 εκ. Εύκολη στη χρήση — φτιαγμένη για να αντέχει χρόνια.</p>\n"
            "<ul>\n<li>Στυλ: μακριές ελεύθερες μπούκλες — ζεστό ξανθό</li>\n"
            "<li>Κατάλληλη για: cosplay, Halloween, αποκριές, θέατρο, φαντασιακή στολή</li>\n"
            "<li>Ελαστική βάση: εφαρμόζει σε περίμετρο κεφαλής 42–63 εκ.</li>\n"
            "<li>Κατασκευάζεται στην Ελλάδα — διαθέσιμη κατά παραγγελία σε ειδικά μεγέθη</li>\n</ul>"
        ),
        short_en="<p>Long blonde curly wig. Full, radiant style. Handmade in Greece. Elastic base, fits all.</p>",
        short_el="<p>Μακριά ξανθιά σγουρή περούκα. Πλούσιο, λαμπερό στυλ. Φτιάχνεται στην Ελλάδα. Ελαστική βάση.</p>",
        meta_en="Long Blonde Curly Wig | Handmade in Greece | Alegro Athens",
        meta_el="Μακριά Ξανθιά Σγουρή Περούκα | Alegro Αθήνα",
    ),

    # 101 — LADY GODIVA
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
            "την Αγγλοσαξονική ευγενή που αθανατίστηκε για τον περίπατό της στο Κόβεντρι με μόνο κάλυμμα τις χρυσές ρέουσες τρέσες της. "
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

    # 102-105 — DANAE (long with side part)
    102: danae("Blonde Light Brown", "Ξανθιά",   "ξανθό"),
    103: danae("Black",              "Μαύρη",    "μαύρο"),
    104: danae("Honey Blonde",       "Μελί",     "μελί"),
    105: danae("Red",                "Κόκκινη",  "κόκκινο"),

    # 106-107 — APHRODITE (long with side part, Greek goddess)
    106: dict(
        desc_en=(
            "<p>The <strong>Aphrodite Platinum Blonde Wig</strong> is a long, straight platinum blonde wig with a sweeping side part — "
            "inspired by Aphrodite, the Greek goddess of love and beauty. Radiant and luminous, it captures the divine grace "
            "of the goddess. A beautiful choice for mythology cosplay, fancy dress, Halloween, and theatrical performances.</p>\n"
            "<p>Made in our workshop in Athens, Greece. Features a comfortable elastic base that fits head circumferences from 42 to 63 cm. Easy to wash and comb — built to last for years.</p>\n"
            "<ul>\n<li>Style: long straight platinum blonde hair with side part</li>\n"
            "<li>Ideal for: mythology cosplay, Halloween, carnival, theatre, fantasy costume</li>\n"
            "<li>Elastic base: fits 42–63 cm head circumference</li>\n"
            "<li>Made in Greece — custom sizes available on request</li>\n</ul>"
        ),
        desc_el=(
            "<p>Η <strong>Περούκα Αφροδίτη Πλατινέ Ξανθιά</strong> είναι μια μακριά, ίσια πλατινέ ξανθιά περούκα με χωρίστρα στο πλάι — "
            "εμπνευσμένη από την Αφροδίτη, τη θεά της αγάπης και της ομορφιάς στην ελληνική μυθολογία. Λαμπερή και φωτεινή, αποτυπώνει τη θεϊκή χάρη της θεάς. "
            "Υπέροχη επιλογή για μυθολογικές μεταμφιέσεις, Halloween, αποκριές και θεατρικές παραστάσεις.</p>\n"
            "<p>Φτιάχνεται στο εργαστήριό μας στην Αθήνα. Διαθέτει ελαστική βάση που εφαρμόζει σε περίμετρο κεφαλής από 42 έως 63 εκ. Πλένεται και χτενίζεται εύκολα — φτιαγμένη για να αντέχει χρόνια.</p>\n"
            "<ul>\n<li>Στυλ: μακριά ίσια πλατινέ ξανθιά με χωρίστρα στο πλάι</li>\n"
            "<li>Κατάλληλη για: μυθολογικό cosplay, Halloween, αποκριές, θέατρο, φαντασιακή στολή</li>\n"
            "<li>Ελαστική βάση: εφαρμόζει σε περίμετρο κεφαλής 42–63 εκ.</li>\n"
            "<li>Κατασκευάζεται στην Ελλάδα — διαθέσιμη κατά παραγγελία σε ειδικά μεγέθη</li>\n</ul>"
        ),
        short_en="<p>Long straight platinum blonde wig with side part — Aphrodite. Handmade in Greece. Elastic base, fits all.</p>",
        short_el="<p>Μακριά ίσια πλατινέ ξανθιά περούκα με χωρίστρα στο πλάι — Αφροδίτη. Φτιάχνεται στην Ελλάδα. Ελαστική βάση.</p>",
        meta_en="Aphrodite Platinum Blonde Long Wig Side Part | Handmade in Greece | Alegro Athens",
        meta_el="Αφροδίτη Πλατινέ Ξανθιά Μακριά Περούκα | Alegro Αθήνα",
    ),
    107: dict(
        desc_en=(
            "<p>The <strong>Aphrodite Black Wig</strong> is a long, straight black wig with a sweeping side part — "
            "inspired by Aphrodite, the Greek goddess of love and beauty, rendered here in timeless, dramatic black. "
            "Elegant and striking, it suits mythology cosplay, fancy dress, Halloween, and theatrical performances.</p>\n"
            "<p>Made in our workshop in Athens, Greece. Features a comfortable elastic base that fits head circumferences from 42 to 63 cm. Easy to wash and comb — built to last for years.</p>\n"
            "<ul>\n<li>Style: long straight black hair with side part</li>\n"
            "<li>Ideal for: mythology cosplay, Halloween, carnival, theatre, fantasy costume</li>\n"
            "<li>Elastic base: fits 42–63 cm head circumference</li>\n"
            "<li>Made in Greece — custom sizes available on request</li>\n</ul>"
        ),
        desc_el=(
            "<p>Η <strong>Περούκα Αφροδίτη Μαύρη</strong> είναι μια μακριά, ίσια μαύρη περούκα με χωρίστρα στο πλάι — "
            "εμπνευσμένη από την Αφροδίτη, τη θεά της αγάπης και της ομορφιάς, εδώ σε διαχρονικό, δραματικό μαύρο. "
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

    # 108-113 — PAULINE (medium layered with fringe)
    108: pauline("Black",        "Μαύρη",      "μαύρο"),
    109: pauline("Red",          "Κόκκινη",    "κόκκινο"),
    110: pauline("Multicoloured","Τρίχρωμη",   "τρίχρωμο"),
    111: pauline("White",        "Λευκή",      "λευκό"),
    112: pauline("Light Blue",   "Γαλάζια",    "γαλάζιο"),
    113: pauline("Purple",       "Μωβ",        "μωβ"),

    # 114-115 — JOHN (short men's wig)
    114: john("Black",  "Μαύρη", "μαύρο"),
    115: john("Blonde", "Ξανθιά","ξανθό"),

    # 116-117 — JIM (wig with ponytail)
    116: jim("Black", "Μαύρη", "μαύρο"),
    117: jim("Gray",  "Γκρι",  "γκρι"),
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

# ── Per-product worker ────────────────────────────────────────────────────────

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

# ── Main ──────────────────────────────────────────────────────────────────────

log('Logging in…')
sessions = [make_session() for _ in range(WORKERS)]
log(f'All {WORKERS} sessions ready. Processing {len(PRODUCTS)} products.\n')

pids = sorted(PRODUCTS.keys())
tasks = [(i % WORKERS, pid) for i, pid in enumerate(pids)]

def worker(args):
    idx, pid = args
    s, cat = sessions[idx]
    return update_product(s, cat, pid, PRODUCTS[pid])

ok = skip = fail = 0
done = 0
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
