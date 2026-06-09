"""
create_cart_rule.py
Creates a 10 EUR discount coupon on alegro.gr PS9.

Settings:
  - Auto-generated code (uppercase letters + digits)
  - Discount: EUR 10 (tax incl.), wigs categories only
  - Min order: EUR 20 (tax incl., shipping excluded)
  - Valid: today -> 2026-10-31
  - 1 use per customer, unlimited total uses
"""

import re
import sys
import random
import string
import datetime
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
sys.stdout.reconfigure(encoding='utf-8')

ADMIN  = 'https://alegro.gr/admin875fdclzkf27m3shsg9'
EMAIL  = 'damoncollective@gmail.com'
PASSWD = 'cultivatesandspreadslove13579' + chr(33)

# All wigs categories (parent 18 + every subcategory)
# 18=Wigs, 10=Women's, 11=Men's, 12=Theatrical, 14=Halloween, 15=Natural, 16=Cosplay, 19=Party
WIGS_CAT_IDS = [18, 10, 11, 12, 14, 15, 16, 19]

def gen_code(n=10):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=n))

def login():
    s = requests.Session()
    s.verify = False
    s.headers['User-Agent'] = 'Mozilla/5.0'

    r = s.get(ADMIN + '/login')
    ft = re.search(r'name="_token"\s+value="([^"]+)"', r.text)
    if not ft:
        print('ERROR: could not find login _token'); sys.exit(1)

    r = s.post(ADMIN + '/login', data={
        'email': EMAIL,
        'passwd': PASSWD,
        'stay_logged_in': '0',
        '_token': ft.group(1),
        'submitLogin': '1',
    }, allow_redirects=True)

    if 'login' in r.url:
        print('ERROR: login failed'); sys.exit(1)

    # Extract the _token for addcart_rule from menu links
    add_tok = re.search(r'addcart_rule&(?:amp;)?_token=([A-Za-z0-9._\-]+)', r.text)
    if not add_tok:
        print('ERROR: could not find addcart_rule _token in page'); sys.exit(1)

    print('Logged in OK')
    return s, add_tok.group(1)

def create_cart_rule(s, add_token, coupon_code):
    today  = datetime.date.today().strftime('%Y-%m-%d') + ' 00:00:00'
    date_to = '2026-10-31 23:59:59'

    data = {
        'currentFormTab'          : 'informations',
        # --- Information ---
        'name_1'                  : '10 Euro Discount - Wigs',
        'name_2'                  : 'Ekptosi 10 Euro - Peroukes',
        'code'                    : coupon_code,
        'highlight'               : '1',
        'partial_use'             : '0',
        'priority'                : '1',
        'active'                  : '1',
        'id_customer'             : '0',
        'date_from'               : today,
        'date_to'                 : date_to,
        # --- Conditions ---
        'minimum_amount'          : '20',
        'minimum_amount_currency' : '1',  # EUR
        'minimum_amount_tax'      : '1',  # Tax included
        'minimum_amount_shipping' : '0',  # Shipping excluded
        'quantity'                : '0',  # 0 = unlimited total uses
        'quantity_per_user'       : '1',
        # restrictions: omit country/carrier/group/cart_rule (= unchecked = disabled)
        'product_restriction'     : '1',  # enable product restriction
        # --- Actions ---
        'free_shipping'           : '0',
        'apply_discount'          : 'amount',
        'reduction_amount'        : '10',
        'reduction_currency'      : '1',  # EUR
        'reduction_tax'           : '1',  # Tax included
        'apply_discount_to'       : 'order',
        'reduction_product'       : '0',
        'reduction_exclude_special': '0',
        'free_gift'               : '0',
        # --- Product restriction: wigs categories ---
        'product_rule_group[0][quantity]' : '1',
        'product_rule[0][0][type]'        : 'categories',
        # --- Submit ---
        'submitAddcart_rule'      : 'Save',
    }

    # Multiple category IDs for the restriction
    for cat_id in WIGS_CAT_IDS:
        data.setdefault('product_rule[0][0][values][]', [])
        if isinstance(data['product_rule[0][0][values][]'], list):
            data['product_rule[0][0][values][]'].append(str(cat_id))
        else:
            data['product_rule[0][0][values][]'] = [data['product_rule[0][0][values][]'], str(cat_id)]

    r = s.post(
        ADMIN + '/index.php',
        params={'controller': 'AdminCartRules', 'addcart_rule': '', '_token': add_token},
        data=data,
        allow_redirects=True,
    )

    print(f'Response status : {r.status_code}')
    print(f'Response URL    : {r.url}')

    # Parse success/error messages
    errors = re.findall(
        r'class="[^"]*alert-danger[^"]*"[^>]*>(.*?)</div>',
        r.text, re.S
    )
    successes = re.findall(
        r'class="[^"]*alert-success[^"]*"[^>]*>(.*?)</div>',
        r.text, re.S
    )

    for msg in errors:
        clean = re.sub(r'<[^>]+>', '', msg).strip()
        if clean:
            print('  ERROR:', clean[:300])

    for msg in successes:
        clean = re.sub(r'<[^>]+>', '', msg).strip()
        if clean:
            print('  SUCCESS:', clean[:300])

    if not errors and not successes:
        if 'addcart_rule' not in r.url:
            print('  Likely success — redirected away from create form.')
        else:
            print('  WARNING: still on create form. Check manually.')

    # Try to extract the new cart rule ID
    new_id = re.search(r'updatecart_rule.*?id_cart_rule[=_](\d+)', r.url)
    if new_id:
        print(f'  New cart rule ID: {new_id.group(1)}')

    return r

def main():
    coupon_code = gen_code()
    print('=' * 50)
    print(f'Coupon code  : {coupon_code}')
    print(f'Value        : EUR 10 (tax incl.)')
    print(f'Min order    : EUR 20')
    print(f'Valid until  : 2026-10-31')
    print(f'Per customer : 1 use')
    print(f'Categories   : Wigs + subcategories (IDs {WIGS_CAT_IDS})')
    print('=' * 50)

    s, add_token = login()
    create_cart_rule(s, add_token, coupon_code)

    # Save to Desktop
    out = r'C:\Users\Damon\Desktop\new_coupon.txt'
    with open(out, 'w', encoding='utf-8') as f:
        f.write(f'Coupon Code  : {coupon_code}\n')
        f.write(f'Value        : EUR 10 (tax incl.)\n')
        f.write(f'Min order    : EUR 20\n')
        f.write(f'Valid until  : 2026-10-31\n')
        f.write(f'Per customer : 1 use\n')
        f.write(f'Applies to   : Wigs + subcategories\n')
    print(f'\nSaved to {out}')
    print(f'\nCOUPON CODE: {coupon_code}')

if __name__ == '__main__':
    main()
