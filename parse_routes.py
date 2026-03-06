"""Parse the JS routing table and analyze the product save mechanism."""
import requests, re, sys, json
sys.stdout.reconfigure(encoding='utf-8')

ADMIN = 'https://alegro.gr/admin875fdclzkf27m3shsg9'
PID = 265

s = requests.Session()
s.headers['User-Agent'] = 'Mozilla/5.0'

# Login
r = s.get(ADMIN + '/login')
ft = re.search(r'name="_token"\s+value="([^"]+)"', r.text).group(1)
passwd = 'cultivatesandspreadslove13579' + chr(33)
r = s.post(ADMIN + '/login', data={'email':'damoncollective@gmail.com','passwd':passwd,'stay_logged_in':'0','_token':ft,'submitLogin':'1'}, allow_redirects=True)
m = re.search(r'[?&]token=([A-Za-z0-9._\-]+)', r.url)
legacy_tok = m.group(1) if m else ''
r2 = s.get(ADMIN + '/index.php', params={'controller':'AdminProducts','token':legacy_tok}, allow_redirects=True)
cat_token = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r2.url).group(1)

# Read the small create_product bundle (50KB) which has the routing table
bundle_url = f'https://alegro.gr/admin875fdclzkf27m3shsg9/themes/new-theme/public/create_product.bundle.js?9.0.0'
r_bundle = s.get(bundle_url)
bundle = r_bundle.text

# Extract the routing JSON object
# It's in format: Routing.setRoutingData({...})
route_m = re.search(r'Routing\.setRoutingData\((\{.*?\})\)', bundle, re.S)
if not route_m:
    route_m = re.search(r'"routes":\s*(\{[^}]{1,50000}\})', bundle, re.S)

if route_m:
    try:
        routes_raw = route_m.group(1)
        # Extract all route names and their tokens/paths
        route_entries = re.findall(r'"(admin_\w+)":\{"tokens":\[(.*?)\]', routes_raw, re.S)
        print(f'Found {len(route_entries)} routes')
        print('\n--- Product-related routes ---')
        for name, tokens in route_entries:
            if 'product' in name.lower() or 'catalog' in name.lower():
                # Parse path from tokens
                path_parts = re.findall(r'\["text","([^"]+)"\]', tokens)
                path = ''.join(reversed(path_parts))
                # Also get variable tokens
                var_parts = re.findall(r'\["variable",[^,]+,"[^"]+","([^"]+)"\]', tokens)
                print(f'  {name}: {path} vars={var_parts}')
    except Exception as e:
        print(f'Parse error: {e}')
        print(route_m.group(1)[:500])
else:
    print('No routing data found')
    # Try to find it differently
    all_routes_m = re.search(r'(\{(?:["\']admin_[^"\']+["\'][^\n]{0,500}){5,})', bundle, re.S)
    if all_routes_m:
        print(f'Found routes block: {all_routes_m.group()[:2000]}')

# Also look in the edit page HTML for routing data
r_edit = s.get(f'{ADMIN}/index.php/sell/catalog/products/{PID}/edit',
               params={'_token': cat_token}, allow_redirects=True)
edit_tok = re.search(r'[?&]_token=([A-Za-z0-9._\-]+)', r_edit.url).group(1)
html = r_edit.text

print('\n--- Routing data in edit page HTML ---')
routing_in_html = re.findall(r'admin_\w+_(?:save|update|edit|put)[^\s"\']{0,200}', html, re.I)
for r in routing_in_html[:10]:
    print(f'  {r[:150]}')

# Look for the form submit handler in the page
print('\n--- Form action and method ---')
form_tags = re.findall(r'<form[^>]{0,400}>', html, re.I)
for form_tag in form_tags:
    if 'product' in form_tag.lower() or 'action' in form_tag.lower():
        print(f'  {form_tag[:300]}')

# Check what happens with raw POST - inspect response headers and body sections
print('\n--- Raw POST response analysis ---')
payload = {}
for m in re.finditer(r'<input[^>]+>', html, re.I):
    tag = m.group(0)
    name_m = re.search(r'\bname="([^"]+)"', tag, re.I)
    val_m  = re.search(r'\bvalue="([^"]*)"', tag, re.I)
    if name_m:
        payload[name_m.group(1)] = val_m.group(1) if val_m else ''

payload['_token'] = edit_tok

r_post = s.post(
    f'{ADMIN}/index.php/sell/catalog/products/{PID}/edit',
    params={'_token': edit_tok},
    data=payload,
    headers={'Referer': r_edit.url},
    allow_redirects=False,
)
print(f'POST status: {r_post.status_code}')
print(f'Location: {r_post.headers.get("Location", "NONE")}')
print(f'All response headers:')
for k, v in r_post.headers.items():
    print(f'  {k}: {v}')

# Look for is-invalid or form errors in response
resp_html = r_post.text
invalid_fields = re.findall(r'<(?:input|select|textarea)[^>]*class="[^"]*is-invalid[^"]*"[^>]*name="([^"]+)"', resp_html, re.I)
print(f'\nInvalid fields: {invalid_fields[:10]}')

form_errors = re.findall(r'<span[^>]*class="[^"]*(?:form-text|help-block|invalid-feedback)[^"]*"[^>]*>(.*?)</span>', resp_html, re.I | re.S)
nonempty_errors = [re.sub(r'<[^>]+>', '', e).strip() for e in form_errors if re.sub(r'<[^>]+>', '', e).strip()]
print(f'Form text spans: {nonempty_errors[:10]}')

# Check the data-form-valid attribute on the form
form_valid_m = re.search(r'data-form-(?:valid|submitted|errors)[^>]{0,200}', resp_html, re.I)
if form_valid_m:
    print(f'Form state attrs: {form_valid_m.group()[:200]}')

# Check if the page has a "success" flash message
success_m = re.search(r'alert-success', resp_html, re.I)
print(f'Has alert-success: {bool(success_m)}')
