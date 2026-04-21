"""
Product descriptions data — Part 1 (PIDs 20–175).
Run generate_descriptions_sql.py to produce the SQL file.
"""

# Shared closing paragraphs
CLOSE_EN = (
    "<p>Handcrafted in our small atelier in Athens, Greece, "
    "with over 45 years of wig-making tradition. "
    "Features an elastic base that comfortably fits head circumferences "
    "from 42 to 63 cm.</p>"
)
CLOSE_EL = (
    "<p>Χειροποίητη στο μικρό μας ατελιέ στην Αθήνα, Ελλάδα, "
    "με πάνω από 45 χρόνια παράδοσης στην κατασκευή περούκων. "
    "Διαθέτει ελαστική βάση που προσαρμόζεται άνετα σε περίμετρο κεφαλής "
    "από 42 έως 63 εκατοστά.</p>"
)

def d(desc_en, short_en, desc_el, short_el,
      name_en="", name_el="", slug_en="", slug_el="",
      meta_en="", meta_el=""):
    return {
        "name_en": name_en, "name_el": name_el,
        "desc_en": desc_en + CLOSE_EN,
        "short_en": short_en,
        "desc_el": desc_el + CLOSE_EL,
        "short_el": short_el,
        "slug_en": slug_en, "slug_el": slug_el,
        "meta_en": meta_en, "meta_el": meta_el,
    }

# ── Hero series helper ───────────────────────────────────────────────────────
_hero_colors_en = {
    "RED": ("red","κόκκινη"), "YELLOW": ("yellow","κίτρινη"),
    "PURPLE": ("purple","μωβ"), "GREEN": ("green","πράσινη"),
    "PINK": ("pink","ροζ"), "BLACK": ("black","μαύρη"),
    "AUBURN": ("auburn","ακαζού"), "BLONDE": ("blonde","ξανθιά"),
    "FUCHSIA": ("fuchsia","φούξια"),
}

def hero(color_key):
    en, el = _hero_colors_en[color_key]
    name_en = f"Hero {color_key.title()} Wig"
    name_el = f"Περούκα Ήρωας {color_key.title()}"
    de = (
        f"<p>The <strong>Hero {color_key.title()} Wig</strong> is a bold, "
        f"short bob-style wig in vibrant {en}. Whether you're dressing as a superhero, "
        f"a pop-art character, or heading to a themed party, this eye-catching wig "
        f"delivers instant impact.</p>"
        f"<ul><li>Color: {color_key.title()}</li>"
        f"<li>Style: Short bob</li>"
        f"<li>Ideal for: superhero costumes, carnival, themed parties, stage performances</li>"
        f"<li>Material: High-quality synthetic fiber</li>"
        f"<li>Made in Greece</li></ul>"
    )
    se = f"<p>Short {en} bob-style Hero wig. Perfect for superhero costumes, carnival, and parties. Made in Athens, Greece.</p>"
    dl = (
        f"<p>Η <strong>περούκα Ήρωας σε {el} χρώμα</strong> είναι μια τολμηρή, "
        f"κοντή κυκλική περούκα σε ζωντανό {el} χρώμα. Ιδανική για μεταμφιέσεις "
        f"σε σούπερ ήρωα, αποκριάτικες εκδηλώσεις και θεματικά πάρτι.</p>"
        f"<ul><li>Χρώμα: {color_key.title()}</li>"
        f"<li>Στυλ: Κοντό καρέ</li>"
        f"<li>Κατάλληλη για: μεταμφίεση σε ήρωα, αποκριές, θεματικές εκδηλώσεις</li>"
        f"<li>Υλικό: Υψηλής ποιότητας συνθετική ίνα</li>"
        f"<li>Κατασκευή στην Ελλάδα</li></ul>"
    )
    sl = f"<p>Κοντή περούκα Ήρωας σε {el} χρώμα. Ιδανική για μεταμφιέσεις σε σούπερ ήρωα, αποκριές και πάρτι. Κατασκευή στην Αθήνα.</p>"
    c = color_key.lower()
    return d(de, se, dl, sl,
             name_en=name_en, name_el=name_el,
             slug_en=f"hero-{c}-wig", slug_el=f"perouka-iroas-{c}",
             meta_en=f"Hero {color_key.title()} Short Bob Wig | Alegro Athens",
             meta_el=f"Περούκα Ήρωας {color_key.title()} Κοντή | Alegro Αθήνα")

# ── Xena series helper ───────────────────────────────────────────────────────
def xena(color_en, color_el, slug_suffix_en, slug_suffix_el):
    name_en = f"Xena {color_en.title()} Long Wig with Fringe"
    name_el = f"Περούκα Σίσσυ Μακριά με Αφέλεια — {color_el.title()}"
    de = (
        f"<p>The <strong>Xena {color_en.title()} Wig</strong> is a long, straight wig "
        f"with a stylish fringe, inspired by the warrior heroines of action and adventure. "
        f"Its smooth, flowing {color_en} fibers create a dramatic, commanding presence — "
        f"perfect for theatrical productions, cosplay, and historical costume events.</p>"
        f"<ul><li>Color: {color_en.title()}</li>"
        f"<li>Style: Long, straight, with fringe</li>"
        f"<li>Ideal for: cosplay, theatre, carnival, historical reenactments</li>"
        f"<li>Material: High-quality synthetic fiber</li>"
        f"<li>Made in Greece</li></ul>"
    )
    se = f"<p>Long {color_en} straight wig with fringe. Ideal for warrior and action-hero costumes, theatre, and cosplay. Made in Athens, Greece.</p>"
    dl = (
        f"<p>Η <strong>περούκα Σίσσυ σε {color_el} χρώμα</strong> είναι μια μακριά, ίσια περούκα "
        f"με κομψή αφέλεια, εμπνευσμένη από θρυλικές πολεμίστριες. "
        f"Οι λείες, ρέουσες {color_el} ίνες της δημιουργούν μια εντυπωσιακή παρουσία, "
        f"ιδανική για θεατρικές παραστάσεις, cosplay και αποκριάτικες εκδηλώσεις.</p>"
        f"<ul><li>Χρώμα: {color_el.title()}</li>"
        f"<li>Στυλ: Μακριά, ίσια, με αφέλεια</li>"
        f"<li>Κατάλληλη για: cosplay, θέατρο, αποκριές, ιστορικές αναπαραστάσεις</li>"
        f"<li>Υλικό: Υψηλής ποιότητας συνθετική ίνα</li>"
        f"<li>Κατασκευή στην Ελλάδα</li></ul>"
    )
    sl = f"<p>Μακριά {color_el} ίσια περούκα με αφέλεια. Ιδανική για cosplay, θέατρο και αποκριές. Κατασκευή στην Αθήνα.</p>"
    return d(de, se, dl, sl,
             name_en=name_en, name_el=name_el,
             slug_en=f"xena-{slug_suffix_en}-long-wig", slug_el=f"perouka-sissy-{slug_suffix_el}-makria",
             meta_en=f"Xena {color_en.title()} Long Wig with Fringe | Alegro Athens",
             meta_el=f"Περούκα Σίσσυ {color_el.title()} Μακριά με Αφέλεια | Alegro")

# ── Disco/Afro series helper ─────────────────────────────────────────────────
def disco(color_en, color_el, slug_c_en, slug_c_el, curly=True):
    style = "curly afro" if curly else "voluminous"
    style_el = "σγουρή αφάνα" if curly else "ογκώδης"
    name_en = f"Disco {color_en.title()} {'Curly Afro ' if curly else ''}Wig"
    name_el = f"Περούκα Ντίσκο {color_el.title()} {'Σγουρή Αφάνα' if curly else ''}"
    de = (
        f"<p>The <strong>Disco {color_en.title()} Wig</strong> is a show-stopping "
        f"{style} wig in dazzling {color_en}. Inspired by the glam and energy of the "
        f"1970s disco era, it turns heads at any party, carnival, or stage event. "
        f"Big, bold, and unforgettable.</p>"
        f"<ul><li>Color: {color_en.title()}</li>"
        f"<li>Style: {'Curly afro' if curly else 'Voluminous'}</li>"
        f"<li>Ideal for: disco-themed parties, carnival, stage, photoshoots</li>"
        f"<li>Material: High-quality synthetic fiber</li>"
        f"<li>Made in Greece</li></ul>"
    )
    se = f"<p>Eye-catching {color_en} {style} disco wig. Perfect for 70s-themed parties, carnival, and stage. Made in Athens, Greece.</p>"
    dl = (
        f"<p>Η <strong>περούκα Ντίσκο σε {color_el} χρώμα</strong> είναι μια εντυπωσιακή "
        f"{style_el} περούκα. Εμπνευσμένη από τη λάμψη της δεκαετίας του '70, "
        f"κλέβει τις εντυπώσεις σε κάθε πάρτι, αποκριάτικη εκδήλωση ή παράσταση.</p>"
        f"<ul><li>Χρώμα: {color_el.title()}</li>"
        f"<li>Στυλ: {'Σγουρή αφάνα' if curly else 'Ογκώδης'}</li>"
        f"<li>Κατάλληλη για: ντίσκο πάρτι, αποκριές, σκηνή, φωτογραφίσεις</li>"
        f"<li>Υλικό: Υψηλής ποιότητας συνθετική ίνα</li>"
        f"<li>Κατασκευή στην Ελλάδα</li></ul>"
    )
    sl = f"<p>{color_el.title()} {'σγουρή αφάνα' if curly else 'ογκώδης'} περούκα ντίσκο. Ιδανική για πάρτι, αποκριές και παραστάσεις. Κατασκευή στην Αθήνα.</p>"
    return d(de, se, dl, sl,
             name_en=name_en, name_el=name_el,
             slug_en=f"disco-{slug_c_en}-wig", slug_el=f"perouka-disko-{slug_c_el}",
             meta_en=f"Disco {color_en.title()} Wig | Party & Carnival | Alegro Athens",
             meta_el=f"Περούκα Ντίσκο {color_el.title()} | Πάρτι & Αποκριές | Alegro")

# ── Afro size helpers ────────────────────────────────────────────────────────
def afro(color_en, color_el, slug_c_en, slug_c_el, size="regular"):
    prefix = {"small": "Small ", "super": "Super ", "regular": ""}[size]
    prefix_el = {"small": "Μικρή ", "super": "Σούπερ ", "regular": ""}[size]
    name_en = f"{prefix}Afro {color_en.title()} Wig"
    name_el = f"{prefix_el}Αφάνα {color_el.title()}"
    de = (
        f"<p>The <strong>{prefix}Afro {color_en.title()} Wig</strong> is a "
        f"{'compact yet' if size=='small' else 'full and' if size=='regular' else 'dramatically large and'} "
        f"voluminous curly afro wig in vibrant {color_en}. "
        f"A classic carnival and party staple that never fails to impress.</p>"
        f"<ul><li>Color: {color_en.title()}</li>"
        f"<li>Style: {'Compact' if size=='small' else 'Full' if size=='regular' else 'Extra large'} curly afro</li>"
        f"<li>Ideal for: carnival, disco parties, 70s themes, stage performances</li>"
        f"<li>Material: High-quality synthetic fiber</li>"
        f"<li>Made in Greece</li></ul>"
    )
    se = f"<p>{prefix}curly afro wig in {color_en}. Perfect for carnival, 70s parties, and stage. Made in Athens, Greece.</p>"
    dl = (
        f"<p>Η <strong>{prefix_el}αφάνα σε {color_el} χρώμα</strong> είναι μια "
        f"{'συμπαγής αλλά' if size=='small' else 'πλήρης και' if size=='regular' else 'εντυπωσιακά μεγάλη και'} "
        f"ογκώδης σγουρή περούκα αφάνα. "
        f"Κλασική επιλογή για αποκριές και πάρτι.</p>"
        f"<ul><li>Χρώμα: {color_el.title()}</li>"
        f"<li>Στυλ: {'Μικρή' if size=='small' else 'Κανονική' if size=='regular' else 'Πολύ μεγάλη'} σγουρή αφάνα</li>"
        f"<li>Κατάλληλη για: αποκριές, ντίσκο πάρτι, θέματα 70s, παραστάσεις</li>"
        f"<li>Υλικό: Υψηλής ποιότητας συνθετική ίνα</li>"
        f"<li>Κατασκευή στην Ελλάδα</li></ul>"
    )
    sl = f"<p>{prefix_el}σγουρή αφάνα σε {color_el} χρώμα. Ιδανική για αποκριές, ντίσκο πάρτι και παραστάσεις. Κατασκευή στην Αθήνα.</p>"
    sz = f"-{size}" if size != "regular" else ""
    return d(de, se, dl, sl,
             name_en=name_en, name_el=name_el,
             slug_en=f"afro{sz}-{slug_c_en}-wig", slug_el=f"afana{sz.replace('-','-')}-{slug_c_el}",
             meta_en=f"{prefix}Afro {color_en.title()} Wig | Carnival & Party | Alegro Athens",
             meta_el=f"{prefix_el}Αφάνα {color_el.title()} | Αποκριές & Πάρτι | Alegro")

# ── Clown helper ─────────────────────────────────────────────────────────────
def clown(color_en, color_el, slug_c_en, slug_c_el):
    name_en = f"Clown {color_en.title()} Wig"
    name_el = f"Περούκα Κλόουν {color_el.title()}"
    de = (
        f"<p>The <strong>Clown {color_en.title()} Wig</strong> features the iconic "
        f"tufted clown silhouette in vivid {color_en} — big, fun, and impossible to ignore. "
        f"The perfect finishing touch for a clown costume at carnival, theatre, or any "
        f"celebration where laughter is the main act.</p>"
        f"<ul><li>Color: {color_en.title()}</li>"
        f"<li>Style: Classic clown tufts</li>"
        f"<li>Ideal for: clown costumes, carnival, theatre, children's events</li>"
        f"<li>Material: High-quality synthetic fiber</li>"
        f"<li>Made in Greece</li></ul>"
    )
    se = f"<p>Classic {color_en} clown wig with iconic tufted silhouette. Perfect for carnival, theatre, and children's parties. Made in Athens, Greece.</p>"
    dl = (
        f"<p>Η <strong>περούκα Κλόουν σε {color_el} χρώμα</strong> διαθέτει το εμβληματικό "
        f"σχέδιο κλόουν σε ζωντανό {color_el} χρώμα — μεγάλη, διασκεδαστική και αδύνατο "
        f"να αγνοηθεί. Η τέλεια τελική πινελιά για ένα κοστούμι κλόουν.</p>"
        f"<ul><li>Χρώμα: {color_el.title()}</li>"
        f"<li>Στυλ: Κλασικές φουντίτσες κλόουν</li>"
        f"<li>Κατάλληλη για: κοστούμι κλόουν, αποκριές, θέατρο, παιδικές εκδηλώσεις</li>"
        f"<li>Υλικό: Υψηλής ποιότητας συνθετική ίνα</li>"
        f"<li>Κατασκευή στην Ελλάδα</li></ul>"
    )
    sl = f"<p>Κλασική περούκα κλόουν σε {color_el} χρώμα. Ιδανική για αποκριές, θέατρο και παιδικές εκδηλώσεις. Κατασκευή στην Αθήνα.</p>"
    return d(de, se, dl, sl,
             name_en=name_en, name_el=name_el,
             slug_en=f"clown-{slug_c_en}-wig", slug_el=f"perouka-kloun-{slug_c_el}",
             meta_en=f"Clown {color_en.title()} Wig | Carnival & Theatre | Alegro Athens",
             meta_el=f"Περούκα Κλόουν {color_el.title()} | Αποκριές & Θέατρο | Alegro")

# ── Mohawk helper ─────────────────────────────────────────────────────────────
def mohawk(color_en, color_el, slug_c_en, slug_c_el):
    name_en = f"Mohawk {color_en.title()} Wig"
    name_el = f"Περούκα Μοϊκανός {color_el.title()}"
    de = (
        f"<p>The <strong>Mohawk {color_en.title()} Wig</strong> features a dramatic "
        f"standing Mohawk crest in bold {color_en} — the ultimate symbol of punk rebellion "
        f"and rock attitude. Instantly recognisable and impossible to ignore at any "
        f"costume event, carnival, or themed party.</p>"
        f"<ul><li>Color: {color_en.title()}</li>"
        f"<li>Style: Standing Mohawk crest</li>"
        f"<li>Ideal for: punk costumes, rock themes, carnival, stage performances</li>"
        f"<li>Material: High-quality synthetic fiber</li>"
        f"<li>Made in Greece</li></ul>"
    )
    se = f"<p>{color_en.title()} Mohawk wig with standing crest. Perfect for punk and rock costumes, carnival, and themed events. Made in Athens, Greece.</p>"
    dl = (
        f"<p>Η <strong>περούκα Μοϊκανός σε {color_el} χρώμα</strong> διαθέτει εντυπωσιακή "
        f"όρθια λοφιά σε έντονο {color_el} χρώμα — το απόλυτο σύμβολο πανκ επανάστασης "
        f"και ροκ στάσης. Αμέσως αναγνωρίσιμη σε κάθε αποκριάτικη εκδήλωση και πάρτι.</p>"
        f"<ul><li>Χρώμα: {color_el.title()}</li>"
        f"<li>Στυλ: Όρθια λοφιά μοϊκανού</li>"
        f"<li>Κατάλληλη για: πανκ κοστούμια, ροκ θέματα, αποκριές, παραστάσεις</li>"
        f"<li>Υλικό: Υψηλής ποιότητας συνθετική ίνα</li>"
        f"<li>Κατασκευή στην Ελλάδα</li></ul>"
    )
    sl = f"<p>Περούκα Μοϊκανός σε {color_el} χρώμα με όρθια λοφιά. Ιδανική για πανκ κοστούμια, αποκριές και θεματικές εκδηλώσεις. Κατασκευή στην Αθήνα.</p>"
    return d(de, se, dl, sl,
             name_en=name_en, name_el=name_el,
             slug_en=f"mohawk-{slug_c_en}-wig", slug_el=f"perouka-moikanos-{slug_c_el}",
             meta_en=f"Mohawk {color_en.title()} Wig | Punk & Rock Costume | Alegro Athens",
             meta_el=f"Περούκα Μοϊκανός {color_el.title()} | Πανκ & Ροκ | Alegro")

# ── Pippi helper ──────────────────────────────────────────────────────────────
def pippi(color_en, color_el, slug_c_en, slug_c_el):
    name_en = f"Pippi Longstocking {color_en.title()} Wig with Braids"
    name_el = f"Περούκα Πίπη Φακιδομύτη {color_el.title()} με Κοτσίδες"
    de = (
        f"<p>The <strong>Pippi Longstocking {color_en.title()} Wig</strong> brings the "
        f"world's strongest girl to life with its iconic standing pigtail braids in "
        f"{color_en}. Instantly lovable and recognisable, it's the perfect choice for "
        f"children's characters and story-book themed events.</p>"
        f"<ul><li>Color: {color_en.title()}</li>"
        f"<li>Style: Standing pigtail braids</li>"
        f"<li>Ideal for: Pippi Longstocking costumes, carnival, children's theatre, photoshoots</li>"
        f"<li>Material: High-quality synthetic fiber</li>"
        f"<li>Made in Greece</li></ul>"
    )
    se = f"<p>{color_en.title()} Pippi Longstocking wig with iconic standing braids. Perfect for children's character costumes and carnival. Made in Athens, Greece.</p>"
    dl = (
        f"<p>Η <strong>περούκα Πίπη Φακιδομύτη σε {color_el} χρώμα</strong> "
        f"δίνει ζωή στην πιο δυνατή κοπέλα στον κόσμο με τις εμβληματικές της "
        f"όρθιες κοτσίδες. Αμέσως αναγνωρίσιμη και χαριτωμένη για κάθε αποκριάτικη εκδήλωση.</p>"
        f"<ul><li>Χρώμα: {color_el.title()}</li>"
        f"<li>Στυλ: Όρθιες κοτσίδες</li>"
        f"<li>Κατάλληλη για: κοστούμι Πίπης, αποκριές, παιδικό θέατρο, φωτογραφίσεις</li>"
        f"<li>Υλικό: Υψηλής ποιότητας συνθετική ίνα</li>"
        f"<li>Κατασκευή στην Ελλάδα</li></ul>"
    )
    sl = f"<p>Περούκα Πίπη Φακιδομύτη σε {color_el} χρώμα με εμβληματικές όρθιες κοτσίδες. Ιδανική για αποκριάτικα κοστούμια. Κατασκευή στην Αθήνα.</p>"
    return d(de, se, dl, sl,
             name_en=name_en, name_el=name_el,
             slug_en=f"pippi-{slug_c_en}-wig", slug_el=f"perouka-pipi-fakidomyti-{slug_c_el}",
             meta_en=f"Pippi Longstocking {color_en.title()} Wig | Alegro Athens",
             meta_el=f"Περούκα Πίπη Φακιδομύτη {color_el.title()} | Alegro Αθήνα")

# ════════════════════════════════════════════════════════════════════════════
# PRODUCTS dict — key = product ID (int)
# ════════════════════════════════════════════════════════════════════════════
PRODUCTS = {}

# 20 — Morticia Long Black Wig
PRODUCTS[20] = d(
    "<p>The <strong>Morticia Long Black Wig</strong> captures the dark elegance of the "
    "Addams Family's matriarch. Sleek, jet-black, and flowing all the way to the waist, "
    "it is the centrepiece of an unforgettable Morticia costume for Halloween, carnival, "
    "theatre, or any gothic event.</p>"
    "<ul><li>Color: Jet black</li><li>Style: Long, straight, to the waist</li>"
    "<li>Ideal for: Morticia Addams, Halloween, gothic costumes, theatre</li>"
    "<li>Material: High-quality synthetic fiber</li><li>Made in Greece</li></ul>",
    "<p>Sleek jet-black long wig inspired by Morticia Addams. Perfect for Halloween, gothic costumes, and theatre. Made in Athens, Greece.</p>",
    "<p>Η <strong>μαύρη μακριά περούκα Μορτίσια</strong> αποτυπώνει τη σκοτεινή κομψότητα "
    "της οικογένειας Άνταμς. Λεία, κατάμαυρη, με μήκος έως τη μέση, αποτελεί τον "
    "κεντρικό πυλώνα μιας αξέχαστης μεταμφίεσης για αποκριές, Halloween ή θέατρο.</p>"
    "<ul><li>Χρώμα: Κατάμαυρο</li><li>Στυλ: Μακριά, ίσια, έως τη μέση</li>"
    "<li>Κατάλληλη για: Μορτίσια Άνταμς, Halloween, γκοθ κοστούμια, θέατρο</li>"
    "<li>Υλικό: Υψηλής ποιότητας συνθετική ίνα</li><li>Κατασκευή στην Ελλάδα</li></ul>",
    "<p>Λεία κατάμαυρη μακριά περούκα εμπνευσμένη από τη Μορτίσια Άνταμς. Ιδανική για Halloween, γκοθ κοστούμια και θέατρο. Κατασκευή στην Αθήνα.</p>",
    name_en="Morticia Long Black Wig", name_el="Μορτίσια Μαύρη Μακριά Περούκα",
    slug_en="morticia-long-black-wig", slug_el="mortisia-makria-mavri-perouka",
    meta_en="Morticia Addams Long Black Wig | Halloween & Carnival | Alegro Athens",
    meta_el="Περούκα Μορτίσια Μαύρη Μακριά | Αποκριές & Halloween | Alegro"
)

# 21–24 — Xena series
PRODUCTS[21] = xena("black", "μαύρη", "black", "mavri")
PRODUCTS[22] = xena("blonde", "ξανθιά", "blonde", "xanthia")
PRODUCTS[23] = xena("auburn", "ακαζού", "auburn", "akazou")
PRODUCTS[24] = xena("brown", "καστανή", "brown", "kastani")

# 35 — Wednesday
PRODUCTS[35] = d(
    "<p>The <strong>Wednesday Wig</strong> recreates the instantly iconic hairstyle "
    "of Wednesday Addams — two perfectly straight black pigtail braids. Simple, dark, "
    "and unmistakably Wednesday. Perfect for fans of the hit TV series and classic "
    "Addams Family fans alike.</p>"
    "<ul><li>Color: Black</li><li>Style: Straight twin braids</li>"
    "<li>Ideal for: Wednesday Addams costume, Halloween, carnival, gothic themed events</li>"
    "<li>Material: High-quality synthetic fiber</li><li>Made in Greece</li></ul>",
    "<p>Straight black twin-braid wig inspired by Wednesday Addams. Perfect for Halloween, carnival, and gothic themes. Made in Athens, Greece.</p>",
    "<p>Η <strong>περούκα Wednesday</strong> αναπαράγει το εμβληματικό χτένισμα "
    "της Wednesday Addams — δύο απόλυτα ίσιες μαύρες κοτσίδες. Απλή, σκοτεινή "
    "και αναπόφευκτα αναγνωρίσιμη. Ιδανική για φανς της τηλεοπτικής σειράς.</p>"
    "<ul><li>Χρώμα: Μαύρο</li><li>Στυλ: Ίσιες διπλές κοτσίδες</li>"
    "<li>Κατάλληλη για: κοστούμι Wednesday Addams, Halloween, αποκριές, γκοθ εκδηλώσεις</li>"
    "<li>Υλικό: Υψηλής ποιότητας συνθετική ίνα</li><li>Κατασκευή στην Ελλάδα</li></ul>",
    "<p>Ίσιες μαύρες κοτσίδες εμπνευσμένες από τη Wednesday Addams. Ιδανικές για Halloween, αποκριές και γκοθ εκδηλώσεις. Κατασκευή στην Αθήνα.</p>",
    name_en="Wednesday Addams Twin Braid Wig", name_el="Περούκα Wednesday Addams με Κοτσίδες",
    slug_en="wednesday-addams-wig", slug_el="perouka-wednesday-addams",
    meta_en="Wednesday Addams Wig | Halloween & Carnival | Alegro Athens",
    meta_el="Περούκα Wednesday Addams | Halloween & Αποκριές | Alegro"
)

# 36 — Enid
PRODUCTS[36] = d(
    "<p>The <strong>Enid Wig</strong> is inspired by Enid Sinclair from the hit series "
    "<em>Wednesday</em> — a vibrant, colourful half-and-half wig that bursts with "
    "personality. Cheerful, bold, and fun, it's the perfect counterpoint to Wednesday's "
    "dark aesthetic and a great choice for duo costumes.</p>"
    "<ul><li>Style: Colourful, half-and-half or rainbow streaks</li>"
    "<li>Ideal for: Enid Sinclair costume, duo Halloween costumes, carnival, themed parties</li>"
    "<li>Material: High-quality synthetic fiber</li><li>Made in Greece</li></ul>",
    "<p>Colourful Enid Sinclair-inspired wig from the Wednesday series. Great for duo Halloween costumes and themed parties. Made in Athens, Greece.</p>",
    "<p>Η <strong>περούκα Enid</strong> εμπνέεται από την Enid Sinclair της σειράς "
    "<em>Wednesday</em> — μια ζωηρή, πολύχρωμη περούκα γεμάτη χαρακτήρα. "
    "Χαρούμενη, τολμηρή και διασκεδαστική, είναι η τέλεια επιλογή για ντουέτο "
    "μεταμφίεσης με τη Wednesday.</p>"
    "<ul><li>Στυλ: Πολύχρωμη</li>"
    "<li>Κατάλληλη για: κοστούμι Enid, ντουέτο Halloween, αποκριές, θεματικά πάρτι</li>"
    "<li>Υλικό: Υψηλής ποιότητας συνθετική ίνα</li><li>Κατασκευή στην Ελλάδα</li></ul>",
    "<p>Πολύχρωμη περούκα εμπνευσμένη από την Enid Sinclair της σειράς Wednesday. Ιδανική για ντουέτο Halloween και θεματικά πάρτι. Κατασκευή στην Αθήνα.</p>",
    name_en="Enid Sinclair Colourful Wig", name_el="Περούκα Enid Sinclair Πολύχρωμη",
    slug_en="enid-sinclair-wig", slug_el="perouka-enid-sinclair",
    meta_en="Enid Sinclair Colourful Wig from Wednesday | Alegro Athens",
    meta_el="Περούκα Enid Sinclair από τη Wednesday | Alegro Αθήνα"
)

# 37–45 — Hero series
PRODUCTS[37] = hero("RED")
PRODUCTS[38] = hero("YELLOW")
PRODUCTS[39] = hero("PURPLE")
PRODUCTS[40] = hero("GREEN")
PRODUCTS[41] = hero("PINK")
PRODUCTS[42] = hero("BLACK")
PRODUCTS[43] = hero("AUBURN")
PRODUCTS[44] = hero("BLONDE")
PRODUCTS[45] = hero("FUCHSIA")

# 46 — Cecilia Black Bob
PRODUCTS[46] = d(
    "<p>The <strong>Cecilia Black Bob Wig</strong> is a sleek, sophisticated short bob "
    "with a neat fringe. Timeless and versatile, it suits 1920s flapper looks, retro "
    "styles, professional character costumes, and chic theatrical roles.</p>"
    "<ul><li>Color: Black</li><li>Style: Short bob with fringe</li>"
    "<li>Ideal for: 1920s/flapper costumes, retro looks, theatre, carnival</li>"
    "<li>Material: High-quality synthetic fiber</li><li>Made in Greece</li></ul>",
    "<p>Sleek black short bob wig with fringe. Ideal for 1920s, flapper, and retro costumes. Made in Athens, Greece.</p>",
    "<p>Η <strong>περούκα Σεσίλια σε μαύρο καρέ</strong> είναι ένα κομψό, σύγχρονο κοντό "
    "καρέ με τακτοποιημένη αφέλεια. Διαχρονική και ευέλικτη, ταιριάζει σε στυλ της δεκαετίας "
    "του 1920, ρετρό εμφανίσεις και θεατρικούς ρόλους.</p>"
    "<ul><li>Χρώμα: Μαύρο</li><li>Στυλ: Κοντό καρέ με αφέλεια</li>"
    "<li>Κατάλληλη για: κοστούμια 1920s/flapper, ρετρό στυλ, θέατρο, αποκριές</li>"
    "<li>Υλικό: Υψηλής ποιότητας συνθετική ίνα</li><li>Κατασκευή στην Ελλάδα</li></ul>",
    "<p>Κομψό μαύρο κοντό καρέ με αφέλεια. Ιδανικό για κοστούμια 1920s, ρετρό στυλ και θέατρο. Κατασκευή στην Αθήνα.</p>",
    name_en="Cecilia Black Bob Wig with Fringe", name_el="Περούκα Σεσίλια Μαύρο Καρέ με Αφέλεια",
    slug_en="cecilia-black-bob-wig-fringe", slug_el="perouka-sesilia-mavro-kare-afelia",
    meta_en="Cecilia Black Bob Wig with Fringe | 1920s & Retro | Alegro Athens",
    meta_el="Περούκα Σεσίλια Μαύρο Καρέ με Αφέλεια | 1920s & Ρετρό | Alegro"
)

# 47 — Cecilia Purple Bob
PRODUCTS[47] = d(
    "<p>The <strong>Cecilia Purple Bob Wig</strong> is a bold, statement short bob "
    "with a neat fringe in striking purple. Perfect for fantasy characters, theatrical "
    "performers, pop-culture looks, and anyone who wants to stand out at a party.</p>"
    "<ul><li>Color: Purple</li><li>Style: Short bob with fringe</li>"
    "<li>Ideal for: fantasy characters, theatrical roles, carnival, themed parties</li>"
    "<li>Material: High-quality synthetic fiber</li><li>Made in Greece</li></ul>",
    "<p>Bold purple short bob wig with fringe. Perfect for fantasy characters, theatrical roles, and carnival. Made in Athens, Greece.</p>",
    "<p>Η <strong>περούκα Σεσίλια σε μωβ καρέ</strong> είναι ένα τολμηρό κοντό καρέ "
    "με αφέλεια σε εντυπωσιακό μωβ χρώμα. Ιδανική για χαρακτήρες φαντασίας, "
    "θεατρικές παραστάσεις και θεματικά πάρτι.</p>"
    "<ul><li>Χρώμα: Μωβ</li><li>Στυλ: Κοντό καρέ με αφέλεια</li>"
    "<li>Κατάλληλη για: χαρακτήρες φαντασίας, θεατρικοί ρόλοι, αποκριές, πάρτι</li>"
    "<li>Υλικό: Υψηλής ποιότητας συνθετική ίνα</li><li>Κατασκευή στην Ελλάδα</li></ul>",
    "<p>Τολμηρό μωβ κοντό καρέ με αφέλεια. Ιδανικό για χαρακτήρες φαντασίας, θεατρικούς ρόλους και αποκριές. Κατασκευή στην Αθήνα.</p>",
    name_en="Cecilia Purple Bob Wig with Fringe", name_el="Περούκα Σεσίλια Μωβ Καρέ με Αφέλεια",
    slug_en="cecilia-purple-bob-wig-fringe", slug_el="perouka-sesilia-mov-kare-afelia",
    meta_en="Cecilia Purple Bob Wig with Fringe | Fantasy & Theatre | Alegro Athens",
    meta_el="Περούκα Σεσίλια Μωβ Καρέ | Φαντασία & Θέατρο | Alegro"
)

# ── Style series: Nora, Stella, Peggy ────────────────────────────────────────
def style_wig(series, color_en, color_el, style_desc_en, style_desc_el, pid_slug_en, pid_slug_el, name_en_override="", name_el_override=""):
    name_en = name_en_override or f"{series} {color_en.title()} Wig"
    name_el = name_el_override or f"Περούκα {series} {color_el.title()}"
    de = (
        f"<p>The <strong>{series} {color_en.title()} Wig</strong> is {style_desc_en}. "
        f"A versatile, stylish option for theatrical productions, carnival costumes, "
        f"photoshoots, and entertainment events.</p>"
        f"<ul><li>Color: {color_en.title()}</li>"
        f"<li>Ideal for: theatre, carnival, photoshoots, entertainment events</li>"
        f"<li>Material: High-quality synthetic fiber</li><li>Made in Greece</li></ul>"
    )
    se = f"<p>{series} {color_en} wig — {style_desc_en[:60]}. Made in Athens, Greece.</p>"
    dl = (
        f"<p>Η <strong>περούκα {series} σε {color_el} χρώμα</strong> είναι {style_desc_el}. "
        f"Μια ευέλικτη, κομψή επιλογή για θεατρικές παραστάσεις, αποκριάτικα κοστούμια, "
        f"φωτογραφίσεις και ψυχαγωγικές εκδηλώσεις.</p>"
        f"<ul><li>Χρώμα: {color_el.title()}</li>"
        f"<li>Κατάλληλη για: θέατρο, αποκριές, φωτογραφίσεις, ψυχαγωγικές εκδηλώσεις</li>"
        f"<li>Υλικό: Υψηλής ποιότητας συνθετική ίνα</li><li>Κατασκευή στην Ελλάδα</li></ul>"
    )
    sl = f"<p>Περούκα {series} σε {color_el} χρώμα. Ιδανική για θέατρο, αποκριές και φωτογραφίσεις. Κατασκευή στην Αθήνα.</p>"
    return d(de, se, dl, sl,
             name_en=name_en, name_el=name_el,
             slug_en=pid_slug_en, slug_el=pid_slug_el,
             meta_en=f"{name_en} | Alegro Athens", meta_el=f"{name_el} | Alegro")

# 130–131 — Nora
PRODUCTS[130] = style_wig("Nora","blonde","ξανθιά",
    "a flowing medium-length wig with soft, natural-looking blonde tones",
    "μια ρέουσα περούκα μεσαίου μήκους με απαλές, φυσικές ξανθές αποχρώσεις",
    "nora-blonde-wig","perouka-nora-xanthia")
PRODUCTS[131] = style_wig("Nora","auburn","ακαζού",
    "a flowing medium-length wig in warm auburn tones",
    "μια ρέουσα περούκα μεσαίου μήκους σε ζεστές ακαζού αποχρώσεις",
    "nora-auburn-wig","perouka-nora-akazou")

# 132–134 — Stella
PRODUCTS[132] = style_wig("Stella","black","μαύρη",
    "a glamorous, full-bodied wig with glossy black waves",
    "μια γοητευτική, ογκώδης περούκα με γυαλιστερά μαύρα κύματα",
    "stella-black-wig","perouka-stella-mavri")
PRODUCTS[133] = style_wig("Stella","blonde","ξανθιά",
    "a glamorous, full-bodied wig with radiant blonde waves",
    "μια γοητευτική, ογκώδης περούκα με λαμπερά ξανθά κύματα",
    "stella-blonde-wig","perouka-stella-xanthia")
PRODUCTS[134] = style_wig("Stella","light brown","ανοιχτό καστανό",
    "a glamorous, full-bodied wig in soft light-brown waves",
    "μια γοητευτική, ογκώδης περούκα σε απαλά ανοιχτά καστανά κύματα",
    "stella-light-brown-wig","perouka-stella-anoixto-kastano")

# 135–137 — Peggy
PRODUCTS[135] = style_wig("Peggy","black","μαύρη",
    "a short, sleek black wig with a classic feminine silhouette",
    "μια κοντή, λεία μαύρη περούκα με κλασική γυναικεία σιλουέτα",
    "peggy-black-wig","perouka-peggy-mavri")
PRODUCTS[136] = style_wig("Peggy","blonde","ξανθιά",
    "a short, sleek blonde wig with a classic retro silhouette",
    "μια κοντή, λεία ξανθιά περούκα με κλασική ρετρό σιλουέτα",
    "peggy-blonde-wig","perouka-peggy-xanthia")
PRODUCTS[137] = style_wig("Peggy","auburn","ακαζού",
    "a short, sleek auburn wig with a classic feminine silhouette",
    "μια κοντή, λεία ακαζού περούκα με κλασική γυναικεία σιλουέτα",
    "peggy-auburn-wig","perouka-peggy-akazou")

# 138 — Dalia
PRODUCTS[138] = d(
    "<p>The <strong>Dalia Blonde Wavy Wig</strong> is a long, flowing wig with "
    "beautiful soft waves in warm blonde. Romantic and natural-looking, it's ideal "
    "for theatrical roles that call for an effortlessly elegant, feminine look.</p>"
    "<ul><li>Color: Blonde</li><li>Style: Long, wavy</li>"
    "<li>Ideal for: theatre, romantic character roles, photoshoots, carnival</li>"
    "<li>Material: High-quality synthetic fiber</li><li>Made in Greece</li></ul>",
    "<p>Long blonde wavy wig — romantic and natural-looking. Perfect for theatrical roles and photoshoots. Made in Athens, Greece.</p>",
    "<p>Η <strong>περούκα Νταλία ξανθιά κυματιστή</strong> είναι μια μακριά, ρέουσα "
    "περούκα με όμορφα απαλά κύματα σε ζεστό ξανθό χρώμα. Ρομαντική και φυσική, "
    "ιδανική για θεατρικούς ρόλους και φωτογραφίσεις.</p>"
    "<ul><li>Χρώμα: Ξανθιά</li><li>Στυλ: Μακριά, κυματιστή</li>"
    "<li>Κατάλληλη για: θέατρο, ρομαντικοί χαρακτήρες, φωτογραφίσεις, αποκριές</li>"
    "<li>Υλικό: Υψηλής ποιότητας συνθετική ίνα</li><li>Κατασκευή στην Ελλάδα</li></ul>",
    "<p>Μακριά ξανθιά κυματιστή περούκα, ρομαντική και φυσική. Ιδανική για θεατρικούς ρόλους και φωτογραφίσεις. Κατασκευή στην Αθήνα.</p>",
    name_en="Dalia Blonde Long Wavy Wig", name_el="Περούκα Νταλία Ξανθιά Μακριά Κυματιστή",
    slug_en="dalia-blonde-long-wavy-wig", slug_el="perouka-ntalia-xanthia-makria-kymatisti",
    meta_en="Dalia Blonde Long Wavy Wig | Theatre & Carnival | Alegro Athens",
    meta_el="Περούκα Νταλία Ξανθιά Κυματιστή | Θέατρο & Αποκριές | Alegro"
)

# 139–142 — Daphnes series
def daphnes(color_en, color_el, slug_c_en, slug_c_el):
    return style_wig("Daphnes", color_en, color_el,
        f"a long, curly wig in rich {color_en} — inspired by the spirited heroines of adventure",
        f"μια μακριά, σγουρή περούκα σε πλούσιο {color_el} χρώμα — εμπνευσμένη από τολμηρές ηρωίδες περιπέτειας",
        f"daphnes-{slug_c_en}-wig", f"perouka-daphnes-{slug_c_el}")

PRODUCTS[139] = daphnes("black","μαύρη","black","mavri")
PRODUCTS[140] = daphnes("blonde","ξανθιά","blonde","xanthia")
PRODUCTS[141] = daphnes("red","κόκκινη","red","kokkini")
PRODUCTS[142] = daphnes("light brown","ανοιχτό καστανό","light-brown","anoixto-kastano")

# 143–144 — Samantha
def samantha(color_en, color_el, slug_c_en, slug_c_el):
    return style_wig("Samantha", color_en, color_el,
        f"a chic, medium-length {color_en} wig with smooth, polished styling",
        f"μια κομψή περούκα μεσαίου μήκους σε {color_el} χρώμα με λεία, γυαλισμένη εμφάνιση",
        f"samantha-{slug_c_en}-wig", f"perouka-samantha-{slug_c_el}")

PRODUCTS[143] = samantha("blonde","ξανθιά","blonde","xanthia")
PRODUCTS[144] = samantha("black","μαύρη","black","mavri")

# 145–146 — Ancient Greek Girl
def ancient_greek(color_en, color_el, slug_c_en, slug_c_el):
    name_en = f"Ancient Greek Girl {color_en.title()} Wig"
    name_el = f"Περούκα Αρχαία Ελληνίδα {color_el.title()}"
    de = (
        f"<p>The <strong>Ancient Greek Girl {color_en.title()} Wig</strong> evokes the "
        f"classical beauty of ancient Greece, with long {color_en} hair styled in an "
        f"elegant upswept arrangement. Perfect for historical theatrical productions, "
        f"mythology-themed events, school plays, and carnival costumes inspired by "
        f"the ancient world.</p>"
        f"<ul><li>Color: {color_en.title()}</li>"
        f"<li>Style: Long, classically styled</li>"
        f"<li>Ideal for: ancient Greece / mythology themes, school plays, theatre, carnival</li>"
        f"<li>Material: High-quality synthetic fiber</li><li>Made in Greece</li></ul>"
    )
    se = f"<p>Long {color_en} wig in ancient Greek style. Ideal for mythology themes, historical theatre, and carnival. Made in Athens, Greece.</p>"
    dl = (
        f"<p>Η <strong>περούκα Αρχαία Ελληνίδα σε {color_el} χρώμα</strong> "
        f"αποπνέει την κλασική ομορφιά της αρχαίας Ελλάδας, με μακριά {color_el} μαλλιά "
        f"σε κομψό κλασικό ανέβασμα. Ιδανική για ιστορικές θεατρικές παραστάσεις, "
        f"εκδηλώσεις με θέμα τη μυθολογία και αποκριάτικα κοστούμια.</p>"
        f"<ul><li>Χρώμα: {color_el.title()}</li>"
        f"<li>Στυλ: Μακριά, κλασικά χτενισμένη</li>"
        f"<li>Κατάλληλη για: αρχαία Ελλάδα / μυθολογία, σχολικές παραστάσεις, θέατρο, αποκριές</li>"
        f"<li>Υλικό: Υψηλής ποιότητας συνθετική ίνα</li><li>Κατασκευή στην Ελλάδα</li></ul>"
    )
    sl = f"<p>Μακριά {color_el} περούκα σε στυλ αρχαίας Ελληνίδας. Ιδανική για μυθολογικά θέματα, θέατρο και αποκριές. Κατασκευή στην Αθήνα.</p>"
    return d(de, se, dl, sl,
             name_en=name_en, name_el=name_el,
             slug_en=f"ancient-greek-girl-{slug_c_en}-wig", slug_el=f"perouka-arxaia-ellinika-{slug_c_el}",
             meta_en=f"Ancient Greek Girl {color_en.title()} Wig | Mythology & Theatre | Alegro Athens",
             meta_el=f"Περούκα Αρχαία Ελληνίδα {color_el.title()} | Μυθολογία & Θέατρο | Alegro")

PRODUCTS[145] = ancient_greek("black","μαύρη","black","mavri")
PRODUCTS[146] = ancient_greek("blonde","ξανθιά","blonde","xanthia")

# 147 — Count White
PRODUCTS[147] = d(
    "<p>The <strong>Count White Wig</strong> is a refined, powdered-style white wig "
    "evoking the aristocratic elegance of 18th-century European nobility. With its "
    "structured curls and stately presence, it is the perfect choice for Count, "
    "Marquis, and nobleman character costumes.</p>"
    "<ul><li>Color: White (powdered)</li><li>Style: 18th-century aristocratic curls</li>"
    "<li>Ideal for: Count, Marquis, nobleman costumes, period theatre, carnival</li>"
    "<li>Material: High-quality synthetic fiber</li><li>Made in Greece</li></ul>",
    "<p>White powdered aristocratic wig in 18th-century style. Perfect for Count and nobleman costumes, period theatre, and carnival. Made in Athens, Greece.</p>",
    "<p>Η <strong>περούκα Κόμης σε λευκό χρώμα</strong> είναι μια εκλεπτυσμένη, "
    "πουδραρισμένη λευκή περούκα που αποπνέει την αριστοκρατική κομψότητα της "
    "Ευρώπης του 18ου αιώνα. Με δομημένες μπούκλες και επίσημη παρουσία.</p>"
    "<ul><li>Χρώμα: Λευκό (πουδρέ)</li><li>Στυλ: Αριστοκρατικές μπούκλες 18ου αιώνα</li>"
    "<li>Κατάλληλη για: κοστούμι Κόμη, Μαρκήσιου, αριστοκράτη, ιστορικό θέατρο, αποκριές</li>"
    "<li>Υλικό: Υψηλής ποιότητας συνθετική ίνα</li><li>Κατασκευή στην Ελλάδα</li></ul>",
    "<p>Λευκή πουδρέ αριστοκρατική περούκα 18ου αιώνα. Ιδανική για κοστούμι Κόμη, ιστορικό θέατρο και αποκριές. Κατασκευή στην Αθήνα.</p>",
    name_en="Count White Aristocratic Wig", name_el="Περούκα Κόμης Λευκή Αριστοκρατική",
    slug_en="count-white-aristocratic-wig", slug_el="perouka-komis-lefki-aristokratiki",
    meta_en="Count White 18th-Century Aristocratic Wig | Theatre & Carnival | Alegro Athens",
    meta_el="Περούκα Κόμης Λευκή 18ου Αιώνα | Θέατρο & Αποκριές | Alegro"
)

# 148–149 — Judge wigs
def judge(color_en, color_el, slug_c_en, slug_c_el):
    name_en = f"Judge {color_en.title()} Wig"
    name_el = f"Περούκα Δικαστής {color_el.title()}"
    de = (
        f"<p>The <strong>Judge {color_en.title()} Wig</strong> is the authentic-looking "
        f"curly {color_en} wig worn by British and colonial-era judges. "
        f"A classic of legal and period drama costumes, it brings instant authority "
        f"and gravitas to any character.</p>"
        f"<ul><li>Color: {color_en.title()}</li>"
        f"<li>Style: Curly judicial wig</li>"
        f"<li>Ideal for: judge / barrister costumes, period theatre, Halloween, carnival</li>"
        f"<li>Material: High-quality synthetic fiber</li><li>Made in Greece</li></ul>"
    )
    se = f"<p>{color_en.title()} curly judicial wig for judge and barrister costumes. Perfect for period theatre, Halloween, and carnival. Made in Athens, Greece.</p>"
    dl = (
        f"<p>Η <strong>περούκα Δικαστής σε {color_el} χρώμα</strong> αναπαράγει "
        f"την αυθεντική σγουρή {color_el} περούκα των Βρετανών και αποικιακών δικαστών. "
        f"Κλασική επιλογή για κοστούμια νομικής και ιστορικής δραματολογίας.</p>"
        f"<ul><li>Χρώμα: {color_el.title()}</li>"
        f"<li>Στυλ: Σγουρή δικαστική περούκα</li>"
        f"<li>Κατάλληλη για: κοστούμι δικαστή / δικηγόρου, ιστορικό θέατρο, Halloween, αποκριές</li>"
        f"<li>Υλικό: Υψηλής ποιότητας συνθετική ίνα</li><li>Κατασκευή στην Ελλάδα</li></ul>"
    )
    sl = f"<p>Σγουρή {color_el} δικαστική περούκα. Ιδανική για κοστούμι δικαστή, ιστορικό θέατρο και αποκριές. Κατασκευή στην Αθήνα.</p>"
    return d(de, se, dl, sl,
             name_en=name_en, name_el=name_el,
             slug_en=f"judge-{slug_c_en}-wig", slug_el=f"perouka-dikastis-{slug_c_el}",
             meta_en=f"Judge {color_en.title()} Wig | Period Theatre & Carnival | Alegro Athens",
             meta_el=f"Περούκα Δικαστής {color_el.title()} | Ιστορικό Θέατρο | Alegro")

PRODUCTS[148] = judge("grey","γκρι","grey","gri")
PRODUCTS[149] = judge("brown","καστανή","brown","kastani")

# 150 — D'Artagnan
PRODUCTS[150] = d(
    "<p>The <strong>D'Artagnan Wig</strong> captures the dashing, adventurous spirit "
    "of the legendary Musketeer. With its long, flowing waves and swashbuckling flair, "
    "it completes any Three Musketeers or 17th-century cavalier costume perfectly.</p>"
    "<ul><li>Style: Long wavy, with period flair</li>"
    "<li>Ideal for: Three Musketeers, cavalier costumes, period theatre, carnival</li>"
    "<li>Material: High-quality synthetic fiber</li><li>Made in Greece</li></ul>",
    "<p>Long wavy D'Artagnan Musketeer wig. Perfect for Three Musketeers costumes and period theatre. Made in Athens, Greece.</p>",
    "<p>Η <strong>περούκα D'Artagnan</strong> αποτυπώνει το θαρραλέο, περιπετειώδες πνεύμα "
    "του θρυλικού Μουσκετέρου. Με μακριές, ρέουσες κυματιστές ίνες, "
    "συμπληρώνει τέλεια κάθε κοστούμι Τριών Μουσκετέρων.</p>"
    "<ul><li>Στυλ: Μακριά κυματιστή, με ύφος εποχής</li>"
    "<li>Κατάλληλη για: Τρεις Μουσκετέροι, κοστούμια ιππότη, ιστορικό θέατρο, αποκριές</li>"
    "<li>Υλικό: Υψηλής ποιότητας συνθετική ίνα</li><li>Κατασκευή στην Ελλάδα</li></ul>",
    "<p>Μακριά κυματιστή περούκα D'Artagnan Μουσκετέρου. Ιδανική για κοστούμια Τριών Μουσκετέρων και ιστορικό θέατρο. Κατασκευή στην Αθήνα.</p>",
    name_en="D'Artagnan Musketeer Wig", name_el="Περούκα D'Artagnan Μουσκετέρος",
    slug_en="dartagnan-musketeer-wig", slug_el="perouka-dartagnan-mousketeros",
    meta_en="D'Artagnan Three Musketeers Wig | Period Theatre & Carnival | Alegro Athens",
    meta_el="Περούκα D'Artagnan Μουσκετέρος | Ιστορικό Θέατρο & Αποκριές | Alegro"
)

# 151–154 — Madame Pompadour series
def pompadour(color_en, color_el, slug_c_en, slug_c_el):
    name_en = f"Madame Pompadour {color_en.title()} Wig"
    name_el = f"Περούκα Μαντάμ Πομπαντούρ {color_el.title()}"
    de = (
        f"<p>The <strong>Madame Pompadour {color_en.title()} Wig</strong> embodies the "
        f"grandeur and extravagance of 18th-century French court fashion. Towering, "
        f"elaborate, and unmistakably regal in {color_en}, it is the ultimate statement "
        f"piece for Rococo and Marie Antoinette-inspired costumes.</p>"
        f"<ul><li>Color: {color_en.title()}</li>"
        f"<li>Style: Tall, elaborate 18th-century French court wig</li>"
        f"<li>Ideal for: Marie Antoinette, Rococo, Versailles-themed costumes, period theatre, carnival</li>"
        f"<li>Material: High-quality synthetic fiber</li><li>Made in Greece</li></ul>"
    )
    se = f"<p>Tall, elaborate {color_en} Madame Pompadour wig in 18th-century French court style. Perfect for Marie Antoinette and Rococo costumes. Made in Athens, Greece.</p>"
    dl = (
        f"<p>Η <strong>περούκα Μαντάμ Πομπαντούρ σε {color_el} χρώμα</strong> "
        f"ενσαρκώνει τη μεγαλοπρέπεια και την υπερβολή της γαλλικής αυλής του 18ου αιώνα. "
        f"Ψηλή, περίτεχνη και αναμφίβολα βασιλική, είναι η απόλυτη πρόταση για "
        f"κοστούμια σε στυλ Ροκοκό και Μαρίας Αντουανέτας.</p>"
        f"<ul><li>Χρώμα: {color_el.title()}</li>"
        f"<li>Στυλ: Ψηλή, περίτεχνη περούκα γαλλικής αυλής 18ου αιώνα</li>"
        f"<li>Κατάλληλη για: Μαρία Αντουανέτα, Ροκοκό, Βερσαλλίες, ιστορικό θέατρο, αποκριές</li>"
        f"<li>Υλικό: Υψηλής ποιότητας συνθετική ίνα</li><li>Κατασκευή στην Ελλάδα</li></ul>"
    )
    sl = f"<p>Ψηλή, περίτεχνη {color_el} περούκα Μαντάμ Πομπαντούρ. Ιδανική για κοστούμια Μαρίας Αντουανέτας και Ροκοκό. Κατασκευή στην Αθήνα.</p>"
    return d(de, se, dl, sl,
             name_en=name_en, name_el=name_el,
             slug_en=f"madame-pompadour-{slug_c_en}-wig", slug_el=f"perouka-madame-pompadour-{slug_c_el}",
             meta_en=f"Madame Pompadour {color_en.title()} Wig | 18th Century & Carnival | Alegro Athens",
             meta_el=f"Περούκα Μαντάμ Πομπαντούρ {color_el.title()} | 18ος Αιώνας & Αποκριές | Alegro")

PRODUCTS[151] = pompadour("white","λευκή","white","lefki")
PRODUCTS[152] = pompadour("blonde","ξανθιά","blonde","xanthia")
PRODUCTS[153] = pompadour("light blue","γαλάζια","light-blue","galazia")
PRODUCTS[154] = pompadour("pink","ροζ","pink","roz")

# 155–156 — Duchess
def duchess(color_en, color_el, slug_c_en, slug_c_el):
    name_en = f"Duchess {color_en.title()} Wig"
    name_el = f"Περούκα Δούκισσα {color_el.title()}"
    de = (
        f"<p>The <strong>Duchess {color_en.title()} Wig</strong> radiates aristocratic "
        f"elegance with its softly curled, voluminous {color_en} styling — evoking the "
        f"grace of 18th-century European nobility. The ideal choice for Duchess, "
        f"Countess, and noblewoman costume roles.</p>"
        f"<ul><li>Color: {color_en.title()}</li>"
        f"<li>Style: Softly curled, voluminous aristocratic wig</li>"
        f"<li>Ideal for: Duchess/Countess costumes, period theatre, carnival, royal themes</li>"
        f"<li>Material: High-quality synthetic fiber</li><li>Made in Greece</li></ul>"
    )
    se = f"<p>Voluminous {color_en} Duchess wig with soft curls in 18th-century aristocratic style. Perfect for noblewoman costumes and period theatre. Made in Athens, Greece.</p>"
    dl = (
        f"<p>Η <strong>περούκα Δούκισσα σε {color_el} χρώμα</strong> "
        f"αποπνέει αριστοκρατική κομψότητα με απαλές μπούκλες σε ογκώδες {color_el} στυλ "
        f"— ανακαλεί τη χάρη της ευρωπαϊκής αριστοκρατίας του 18ου αιώνα.</p>"
        f"<ul><li>Χρώμα: {color_el.title()}</li>"
        f"<li>Στυλ: Απαλά σγουρή, ογκώδης αριστοκρατική περούκα</li>"
        f"<li>Κατάλληλη για: κοστούμια Δούκισσας/Κόμισσας, ιστορικό θέατρο, αποκριές, βασιλικά θέματα</li>"
        f"<li>Υλικό: Υψηλής ποιότητας συνθετική ίνα</li><li>Κατασκευή στην Ελλάδα</li></ul>"
    )
    sl = f"<p>Ογκώδης {color_el} περούκα Δούκισσας με απαλές μπούκλες σε αριστοκρατικό στυλ. Ιδανική για κοστούμια αριστοκράτισσας και ιστορικό θέατρο. Κατασκευή στην Αθήνα.</p>"
    return d(de, se, dl, sl,
             name_en=name_en, name_el=name_el,
             slug_en=f"duchess-{slug_c_en}-wig", slug_el=f"perouka-doukissa-{slug_c_el}",
             meta_en=f"Duchess {color_en.title()} Aristocratic Wig | Theatre & Carnival | Alegro Athens",
             meta_el=f"Περούκα Δούκισσα {color_el.title()} | Ιστορικό Θέατρο & Αποκριές | Alegro")

PRODUCTS[155] = duchess("blonde","ξανθιά","blonde","xanthia")
PRODUCTS[156] = duchess("white","λευκή","white","lefki")

# 157 — Countess
PRODUCTS[157] = d(
    "<p>The <strong>Countess Wig</strong> exudes refined aristocratic elegance with its "
    "elaborately styled curls and stately silhouette, inspired by the grand ladies of "
    "European Baroque and Rococo courts. Perfect for Countess, noblewoman, and "
    "high-society character costumes.</p>"
    "<ul><li>Style: Elaborate curled aristocratic wig</li>"
    "<li>Ideal for: Countess / noblewoman costumes, Baroque/Rococo themes, period theatre, carnival</li>"
    "<li>Material: High-quality synthetic fiber</li><li>Made in Greece</li></ul>",
    "<p>Elaborately styled aristocratic Countess wig. Perfect for Baroque and Rococo-themed costumes and period theatre. Made in Athens, Greece.</p>",
    "<p>Η <strong>περούκα Κόμισσα</strong> αποπνέει εκλεπτυσμένη αριστοκρατική κομψότητα "
    "με περίτεχνες μπούκλες και επίσημη σιλουέτα, εμπνευσμένη από τις μεγάλες κυρίες "
    "των Βαρόκ και Ροκοκό αυλών της Ευρώπης.</p>"
    "<ul><li>Στυλ: Περίτεχνη σγουρή αριστοκρατική περούκα</li>"
    "<li>Κατάλληλη για: κοστούμι Κόμισσας / αριστοκράτισσας, Βαρόκ / Ροκοκό θέματα, ιστορικό θέατρο, αποκριές</li>"
    "<li>Υλικό: Υψηλής ποιότητας συνθετική ίνα</li><li>Κατασκευή στην Ελλάδα</li></ul>",
    "<p>Περίτεχνη αριστοκρατική περούκα Κόμισσας. Ιδανική για Βαρόκ / Ροκοκό θέματα και ιστορικό θέατρο. Κατασκευή στην Αθήνα.</p>",
    name_en="Countess Aristocratic Wig", name_el="Περούκα Κόμισσα Αριστοκρατική",
    slug_en="countess-aristocratic-wig", slug_el="perouka-komissa-aristokratiki",
    meta_en="Countess Aristocratic Wig | Baroque & Rococo | Alegro Athens",
    meta_el="Περούκα Κόμισσα Αριστοκρατική | Βαρόκ & Ροκοκό | Alegro"
)

# 158 — Duke
PRODUCTS[158] = d(
    "<p>The <strong>Duke Wig</strong> is a distinguished men's aristocratic wig "
    "with elegant powdered curls, capturing the commanding presence of an 18th-century "
    "European duke or nobleman. The perfect choice for formal period-drama roles and "
    "Baroque costume events.</p>"
    "<ul><li>Style: Powdered curls, men's 18th-century aristocratic</li>"
    "<li>Ideal for: Duke / nobleman costumes, period theatre, Baroque themes, carnival</li>"
    "<li>Material: High-quality synthetic fiber</li><li>Made in Greece</li></ul>",
    "<p>Distinguished men's aristocratic Duke wig with powdered curls. Perfect for 18th-century and Baroque-themed costumes. Made in Athens, Greece.</p>",
    "<p>Η <strong>περούκα Δούκας</strong> είναι μια εκλεπτυσμένη ανδρική αριστοκρατική "
    "περούκα με κομψές πουδραρισμένες μπούκλες, που αποτυπώνει την επιβλητική παρουσία "
    "ενός ευρωπαίου δούκα του 18ου αιώνα.</p>"
    "<ul><li>Στυλ: Πουδραρισμένες μπούκλες, ανδρική αριστοκρατική 18ου αιώνα</li>"
    "<li>Κατάλληλη για: κοστούμι Δούκα / αριστοκράτη, ιστορικό θέατρο, Βαρόκ θέματα, αποκριές</li>"
    "<li>Υλικό: Υψηλής ποιότητας συνθετική ίνα</li><li>Κατασκευή στην Ελλάδα</li></ul>",
    "<p>Εκλεπτυσμένη ανδρική αριστοκρατική περούκα Δούκα με πουδραρισμένες μπούκλες. Ιδανική για κοστούμια 18ου αιώνα και Βαρόκ θέματα. Κατασκευή στην Αθήνα.</p>",
    name_en="Duke Men's Aristocratic Wig", name_el="Περούκα Δούκας Ανδρική Αριστοκρατική",
    slug_en="duke-mens-aristocratic-wig", slug_el="perouka-doukas-andriki-aristokratiki",
    meta_en="Duke Men's Aristocratic Wig | 18th Century & Baroque | Alegro Athens",
    meta_el="Περούκα Δούκας Ανδρική | 18ος Αιώνας & Βαρόκ | Alegro"
)

# 159–161 — Marquis series
def marquis(color_en, color_el, slug_c_en, slug_c_el):
    name_en = f"Marquis {color_en.title()} Wig"
    name_el = f"Περούκα Μαρκήσιος {color_el.title()}"
    de = (
        f"<p>The <strong>Marquis {color_en.title()} Wig</strong> is a men's aristocratic "
        f"wig with flowing side curls and a formal queue, evoking the cultured elegance "
        f"of Baroque and Rococo-era European marquises. A distinguished addition to any "
        f"period costume.</p>"
        f"<ul><li>Color: {color_en.title()}</li>"
        f"<li>Style: Side curls, period aristocratic men's wig</li>"
        f"<li>Ideal for: Marquis / nobleman costumes, Baroque/Rococo theatre, carnival</li>"
        f"<li>Material: High-quality synthetic fiber</li><li>Made in Greece</li></ul>"
    )
    se = f"<p>{color_en.title()} Marquis aristocratic wig with side curls. Perfect for Baroque and Rococo nobleman costumes. Made in Athens, Greece.</p>"
    dl = (
        f"<p>Η <strong>περούκα Μαρκήσιος σε {color_el} χρώμα</strong> είναι μια "
        f"ανδρική αριστοκρατική περούκα με πλευρικές μπούκλες, που αποτυπώνει την "
        f"εκλεπτυσμένη κομψότητα των ευρωπαίων μαρκήσιων της εποχής Βαρόκ και Ροκοκό.</p>"
        f"<ul><li>Χρώμα: {color_el.title()}</li>"
        f"<li>Στυλ: Πλευρικές μπούκλες, ανδρική αριστοκρατική περούκα εποχής</li>"
        f"<li>Κατάλληλη για: κοστούμι Μαρκήσιου / αριστοκράτη, Βαρόκ / Ροκοκό θέατρο, αποκριές</li>"
        f"<li>Υλικό: Υψηλής ποιότητας συνθετική ίνα</li><li>Κατασκευή στην Ελλάδα</li></ul>"
    )
    sl = f"<p>Ανδρική αριστοκρατική περούκα Μαρκήσιου σε {color_el} χρώμα. Ιδανική για κοστούμια Βαρόκ και Ροκοκό. Κατασκευή στην Αθήνα.</p>"
    return d(de, se, dl, sl,
             name_en=name_en, name_el=name_el,
             slug_en=f"marquis-{slug_c_en}-wig", slug_el=f"perouka-markisios-{slug_c_el}",
             meta_en=f"Marquis {color_en.title()} Wig | Baroque Nobleman Costume | Alegro Athens",
             meta_el=f"Περούκα Μαρκήσιος {color_el.title()} | Κοστούμι Βαρόκ | Alegro")

PRODUCTS[159] = marquis("auburn","ακαζού","auburn","akazou")
PRODUCTS[160] = marquis("brown","καστανή","brown","kastani")
PRODUCTS[161] = marquis("white","λευκή","white","lefki")

# 162 — Charlotte
PRODUCTS[162] = d(
    "<p>The <strong>Charlotte Wig</strong> is a soft, romantic medium-length wig "
    "with gentle curls and an old-world charm. Elegant yet approachable, it suits a "
    "wide range of period and storybook characters — from 19th-century heroines "
    "to fairytale princesses.</p>"
    "<ul><li>Style: Medium-length with soft curls</li>"
    "<li>Ideal for: period heroines, storybook characters, theatre, carnival</li>"
    "<li>Material: High-quality synthetic fiber</li><li>Made in Greece</li></ul>",
    "<p>Romantic medium-length curly Charlotte wig with old-world charm. Perfect for period heroines and storybook characters. Made in Athens, Greece.</p>",
    "<p>Η <strong>περούκα Σαρλότ</strong> είναι μια απαλή, ρομαντική περούκα μεσαίου "
    "μήκους με εκλεπτυσμένες μπούκλες και παλιομοδίτικη γοητεία. Κομψή και ευέλικτη, "
    "ταιριάζει σε ηρωίδες του 19ου αιώνα και παραμυθένιες πριγκίπισσες.</p>"
    "<ul><li>Στυλ: Μεσαίο μήκος με απαλές μπούκλες</li>"
    "<li>Κατάλληλη για: ηρωίδες εποχής, χαρακτήρες παραμυθιών, θέατρο, αποκριές</li>"
    "<li>Υλικό: Υψηλής ποιότητας συνθετική ίνα</li><li>Κατασκευή στην Ελλάδα</li></ul>",
    "<p>Ρομαντική περούκα Σαρλότ με απαλές μπούκλες. Ιδανική για ηρωίδες εποχής και παραμυθένιους χαρακτήρες. Κατασκευή στην Αθήνα.</p>",
    name_en="Charlotte Romantic Curly Wig", name_el="Περούκα Σαρλότ Ρομαντική Σγουρή",
    slug_en="charlotte-romantic-curly-wig", slug_el="perouka-sarlot-romantiki-sgouri",
    meta_en="Charlotte Romantic Curly Wig | Period & Storybook Characters | Alegro Athens",
    meta_el="Περούκα Σαρλότ Ρομαντική | Χαρακτήρες Εποχής | Alegro"
)

# 163 — Charleston Black Bob
PRODUCTS[163] = d(
    "<p>The <strong>Charleston Black Bob Wig</strong> transports you straight to the "
    "roaring 1920s with its sleek, polished black bob and neat fringe — the definitive "
    "flapper-era hairstyle. Elegant, playful, and instantly recognisable at any "
    "Jazz Age, Art Deco, or vintage-themed event.</p>"
    "<ul><li>Color: Black</li><li>Style: Short vintage bob with fringe</li>"
    "<li>Ideal for: 1920s flapper, Art Deco, Jazz Age costumes, vintage parties, theatre</li>"
    "<li>Material: High-quality synthetic fiber</li><li>Made in Greece</li></ul>",
    "<p>Sleek black 1920s flapper bob wig with fringe. Perfect for Charleston, Art Deco, and Jazz Age costumes. Made in Athens, Greece.</p>",
    "<p>Η <strong>περούκα Τσάρλεστον σε μαύρο κοντό καρέ</strong> σε μεταφέρει αμέσως "
    "στη δεκαετία του 1920 με το λείο, γυαλισμένο μαύρο καρέ και την τακτοποιημένη "
    "αφέλεια — το χαρακτηριστικό χτένισμα της εποχής flapper.</p>"
    "<ul><li>Χρώμα: Μαύρο</li><li>Στυλ: Κοντό vintage καρέ με αφέλεια</li>"
    "<li>Κατάλληλη για: flapper δεκαετίας '20, Art Deco, Jazz Age, vintage πάρτι, θέατρο</li>"
    "<li>Υλικό: Υψηλής ποιότητας συνθετική ίνα</li><li>Κατασκευή στην Ελλάδα</li></ul>",
    "<p>Λείο μαύρο κοντό καρέ στυλ 1920s flapper. Ιδανικό για Τσάρλεστον, Art Deco και Jazz Age μεταμφιέσεις. Κατασκευή στην Αθήνα.</p>",
    name_en="Charleston Vintage Black Bob Wig with Fringe", name_el="Περούκα Τσάρλεστον Μαύρο Κοντό Καρέ με Αφέλεια",
    slug_en="charleston-vintage-black-bob-wig", slug_el="perouka-tsarleston-mavro-karo-afelia",
    meta_en="Charleston 1920s Black Bob Wig | Flapper & Art Deco | Alegro Athens",
    meta_el="Περούκα Τσάρλεστον Μαύρο Καρέ 1920s | Flapper & Art Deco | Alegro"
)

# 164–165 — Jack
def jack(color_en, color_el, slug_c_en, slug_c_el):
    return style_wig("Jack", color_en, color_el,
        f"a medium-length men's {color_en} wig with a casual, rugged wave — the classic adventurer's look",
        f"μια ανδρική περούκα μεσαίου μήκους σε {color_el} χρώμα με φυσικό κύμα — το κλασικό look του τυχοδιώκτη",
        f"jack-{slug_c_en}-wig", f"perouka-jack-{slug_c_el}",
        name_en_override=f"Jack {color_en.title()} Men's Wig",
        name_el_override=f"Περούκα Jack {color_el.title()} Ανδρική")

PRODUCTS[164] = jack("blonde","ξανθιά","blonde","xanthia")
PRODUCTS[165] = jack("brown","καστανή","brown","kastani")

# 166 — Dolores
PRODUCTS[166] = d(
    "<p>The <strong>Dolores Wig</strong> is a styled women's wig with a classic, "
    "composed silhouette evoking a formal, character-rich persona. Suited to a range "
    "of theatrical and carnival roles where authority and distinctiveness are key.</p>"
    "<ul><li>Style: Classic women's styled wig</li>"
    "<li>Ideal for: theatrical character roles, carnival, themed events</li>"
    "<li>Material: High-quality synthetic fiber</li><li>Made in Greece</li></ul>",
    "<p>Classic styled Dolores women's wig. Perfect for theatrical character roles and carnival. Made in Athens, Greece.</p>",
    "<p>Η <strong>περούκα Dolores</strong> είναι μια γυναικεία στυλιζαρισμένη περούκα "
    "με κλασική, επίσημη σιλουέτα. Κατάλληλη για θεατρικούς ρόλους "
    "και αποκριάτικες μεταμφιέσεις.</p>"
    "<ul><li>Στυλ: Κλασική γυναικεία στυλιζαρισμένη περούκα</li>"
    "<li>Κατάλληλη για: θεατρικοί χαρακτήρες, αποκριές, θεματικές εκδηλώσεις</li>"
    "<li>Υλικό: Υψηλής ποιότητας συνθετική ίνα</li><li>Κατασκευή στην Ελλάδα</li></ul>",
    "<p>Κλασική γυναικεία στυλιζαρισμένη περούκα Dolores. Ιδανική για θεατρικούς ρόλους και αποκριές. Κατασκευή στην Αθήνα.</p>",
    name_en="Dolores Classic Women's Wig", name_el="Περούκα Dolores Κλασική Γυναικεία",
    slug_en="dolores-classic-womens-wig", slug_el="perouka-dolores-klassiki-gynaikeia",
    meta_en="Dolores Classic Women's Wig | Theatre & Carnival | Alegro Athens",
    meta_el="Περούκα Dolores Κλασική Γυναικεία | Θέατρο & Αποκριές | Alegro"
)

# 167 — Male 1920s Short Black Wig
PRODUCTS[167] = d(
    "<p>The <strong>1920s Men's Short Black Wig</strong> channels the dapper, "
    "slicked-back style of the Roaring Twenties — the look of jazz musicians, "
    "gangsters, and sharp-suited gentlemen of the era. Sleek, confident, and "
    "unmistakably vintage.</p>"
    "<ul><li>Color: Black</li><li>Style: Short, slicked-back 1920s men's style</li>"
    "<li>Ideal for: 1920s gentleman, gangster, jazz era costumes, period theatre, carnival</li>"
    "<li>Material: High-quality synthetic fiber</li><li>Made in Greece</li></ul>",
    "<p>Sleek short black 1920s men's wig in slicked-back style. Perfect for gangster, jazz era, and period gentleman costumes. Made in Athens, Greece.</p>",
    "<p>Η <strong>ανδρική κοντή μαύρη περούκα δεκαετίας 1920</strong> αποτυπώνει το "
    "κομψό, χτενισμένο πίσω στυλ της εποχής — το look των τζαζ μουσικών, "
    "γκάνγκστερ και κομψών κυρίων της εποχής. Λείο, αυτοπεποίθησης και "
    "αναμφίβολα vintage.</p>"
    "<ul><li>Χρώμα: Μαύρο</li><li>Στυλ: Κοντό, χτενισμένο πίσω ανδρικό 1920s</li>"
    "<li>Κατάλληλη για: κύριος 1920s, γκάνγκστερ, τζαζ εποχή, ιστορικό θέατρο, αποκριές</li>"
    "<li>Υλικό: Υψηλής ποιότητας συνθετική ίνα</li><li>Κατασκευή στην Ελλάδα</li></ul>",
    "<p>Κοντή μαύρη ανδρική περούκα δεκαετίας 1920, χτενισμένη πίσω. Ιδανική για κοστούμια γκάνγκστερ, τζαζ εποχής και ιστορικού κυρίου. Κατασκευή στην Αθήνα.</p>",
    name_en="1920s Men's Short Black Slicked-Back Wig", name_el="Ανδρική Κοντή Μαύρη Περούκα 1920s",
    slug_en="1920s-mens-short-black-slicked-wig", slug_el="perouka-andrika-konti-mavri-1920s",
    meta_en="1920s Men's Short Black Slicked Wig | Gangster & Jazz Era | Alegro Athens",
    meta_el="Ανδρική Κοντή Μαύρη Περούκα 1920s | Γκάνγκστερ & Τζαζ | Alegro"
)

# 168–170 — Lolita series
def lolita(color_en, color_el, slug_c_en, slug_c_el):
    name_en = f"Lolita {color_en.title()} Wig"
    name_el = f"Περούκα Λολίτα {color_el.title()}"
    de = (
        f"<p>The <strong>Lolita {color_en.title()} Wig</strong> is a fun, youthful wig "
        f"with long twin pigtails in vibrant {color_en}. Playful and eye-catching, "
        f"it suits anime and manga characters, schoolgirl costumes, and anyone "
        f"looking for a bold, characterful look at a themed party.</p>"
        f"<ul><li>Color: {color_en.title()}</li>"
        f"<li>Style: Long twin pigtails</li>"
        f"<li>Ideal for: anime / manga characters, schoolgirl costumes, carnival, themed parties</li>"
        f"<li>Material: High-quality synthetic fiber</li><li>Made in Greece</li></ul>"
    )
    se = f"<p>Long twin pigtail {color_en} Lolita wig. Perfect for anime and manga characters, schoolgirl costumes, and carnival. Made in Athens, Greece.</p>"
    dl = (
        f"<p>Η <strong>περούκα Λολίτα σε {color_el} χρώμα</strong> είναι μια διασκεδαστική, "
        f"νεανική περούκα με μακριές διπλές κοτσίδες σε ζωντανό {color_el} χρώμα. "
        f"Παιχνιδιάρικη και εντυπωσιακή, ταιριάζει σε χαρακτήρες anime και manga.</p>"
        f"<ul><li>Χρώμα: {color_el.title()}</li>"
        f"<li>Στυλ: Μακριές διπλές κοτσίδες</li>"
        f"<li>Κατάλληλη για: χαρακτήρες anime/manga, κοστούμι μαθήτριας, αποκριές, θεματικά πάρτι</li>"
        f"<li>Υλικό: Υψηλής ποιότητας συνθετική ίνα</li><li>Κατασκευή στην Ελλάδα</li></ul>"
    )
    sl = f"<p>Μακριές διπλές κοτσίδες {color_el} χρώμα, Λολίτα. Ιδανική για anime / manga χαρακτήρες και αποκριές. Κατασκευή στην Αθήνα.</p>"
    return d(de, se, dl, sl,
             name_en=name_en, name_el=name_el,
             slug_en=f"lolita-{slug_c_en}-wig", slug_el=f"perouka-lolita-{slug_c_el}",
             meta_en=f"Lolita {color_en.title()} Pigtail Wig | Anime & Carnival | Alegro Athens",
             meta_el=f"Περούκα Λολίτα {color_el.title()} | Anime & Αποκριές | Alegro")

PRODUCTS[168] = lolita("black","μαύρη","black","mavri")
PRODUCTS[169] = lolita("blonde","ξανθιά","blonde","xanthia")
PRODUCTS[170] = lolita("fuchsia","φούξια","fuchsia","fouxia")

# 171 — Sandra
PRODUCTS[171] = d(
    "<p>The <strong>Sandra Wig</strong> is a lively, bouncy short wig with voluminous "
    "curls — full of energy and retro charm. Inspired by the cheerful, carefree spirit "
    "of classic musical-era heroines, it's a delightful choice for fun theatrical "
    "roles and vibrant carnival looks.</p>"
    "<ul><li>Style: Short voluminous curly wig</li>"
    "<li>Ideal for: retro musical characters, carnival, fun themed parties, theatre</li>"
    "<li>Material: High-quality synthetic fiber</li><li>Made in Greece</li></ul>",
    "<p>Bouncy short voluminous curly Sandra wig with retro charm. Perfect for retro musical characters and carnival. Made in Athens, Greece.</p>",
    "<p>Η <strong>περούκα Sandra</strong> είναι μια ζωηρή, αναπηδηστή κοντή περούκα "
    "με ογκώδεις μπούκλες — γεμάτη ενέργεια και ρετρό γοητεία. Εμπνευσμένη από τις "
    "χαρούμενες ηρωίδες κλασικών μιούζικαλ.</p>"
    "<ul><li>Στυλ: Κοντή ογκώδης σγουρή περούκα</li>"
    "<li>Κατάλληλη για: ρετρό μιούζικαλ χαρακτήρες, αποκριές, θεματικά πάρτι, θέατρο</li>"
    "<li>Υλικό: Υψηλής ποιότητας συνθετική ίνα</li><li>Κατασκευή στην Ελλάδα</li></ul>",
    "<p>Ζωηρή κοντή ογκώδης σγουρή περούκα Sandra με ρετρό γοητεία. Ιδανική για ρετρό μιούζικαλ χαρακτήρες και αποκριές. Κατασκευή στην Αθήνα.</p>",
    name_en="Sandra Curly Retro Wig", name_el="Περούκα Sandra Σγουρή Ρετρό",
    slug_en="sandra-curly-retro-wig", slug_el="perouka-sandra-sgouri-retro",
    meta_en="Sandra Curly Retro Wig | Musical & Carnival | Alegro Athens",
    meta_el="Περούκα Sandra Σγουρή Ρετρό | Θέατρο & Αποκριές | Alegro"
)

# 172–175 — Suzan series
def suzan(color_en, color_el, slug_c_en, slug_c_el):
    return style_wig("Suzan", color_en, color_el,
        f"a playful, wavy short-to-medium {color_en} wig with a lively, carefree look",
        f"μια παιχνιδιάρικη, κυματιστή περούκα κοντού έως μεσαίου μήκους σε {color_el} χρώμα",
        f"suzan-{slug_c_en}-wig", f"perouka-suzan-{slug_c_el}",
        name_en_override=f"Suzan {color_en.title()} Wig",
        name_el_override=f"Περούκα Suzan {color_el.title()}")

PRODUCTS[172] = suzan("black","μαύρη","black","mavri")
PRODUCTS[173] = suzan("blonde","ξανθιά","blonde","xanthia")
PRODUCTS[174] = suzan("pink","ροζ","pink","roz")
PRODUCTS[175] = suzan("light green","ανοιχτό πράσινο","light-green","anoixto-prasino")
