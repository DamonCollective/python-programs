"""Extract all product names from the SQL backup."""
import re, sys
sys.stdout.reconfigure(encoding='utf-8')

BACKUP = r'C:\Users\Damon\Desktop\ALLA\sqlqueries\1753088504-255a1d97.sql'

with open(BACKUP, encoding='utf-8', errors='replace') as f:
    content = f.read()

# Find product_lang INSERT blocks
blocks = re.findall(
    r"INSERT INTO `l9n7b_product_lang` VALUES\s*\n(.*?);",
    content, re.S
)

def parse_rows(block):
    rows = []
    i = 0
    while i < len(block):
        if block[i] == '(':
            j = i + 1
            depth = 1
            in_str = False
            escaped = False
            while j < len(block) and depth > 0:
                c = block[j]
                if escaped:
                    escaped = False
                elif c == '\\':
                    escaped = True
                elif c == "'" and not escaped:
                    in_str = not in_str
                elif not in_str:
                    if c == '(':
                        depth += 1
                    elif c == ')':
                        depth -= 1
                j += 1
            rows.append(block[i:j])
            i = j
        else:
            i += 1
    return rows

def parse_values(row_str):
    inner = row_str.strip()
    if inner.startswith('('): inner = inner[1:]
    if inner.endswith(')'): inner = inner[:-1]
    values = []
    i = 0
    while i < len(inner):
        while i < len(inner) and inner[i] in ' \t\n': i += 1
        if i >= len(inner): break
        if inner[i:i+4] == 'NULL':
            values.append(None); i += 4
        elif inner[i] == "'":
            i += 1
            s = []
            while i < len(inner):
                c = inner[i]
                if c == '\\' and i + 1 < len(inner):
                    nc = inner[i+1]
                    esc = {'n': '\n', 'r': '\r', 't': '\t', '\\': '\\', "'": "'", '"': '"'}
                    s.append(esc.get(nc, nc)); i += 2
                elif c == "'":
                    i += 1; break
                else:
                    s.append(c); i += 1
            values.append(''.join(s))
        else:
            j = i
            while j < len(inner) and inner[j] != ',': j += 1
            values.append(inner[i:j].strip()); i = j
        while i < len(inner) and inner[i] in ' \t\n,':
            if inner[i] == ',': i += 1; break
            i += 1
    return values

# cols: id_product, id_shop, id_lang, description, description_short,
#       link_rewrite, meta_description, meta_keywords, meta_title, name, ...

products = {}  # pid -> {1: name_en, 2: name_el, 'desc_en': ..., 'desc_el': ...}

for block in blocks:
    for rs in parse_rows(block):
        vals = parse_values(rs)
        if len(vals) < 10:
            continue
        pid = vals[0]
        lang = vals[2]
        name = vals[9] or ''
        desc = vals[3] or ''
        desc_short = vals[4] or ''
        if pid not in products:
            products[pid] = {}
        products[pid][f'name_{lang}'] = name
        products[pid][f'desc_{lang}'] = desc
        products[pid][f'short_{lang}'] = desc_short

# Print sorted by pid
print(f"{'PID':>4}  {'EN Name':<50}  {'EL Name':<50}")
print("-" * 110)
for pid in sorted(products.keys(), key=int):
    p = products[pid]
    en = p.get('name_1', '')[:48]
    el = p.get('name_2', '')[:48]
    print(f"{pid:>4}  {en:<50}  {el:<50}")

print(f"\nTotal: {len(products)} products")
