"""
Update product 386 (Kapodistrias wig) with bilingual descriptions and SEO.
Uses _method=PATCH with only the changed fields (mimics PS9 Vue.js behaviour).
"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8')

ADMIN = 'https://alegro.gr/admin875fdclzkf27m3shsg9'
PID   = 386

# ── Content ────────────────────────────────────────────────────────────────────
NAME_EN = "Ioannis Kapodistrias Theatrical Wig | Reenactment Stage Wig | Made in Greece"
NAME_EL = "Περούκα Ιωάννης Καποδίστριας | Θεατρική Ιστορική Περούκα | Κατασκευή Ελλάδα"

SHORT_EN = (
    "Theatrical stage wig inspired by the 2026 film Kapodistrias by Ioannis Smaragdis. "
    "Voluminous silver-grey curls. Handcrafted in Greece by Alegro."
)
SHORT_EL = (
    "Θεατρική περούκα εμπνευσμένη από την ταινία Καποδίστριας 2026 του Ι. Σμαράγδη. "
    "Πλούσιες ασημόγκριζες μπούκλες. Κατασκευή στην Ελλάδα από την Alegro."
)

DESC_EN = (
    "<p>The <strong>Ioannis Kapodistrias Theatrical Wig</strong> is a stage-quality wig that "
    "faithfully recreates the iconic look of Greece's first Governor, as seen in the 2026 epic "
    "film <em>Kapodistrias</em> directed by Ioannis Smaragdis. Featuring voluminous silver-grey "
    "curls in authentic 18th\u201319th century aristocratic style, this wig is the ideal choice for "
    "theatre productions, historical reenactments, carnival costumes, and period film or TV "
    "productions.</p>"
    "<p>Handcrafted in Greece by <strong>Alegro</strong>, with over 45 years of professional "
    "wig-making expertise. One size fits most adults.</p>"
    "<ul>"
    "<li>Color: Silver-grey with dark undertones</li>"
    "<li>Style: Voluminous curls, mid-length</li>"
    "<li>Inspired by the film Kapodistrias (2026) \u2013 Ioannis Smaragdis</li>"
    "<li>Ideal for: theatre, reenactment, carnival, film/TV</li>"
    "<li>Made in Greece</li>"
    "</ul>"
)

DESC_EL = (
    "<p>H <strong>θεατρική περούκα Ιωάννης Καποδίστριας</strong> "
    "είναι μια περούκα επαγγελματικής "
    "ποιότητας που αναπαράγει με πιστότητα "
    "το εμβληματικό look του πρώτου Κυβερνήτη "
    "της Ελλάδας, όπως εμφανίζεται στην επική "
    "ταινία «<em>Καποδίστριας</em>» 2026 "
    "του σκηνοθέτη Ιωάννη Σμαράγδη. "
    "Πλούσιες ασημόγκριζες μπούκλες "
    "σε αριστοκρατικό ύφος 18ου–19ου αιώνα.</p>"
    "<p>Κατασκευή στην Ελλάδα από την "
    "<strong>Alegro</strong>, με πάνω από 45 χρόνια "
    "εμπειρίας. Ένα μέγεθος για όλους.</p>"
    "<ul>"
    "<li>Χρώμα: Ασημόγκριζο με σκούρες ρίζες</li>"
    "<li>Στυλ: Πλούσιες μπούκλες, μεσαίο μήκος</li>"
    "<li>Εμπνευσμένη από την ταινία Καποδίστριας (2026)</li>"
    "<li>Ιδανική για: θέατρο, reenactment, αποκριές, κινηματογράφο/TV</li>"
    "<li>Κατασκευή στην Ελλάδα</li>"
    "</ul>"
)

META_TITLE_EN = "Ioannis Kapodistrias Theatrical Wig | Made in Greece | Alegro"
META_TITLE_EL = "Περούκα Καποδίστριας | Θεατρική Ιστορική | Alegro"
META_DESC_EN  = ("Buy the Ioannis Kapodistrias theatrical wig as seen in the 2026 film by "
                 "Ioannis Smaragdis. Silver-grey curls, made in Greece by Alegro.")
META_DESC_EL  = ("Αγοράστε την περούκα Καποδίστριας από την ταινία 2026. "
                 "Ασημόγκριζες μπούκλες, κατασκευή στην Ελλάδα από την Alegro.")
LINK_EN = "ioannis-kapodistrias-theatrical-wig-reenactment-stage-wig"
LINK_EL = "perouka-ioannis-kapodistrias-theatriki-istoriki-perouka"
TAGS_EN = "kapodistrias,theatrical wig,stage wig,historical wig,greek history,reenactment,made in greece"
TAGS_EL = "καποδίστριας,θεατρική περούκα,ιστορική περούκα,ελληνική ιστορία,αποκριές"

# Language IDs (PS9: 1=EN, 2=EL - adjust if different)
EN, EL = 1, 2

# ── Login ──────────────────────────────────────────────────────────────────────
s = requests.Session()
s.headers['User-Agent'] = 'Mozilla/5.0'

r = s.get(ADMIN + '/login')
ft = re.search(r'name="_token"\s+value="([^"]+)"', r.text).group(1)
passwd = 'cultivatesandspreadslove13579' + chr(33)
r = s.post(ADMIN + '/login', data={'email':'damoncollective@gmail.com','passwd':passwd,'stay_logged_in':'0','_token':ft,'submitLogin':'1'}, allow_redirects=True)
m = re.search(r'[?&]token=([A-Za-z0-9._\-]+)', r.url)
legacy_tok = m.group(1) if m else ''
r2 = s.get(ADMIN + '/index.php', params={'controller':'AdminProducts','token':legacy_tok}, allow_redirects=True)
cat_token = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r2.url).group(1)
print('Logged in OK')

# ── Fetch edit page ────────────────────────────────────────────────────────────
r_edit = s.get(f'{ADMIN}/index.php/sell/catalog/products/{PID}/edit',
               params={'_token': cat_token}, allow_redirects=True)
edit_tok = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r_edit.url).group(1)
html = r_edit.text
print(f'Edit page: {len(html):,} bytes')

form_tok_m = re.search(r'name="product\[_token\]"[^>]*value="([^"]+)"', html, re.I)
form_tok = form_tok_m.group(1) if form_tok_m else edit_tok

# Detect language IDs from actual page
en_m = re.search(r'name="product\[header\]\[name\]\[(\d+)\]"[^>]*value="[^"]*(?:wig|peruke|kapod)[^"]*"', html, re.I)
el_m = re.search(r'name="product\[header\]\[name\]\[(\d+)\]"[^>]*value="[^"]*(?:\u03c0\u03b5\u03c1\u03bf\u03cd\u03ba|\u03ba\u03b1\u03c0\u03bf\u03b4)[^"]*"', html, re.I)
if en_m:
    EN = int(en_m.group(1))
    print(f'EN lang id detected: {EN}')
if el_m:
    EL = int(el_m.group(1))
    print(f'EL lang id detected: {EL}')

# Show current names
name_en_cur = re.search(f'name="product\\[header\\]\\[name\\]\\[{EN}\\]"[^>]*value="([^"]*)"', html, re.I)
name_el_cur = re.search(f'name="product\\[header\\]\\[name\\]\\[{EL}\\]"[^>]*value="([^"]*)"', html, re.I)
print(f'Current EN name: {name_en_cur.group(1)[:80] if name_en_cur else "not found"}')
print(f'Current EL name: {name_el_cur.group(1)[:80] if name_el_cur else "not found"}')

# ── Build PATCH payload (only changed fields + product[_token] + _method) ──────
payload = {
    '_method': 'PATCH',
    'product[_token]': form_tok,

    # Names
    f'product[header][name][{EN}]': NAME_EN,
    f'product[header][name][{EL}]': NAME_EL,

    # Descriptions
    f'product[description][description][{EN}]':       DESC_EN,
    f'product[description][description][{EL}]':       DESC_EL,
    f'product[description][description_short][{EN}]': SHORT_EN,
    f'product[description][description_short][{EL}]': SHORT_EL,

    # SEO
    f'product[seo][meta_title][{EN}]':       META_TITLE_EN,
    f'product[seo][meta_title][{EL}]':       META_TITLE_EL,
    f'product[seo][meta_description][{EN}]': META_DESC_EN,
    f'product[seo][meta_description][{EL}]': META_DESC_EL,
    f'product[seo][link_rewrite][{EN}]':     LINK_EN,
    f'product[seo][link_rewrite][{EL}]':     LINK_EL,
    f'product[seo][tags][{EN}]':             TAGS_EN,
    f'product[seo][tags][{EL}]':             TAGS_EL,
}

print(f'\nSending {len(payload)} fields with _method=PATCH')

# ── Submit ─────────────────────────────────────────────────────────────────────
r_save = s.post(
    f'{ADMIN}/index.php/sell/catalog/products/{PID}/edit',
    params={'_token': edit_tok},
    data=payload,
    headers={'Referer': r_edit.url},
    allow_redirects=True,
)
print(f'Save: {r_save.status_code} → {r_save.url[-80:]}')
print(f'Response size: {len(r_save.text):,}')

# Check form validity
form_valid = re.search(r'data-form-valid="(\d+)"', r_save.text)
form_subm  = re.search(r'data-form-submitted="(\d+)"', r_save.text)
print(f'form-valid={form_valid.group(1) if form_valid else "?"}  '
      f'form-submitted={form_subm.group(1) if form_subm else "?"}')

# Check for errors
errors = re.findall(r'<div[^>]*alert-danger[^>]*>(.*?)</div>', r_save.text, re.I | re.S)
for e in errors:
    text = re.sub(r'<[^>]+>', ' ', e).strip()
    text = re.sub(r'\s+', ' ', text)
    if text:
        print(f'ERROR: {text[:300]}')

# ── Verify ─────────────────────────────────────────────────────────────────────
print('\n--- Verification (fresh fetch) ---')
r_v = s.get(f'{ADMIN}/index.php/sell/catalog/products/{PID}/edit',
            params={'_token': cat_token}, allow_redirects=True)

name_en_v = re.search(f'name="product\\[header\\]\\[name\\]\\[{EN}\\]"[^>]*value="([^"]*)"', r_v.text, re.I)
name_el_v = re.search(f'name="product\\[header\\]\\[name\\]\\[{EL}\\]"[^>]*value="([^"]*)"', r_v.text, re.I)
link_en_v = re.search(f'name="product\\[seo\\]\\[link_rewrite\\]\\[{EN}\\]"[^>]*value="([^"]*)"', r_v.text, re.I)

print(f'EN name:  {name_en_v.group(1)[:80] if name_en_v else "not found"}')
print(f'EL name:  {name_el_v.group(1)[:80] if name_el_v else "not found"}')
print(f'EN slug:  {link_en_v.group(1)[:80] if link_en_v else "not found"}')

# Check if names updated
en_ok = name_en_v and NAME_EN[:30] in name_en_v.group(1)
el_ok = name_el_v and NAME_EL[:20] in name_el_v.group(1)
print(f'\nEN updated: {en_ok}')
print(f'EL updated: {el_ok}')

if en_ok and el_ok:
    print('\nSUCCESS: Descriptions and SEO saved to product 386.')
else:
    print('\nSave may have failed - checking form errors...')
    invalid = re.findall(r'name="([^"]+)"[^>]*class="[^"]*is-invalid', r_save.text, re.I)
    if invalid:
        print(f'Invalid fields: {invalid[:5]}')
