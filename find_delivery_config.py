"""
Find the shop-wide delivery time configuration page in PS9 admin.
Also check a few products' delivery_time_note_type values.
"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8')

ADMIN = 'https://alegro.gr/admin875fdclzkf27m3shsg9'

s = requests.Session()
s.headers['User-Agent'] = 'Mozilla/5.0'

r = s.get(ADMIN + '/login')
ft = re.search(r'name="_token"\s+value="([^"]+)"', r.text).group(1)
passwd = 'cultivatesandspreadslove13579' + chr(33)
r = s.post(ADMIN + '/login', data={'email':'damoncollective@gmail.com','passwd':passwd,
           'stay_logged_in':'0','_token':ft,'submitLogin':'1'}, allow_redirects=True)
m = re.search(r'[?&]token=([A-Za-z0-9._\-]+)', r.url)
legacy_tok = m.group(1) if m else ''
r2 = s.get(ADMIN + '/index.php', params={'controller':'AdminProducts','token':legacy_tok}, allow_redirects=True)
cat_token = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r2.url).group(1)
print('Logged in OK')

# Try the Order Settings page (where global delivery time is configured)
print('\n--- Trying Order Settings pages ---')
pages_to_try = [
    ('/index.php/configure/shop-parameters/order-preferences/', 'Order Preferences'),
    ('/index.php/configure/shop-parameters/product-preferences/', 'Product Preferences'),
]
for path, label in pages_to_try:
    r_p = s.get(ADMIN + path, params={'_token': cat_token}, allow_redirects=True)
    print(f'{label}: {r_p.status_code} ({len(r_p.text):,} bytes) → {r_p.url[-60:]}')
    if 'delivery' in r_p.text.lower():
        # Find delivery-related inputs
        for m2 in re.finditer(r'<input[^>]+>', r_p.text, re.I):
            tag = m2.group(0)
            nm = re.search(r'\bname="([^"]+)"', tag, re.I)
            vm = re.search(r'\bvalue="([^"]*)"', tag, re.I)
            if nm and 'delivery' in nm.group(1).lower():
                print(f'  INPUT: {nm.group(1)} = {repr((vm.group(1) if vm else "")[:60])}')
        # Also find textareas
        for m2 in re.finditer(r'<textarea[^>]*name="([^"]+)"[^>]*>(.*?)</textarea>', r_p.text, re.I|re.S):
            if 'delivery' in m2.group(1).lower():
                print(f'  TEXTAREA: {m2.group(1)} = {repr(m2.group(2)[:60])}')

# Check a sample of products' delivery_time_note_type
print('\n--- Sample product delivery_time_note_type values ---')
sample_pids = [265, 266, 267, 268, 269, 270, 386]
for pid in sample_pids:
    r_e = s.get(f'{ADMIN}/index.php/sell/catalog/products/{pid}/edit',
                params={'_token': cat_token}, allow_redirects=True)
    h = r_e.text
    note_type = re.search(r'name="product\[shipping\]\[delivery_time_note_type\]"[^>]*value="([^"]*)"', h, re.I)
    in_stock_1 = re.search(r'name="product\[shipping\]\[delivery_time_notes\]\[in_stock\]\[1\]"[^>]*value="([^"]*)"', h, re.I)
    in_stock_2 = re.search(r'name="product\[shipping\]\[delivery_time_notes\]\[in_stock\]\[2\]"[^>]*value="([^"]*)"', h, re.I)
    # also check radio buttons for note_type
    note_radios = re.findall(r'<input[^>]*name="product\[shipping\]\[delivery_time_note_type\]"[^>]*value="([^"]*)"[^>]*(?:checked[^>]*)?>', h, re.I)
    checked_radio = re.findall(r'<input[^>]*name="product\[shipping\]\[delivery_time_note_type\]"[^>]*value="([^"]*)"[^>]*checked', h, re.I)

    nt = note_type.group(1) if note_type else f'radios={note_radios} checked={checked_radio}'
    s1 = in_stock_1.group(1) if in_stock_1 else '?'
    s2 = in_stock_2.group(1) if in_stock_2 else '?'
    print(f'  PID {pid}: note_type={nt!r}  in_stock[1]={s1!r}  in_stock[2]={s2!r}')
