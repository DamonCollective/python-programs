"""
Final retry for 6 products where short description exceeds PS9's length limit.
Truncates short description to fit.
"""
import requests, re, sys, html as html_mod
sys.stdout.reconfigure(encoding='utf-8')

ADMIN   = 'https://alegro.gr/admin875fdclzkf27m3shsg9'
PASSWD  = 'cultivatesandspreadslove13579' + chr(33)
EMAIL   = 'damoncollective@gmail.com'
BACKUP  = r'C:\Users\Damon\Desktop\ALLA\sqlqueries\1753088504-255a1d97.sql'

FAILED_PIDS = [40, 47, 138, 163, 197, 250]

# ── Parse backup (same as before) ────────────────────────────────────────────
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

def truncate_short(html_text, max_chars=140):
    """Strip HTML tags, trim to max_chars, rewrap in <p>."""
    plain = re.sub(r'<[^>]+>', ' ', html_text or '')
    plain = re.sub(r'\s+', ' ', plain).strip()
    if len(plain) > max_chars:
        plain = plain[:max_chars].rsplit(' ', 1)[0] + '…'
    return f'<p>{plain}</p>' if plain else ''

print('Parsing backup…')
with open(BACKUP, encoding='utf-8', errors='replace') as f:
    content = f.read()
blocks = re.findall(r"INSERT INTO `l9n7b_product_lang` VALUES\s*\n(.*?);", content, re.S)

descs = {}
for block in blocks:
    for rs in _parse_rows(block):
        v = _parse_vals(rs)
        if len(v) < 10: continue
        pid, lang = v[0], v[2]
        if int(pid) not in FAILED_PIDS: continue
        desc  = v[3] or ''
        short = v[4] or ''
        name  = v[9] or ''
        descs.setdefault(pid, {})[lang] = {
            'desc': desc,
            'short': truncate_short(short),  # truncate here
            'name': name,
        }
        print(f'  PID {pid} lang {lang}: short = {repr(descs[pid][lang]["short"][:80])}')

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
print('\nLogged in.\n')

ok = fail = 0
for pid_int in FAILED_PIDS:
    pid = str(pid_int)
    lang_descs = descs.get(pid, {})

    r_edit = s.get(f'{ADMIN}/index.php/sell/catalog/products/{pid}/edit',
                   params={'_token': cat_tok}, allow_redirects=True, timeout=25)
    em = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r_edit.url)
    if not em:
        print(f'  PID {pid}: SKIP'); fail += 1; continue
    edit_tok = em.group(1)
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

    payload = {k: v for k, v in all_inputs.items() if k not in EXCLUDE}
    payload['product[details][features][feature_id]']     = '0'
    payload['product[options][visibility][visibility]']   = 'both'
    payload['product[options][visibility][online_only]']  = '0'
    payload['product[shipping][delivery_time_note_type]'] = '1'

    # HTML-decode all values
    for k in list(payload.keys()):
        payload[k] = html_mod.unescape(payload[k])

    for lang, data in lang_descs.items():
        payload[f'product[description][description][{lang}]']       = data['desc']
        payload[f'product[description][description_short][{lang}]'] = data['short']

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
        print(f'  PID {pid}: OK')
        ok += 1
    else:
        inv = re.findall(r'name="([^"]+)"[^>]*class="[^"]*is-invalid', r_save.text, re.I)
        errs = re.findall(r'<div[^>]*alert-danger[^>]*>(.*?)</div>', r_save.text, re.I | re.S)
        err_text = ' | '.join(re.sub(r'<[^>]+>', ' ', e).strip()[:100] for e in errs[:1])
        print(f'  PID {pid}: FAIL — inv={inv[:3]}  {err_text[:120]}')
        fail += 1

print(f'\nFinal retry: {ok} OK, {fail} still failing')
print(f'\nTotal restored: {135 + 13 + ok}/154')
