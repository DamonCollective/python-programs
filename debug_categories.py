import requests, re, sys, urllib3
urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

ADMIN = 'https://alegro.gr/admin875fdclzkf27m3shsg9'
s = requests.Session()
s.verify = False
s.headers['User-Agent'] = 'Mozilla/5.0'

r = s.get(ADMIN + '/login')
ft = re.search(r'name="_token"\s+value="([^"]+)"', r.text).group(1)
passwd = 'cultivatesandspreadslove13579' + chr(33)
r = s.post(ADMIN + '/login', data={
    'email': 'damoncollective@gmail.com',
    'passwd': passwd,
    'stay_logged_in': '0',
    '_token': ft,
    'submitLogin': '1',
}, allow_redirects=True)
add_tok = re.search(r'addcart_rule&(?:amp;)?_token=([A-Za-z0-9._\-]+)', r.text).group(1)

r2 = s.get(ADMIN + '/index.php', params={
    'controller': 'AdminCartRules',
    'addcart_rule': '',
    '_token': add_tok,
}, allow_redirects=True)
html = r2.text

# Extract select options for currency, tax, shipping
for sel_name in ['minimum_amount_currency', 'minimum_amount_tax', 'minimum_amount_shipping',
                  'reduction_currency', 'reduction_tax']:
    block = re.search(r'name="' + sel_name + r'"[^>]*>(.*?)</select>', html, re.S)
    if block:
        opts = re.findall(r'<option[^>]*value="([^"]*)"[^>]*>(.*?)</option>', block.group(1))
        print(f'\n{sel_name}:')
        for v, txt in opts:
            print(f'  value={v!r}  text={txt.strip()!r}')
