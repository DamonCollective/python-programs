"""
Retry the 19 failed products from restore_descriptions_admin.py.
Fixes:
  1. HTML-decode name fields (&#039; -> ', &amp; -> &)
  2. Provide fallback short description if backup has empty/None
"""
import requests, re, sys, html as html_mod
from threading import Lock
sys.stdout.reconfigure(encoding='utf-8')

ADMIN   = 'https://alegro.gr/admin875fdclzkf27m3shsg9'
PASSWD  = 'cultivatesandspreadslove13579' + chr(33)
EMAIL   = 'damoncollective@gmail.com'
BACKUP  = r'C:\Users\Damon\Desktop\ALLA\sqlqueries\1753088504-255a1d97.sql'

FAILED_PIDS = [40, 47, 138, 150, 163, 167, 181, 182, 193, 194, 195, 196, 197, 198, 199, 225, 231, 238, 250]

# ── Parse backup ─────────────────────────────────────────────────────────────
def _parse_rows(block):
    rows, i = [], 0
    while i < len(block):
        if block[i] == '(':
            j, depth, in_str, esc = i+1, 1, False, False
            while j < len(block) and depth > 0:
                c = block[j]
                if esc: esc = False
                elif c == '\\': esc = True
                elif c == "'" and not esc: in_str = not in_str
                elif not in_str:
                    if c == '(': depth += 1
                    elif c == ')': depth -= 1
                j += 1
            rows.append(block[i:j]); i = j
        else: i += 1
    return rows

def _parse_vals(row_str):
    inner = row_str.strip().strip('()')
    vals, i = [], 0
    while i < len(inner):
        while i < len(inner) and inner[i] in ' \t\n': i += 1
        if i >= len(inner): break
        if inner[i:i+4] == 'NULL':
            vals.append(None); i += 4
        elif inner[i] == "'":
            i += 1; s = []
            while i < len(inner):
                c = inner[i]
                if c == '\\' and i+1 < len(inner):
                    nc = inner[i+1]
                    s.append({'n':'\n','r':'\r','t':'\t','\\':'\\', "'":"'", '"':'"'}.get(nc, nc))
                    i += 2
                elif c == "'":
                    i += 1; break
                else:
                    s.append(c); i += 1
            vals.append(''.join(s))
        else:
            j = i
            while j < len(inner) and inner[j] != ',': j += 1
            vals.append(inner[i:j].strip()); i = j
        while i < len(inner) and inner[i] in ' \t\n,':
            if inner[i] == ',': i += 1; break
            i += 1
    return vals

print('Parsing backup…')
with open(BACKUP, encoding='utf-8', errors='replace') as f:
    content = f.read()
blocks = re.findall(r"INSERT INTO `l9n7b_product_lang` VALUES\s*\n(.*?);", content, re.S)

descs = {}
names_backup = {}
for block in blocks:
    for rs in _parse_rows(block):
        v = _parse_vals(rs)
        if len(v) < 10: continue
        pid, lang = v[0], v[2]
        if int(pid) not in FAILED_PIDS: continue
        desc  = v[3] or ''
        short = v[4] or ''
        name  = v[9] or ''
        descs.setdefault(pid, {})[lang] = {'desc': desc, 'short': short, 'name': name}

print(f'Loaded data for {len(descs)} products.')
for pid in sorted(descs.keys(), key=int):
    for lang, d in descs[pid].items():
        short_preview = d['short'][:60] if d['short'] else '(empty)'
        print(f'  PID {pid} lang {lang}: name={d["name"][:40]!r}  short={short_preview!r}')

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
r2 = s.get(ADMIN + '/index.php',
           params={'controller': 'AdminProducts', 'token': legacy},
           allow_redirects=True)
cat_tok = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r2.url).group(1)
print('\nLogged in.\n')

ok = fail = 0
for pid_int in FAILED_PIDS:
    pid = str(pid_int)
    lang_descs = descs.get(pid, {})

    r_edit = s.get(f'{ADMIN}/index.php/sell/catalog/products/{pid}/edit',
                   params={'_token': cat_tok}, allow_redirects=True, timeout=25)
    em = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r_edit.url)
    if not em:
        print(f'  PID {pid}: SKIP — no edit token'); fail += 1; continue
    edit_tok = em.group(1)
    html = r_edit.text

    # Collect inputs
    all_inputs = {}
    for im in re.finditer(r'<input[^>]+>', html, re.I):
        tag = im.group(0)
        nm = re.search(r'\bname="([^"]+)"', tag, re.I)
        vm = re.search(r'\bvalue="([^"]*)"', tag, re.I)
        if nm:
            all_inputs[nm.group(1)] = vm.group(1) if vm else ''

    # Collect selects
    for sm in re.finditer(r'<select([^>]*)>(.*?)</select>', html, re.I | re.S):
        attrs, body = sm.group(1), sm.group(2)
        nm = re.search(r'\bname="([^"]+)"', attrs, re.I)
        if not nm or 'paginator' in nm.group(1): continue
        sel = (re.search(r'<option[^>]+selected[^>]*value="([^"]*)"', body, re.I) or
               re.search(r'<option[^>]*value="([^"]*)"', body, re.I))
        all_inputs[nm.group(1)] = sel.group(1) if sel else ''

    payload = {k: v for k, v in all_inputs.items() if k not in EXCLUDE}
    payload['product[details][features][feature_id]']     = '0'
    payload['product[options][visibility][visibility]']   = 'both'
    payload['product[options][visibility][online_only]']  = '0'
    payload['product[shipping][delivery_time_note_type]'] = '1'

    # FIX 1: HTML-decode ALL field values (fixes &#039; -> ', &amp; -> &)
    for k in list(payload.keys()):
        payload[k] = html_mod.unescape(payload[k])

    # FIX 2: Set descriptions, providing fallback short desc if empty
    for lang, data in lang_descs.items():
        desc  = data['desc']
        short = data['short']
        name  = data['name']

        # If short description is empty, use a trimmed version of the full desc
        # or just the product name as a minimal fallback
        if not short or not short.strip():
            if desc and len(desc.strip()) > 10:
                # strip HTML tags and take first 200 chars as short desc
                plain = re.sub(r'<[^>]+>', '', desc).strip()
                short = f'<p>{plain[:200]}</p>' if plain else f'<p>{name}</p>'
            else:
                short = f'<p>{name}</p>'

        payload[f'product[description][description][{lang}]']       = desc
        payload[f'product[description][description_short][{lang}]'] = short

    payload['_token'] = edit_tok

    r_save = s.post(
        f'{ADMIN}/index.php/sell/catalog/products/{pid}/edit',
        params={'_token': edit_tok},
        data=payload,
        headers={'Referer': r_edit.url},
        allow_redirects=True,
        timeout=25,
    )
    fv = re.search(r'data-form-valid="(\d+)"', r_save.text)
    valid = fv.group(1) if fv else '?'
    if valid == '1':
        print(f'  PID {pid}: OK')
        ok += 1
    else:
        inv = re.findall(r'name="([^"]+)"[^>]*class="[^"]*is-invalid', r_save.text, re.I)
        errs = re.findall(r'<div[^>]*alert-danger[^>]*>(.*?)</div>', r_save.text, re.I | re.S)
        err_text = ' | '.join(re.sub(r'<[^>]+>', ' ', e).strip()[:80] for e in errs[:1])
        print(f'  PID {pid}: FAIL — inv={inv[:3]}  {err_text[:100]}')
        fail += 1

print(f'\nRetry done: {ok} OK, {fail} still failing')
