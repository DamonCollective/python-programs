"""
Update product 386 (Kapodistrias wig) with bilingual descriptions + SEO.
Key fix: submit feature_id='0' but exclude feature_value_id and custom_value
         (those extra empty fields trigger a validation error).
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
    "είναι περούκα επαγγελματικής ποιότητας που αναπαράγει με πιστότητα "
    "το εμβληματικό look του πρώτου Κυβερνήτη της Ελλάδας, "
    "όπως εμφανίζεται στην επική ταινία «<em>Καποδίστριας</em>» 2026 "
    "του σκηνοθέτη Ιωάννη Σμαράγδη. "
    "Πλούσιες ασημόγκριζες μπούκλες σε αριστοκρατικό ύφος 18ου–19ου αιώνα.</p>"
    "<p>Κατασκευή στην Ελλάδα από την "
    "<strong>Alegro</strong>, με πάνω από 45 χρόνια εμπειρίας. Ένα μέγεθος για όλους.</p>"
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

# ── Login ──────────────────────────────────────────────────────────────────────
s = requests.Session()
s.headers['User-Agent'] = 'Mozilla/5.0'

r = s.get(ADMIN + '/login')
ft = re.search(r'name="_token"\s+value="([^"]+)"', r.text).group(1)
passwd = 'cultivatesandspreadslove13579' + chr(33)
r = s.post(ADMIN + '/login',
           data={'email':'damoncollective@gmail.com','passwd':passwd,
                 'stay_logged_in':'0','_token':ft,'submitLogin':'1'},
           allow_redirects=True)
m = re.search(r'[?&]token=([A-Za-z0-9._\-]+)', r.url)
legacy_tok = m.group(1) if m else ''
r2 = s.get(ADMIN + '/index.php',
           params={'controller':'AdminProducts','token':legacy_tok},
           allow_redirects=True)
cat_token = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r2.url).group(1)
print('Logged in OK')

# ── Fetch edit page ────────────────────────────────────────────────────────────
r_edit = s.get(f'{ADMIN}/index.php/sell/catalog/products/{PID}/edit',
               params={'_token': cat_token}, allow_redirects=True)
edit_tok = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r_edit.url).group(1)
html = r_edit.text
form_tok = re.search(r'name="product\[_token\]"[^>]*value="([^"]+)"', html).group(1)
print(f'Edit page: {len(html):,} bytes')

# Detect language IDs by looking at other products' field structure
# Lang 1 = EN, Lang 2 = EL (confirmed from product 265 diagnostic)
EN, EL = 1, 2

# Show current state
cur_name_1 = re.search(r'name="product\[header\]\[name\]\[1\]"[^>]*value="([^"]*)"', html)
cur_name_2 = re.search(r'name="product\[header\]\[name\]\[2\]"[^>]*value="([^"]*)"', html)
print(f'Current name[1]: {cur_name_1.group(1)[:60] if cur_name_1 else "not found"}')
print(f'Current name[2]: {cur_name_2.group(1)[:60] if cur_name_2 else "not found"}')

# ── Build payload ──────────────────────────────────────────────────────────────
# Start with all page inputs
all_inputs = {}
for m in re.finditer(r'<input[^>]+>', html, re.I):
    tag = m.group(0)
    nm = re.search(r'\bname="([^"]+)"', tag, re.I)
    vm = re.search(r'\bvalue="([^"]*)"', tag, re.I)
    if nm:
        all_inputs[nm.group(1)] = vm.group(1) if vm else ''

# Also collect select elements (use selected option, or first option as default)
for sel_m in re.finditer(r'<select([^>]*)>(.*?)</select>', html, re.I | re.S):
    attrs, body = sel_m.group(1), sel_m.group(2)
    nm = re.search(r'\bname="([^"]+)"', attrs, re.I)
    if not nm:
        continue
    name = nm.group(1)
    if 'paginator' in name:   # skip pagination selects
        continue
    selected = re.search(r'<option[^>]+selected[^>]*value="([^"]*)"', body, re.I)
    if not selected:
        selected = re.search(r'<option[^>]*value="([^"]*)"', body, re.I)
    all_inputs[name] = selected.group(1) if selected else ''

# KEY FIX: exclude fields that cause validation errors
EXCLUDE = {
    'product[details][features][feature_value_id]',
    'product[details][features][custom_value][1]',
    'product[details][features][custom_value][2]',
    # Priority management — selects all default to 'id_shop' (Vue-driven) → duplicate error
    # Exclude entire priority_management block so server uses shop defaults
    'product[pricing][priority_management][use_custom_priority]',
    'product[pricing][priority_management][priorities][0]',
    'product[pricing][priority_management][priorities][1]',
    'product[pricing][priority_management][priorities][2]',
    'product[pricing][priority_management][priorities][3]',
}
payload = {k: v for k, v in all_inputs.items() if k not in EXCLUDE}
# Ensure feature_id='0' (select default)
payload['product[details][features][feature_id]'] = '0'

# Set the content
payload[f'product[header][name][{EN}]'] = NAME_EN
payload[f'product[header][name][{EL}]'] = NAME_EL
payload[f'product[description][description][{EN}]']       = DESC_EN
payload[f'product[description][description][{EL}]']       = DESC_EL
payload[f'product[description][description_short][{EN}]'] = SHORT_EN
payload[f'product[description][description_short][{EL}]'] = SHORT_EL
payload[f'product[seo][meta_title][{EN}]']       = META_TITLE_EN
payload[f'product[seo][meta_title][{EL}]']       = META_TITLE_EL
payload[f'product[seo][meta_description][{EN}]'] = META_DESC_EN
payload[f'product[seo][meta_description][{EL}]'] = META_DESC_EL
payload[f'product[seo][link_rewrite][{EN}]']     = LINK_EN
payload[f'product[seo][link_rewrite][{EL}]']     = LINK_EL
payload[f'product[seo][tags][{EN}]']             = TAGS_EN
payload[f'product[seo][tags][{EL}]']             = TAGS_EL

# CSRF
payload['_token'] = edit_tok

print(f'Payload: {len(payload)} fields')
print(f'  feature_id = {payload.get("product[details][features][feature_id]", "ABSENT")}')
print(f'  feature_value_id in payload: {"product[details][features][feature_value_id]" in payload}')

# ── Submit ─────────────────────────────────────────────────────────────────────
r_save = s.post(
    f'{ADMIN}/index.php/sell/catalog/products/{PID}/edit',
    params={'_token': edit_tok},
    data=payload,
    headers={'Referer': r_edit.url},
    allow_redirects=True,
)
print(f'\nSave: {r_save.status_code} → {r_save.url[-70:]}')

fv = re.search(r'data-form-valid="(\d+)"', r_save.text)
fs = re.search(r'data-form-submitted="(\d+)"', r_save.text)
print(f'form-valid={fv.group(1) if fv else "?"}  form-submitted={fs.group(1) if fs else "?"}')

errors = re.findall(r'<div[^>]*alert-danger[^>]*>(.*?)</div>', r_save.text, re.I | re.S)
for e in errors:
    t = re.sub(r'<[^>]+>', ' ', e).strip()
    t = re.sub(r'\s+', ' ', t)
    if t: print(f'ERROR: {t[:250]}')

inv = re.findall(r'name="([^"]+)"[^>]*class="[^"]*is-invalid', r_save.text, re.I)
if inv: print(f'Invalid fields: {inv[:5]}')

# ── Verify ─────────────────────────────────────────────────────────────────────
print('\n--- Verification ---')
r_v = s.get(f'{ADMIN}/index.php/sell/catalog/products/{PID}/edit',
            params={'_token': cat_token}, allow_redirects=True)

def get_val(html, field):
    m = re.search(f'name="{re.escape(field)}"[^>]*value="([^"]*)"', html, re.I)
    return m.group(1) if m else '(not found)'

print(f'name[1]: {get_val(r_v.text, "product[header][name][1]")[:70]}')
print(f'name[2]: {get_val(r_v.text, "product[header][name][2]")[:70]}')
print(f'slug[1]: {get_val(r_v.text, "product[seo][link_rewrite][1]")[:70]}')
print(f'slug[2]: {get_val(r_v.text, "product[seo][link_rewrite][2]")[:70]}')

en_ok = NAME_EN[:20] in get_val(r_v.text, f'product[header][name][{EN}]')
el_ok = NAME_EL[:15] in get_val(r_v.text, f'product[header][name][{EL}]')
print(f'\nEN name saved: {en_ok}')
print(f'EL name saved: {el_ok}')

if en_ok and el_ok:
    print('\nSUCCESS: Product 386 updated with bilingual descriptions and SEO.')
else:
    print('\nSomething went wrong — check the output above.')
