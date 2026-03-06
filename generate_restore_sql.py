"""
Parse the SQL backup and generate UPDATE statements to restore product descriptions.
Output: restore_descriptions.sql — run this in phpMyAdmin.
"""
import re
import sys

BACKUP = r'C:\Users\Damon\Desktop\ALLA\sqlqueries\1753088504-255a1d97.sql'
OUTPUT = r'C:\Users\Damon\Desktop\restore_descriptions.sql'

sys.stdout.reconfigure(encoding='utf-8')

# Read the backup
with open(BACKUP, encoding='utf-8', errors='replace') as f:
    content = f.read()

# Find the product_lang INSERT blocks
# They look like: INSERT INTO `l9n7b_product_lang` VALUES\n(row),(row),...;
insert_blocks = re.findall(
    r"INSERT INTO `l9n7b_product_lang` VALUES\s*\n(.*?);",
    content, re.S
)

print(f"Found {len(insert_blocks)} INSERT blocks")

# Parse each row value tuple
# Columns: id_product, id_shop, id_lang, description, description_short,
#           link_rewrite, meta_description, meta_keywords, meta_title, name,
#           available_now, available_later, delivery_in_stock, delivery_out_stock

def parse_rows(block):
    """Parse comma-separated SQL value tuples, handling nested quotes."""
    rows = []
    i = 0
    while i < len(block):
        if block[i] == '(':
            # Find matching closing paren, respecting quoted strings
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
    """Parse a single VALUES tuple like ('a','b',NULL,...) into a list."""
    # Strip outer parens
    inner = row_str.strip()
    if inner.startswith('('):
        inner = inner[1:]
    if inner.endswith(')'):
        inner = inner[:-1]

    values = []
    i = 0
    while i < len(inner):
        # Skip whitespace
        while i < len(inner) and inner[i] in ' \t\n':
            i += 1
        if i >= len(inner):
            break

        if inner[i:i+4] == 'NULL':
            values.append(None)
            i += 4
        elif inner[i] == "'":
            # String value
            i += 1
            s = []
            while i < len(inner):
                c = inner[i]
                if c == '\\' and i + 1 < len(inner):
                    nc = inner[i+1]
                    esc = {'n': '\n', 'r': '\r', 't': '\t', '\\': '\\', "'": "'", '"': '"'}
                    s.append(esc.get(nc, nc))
                    i += 2
                elif c == "'":
                    i += 1
                    break
                else:
                    s.append(c)
                    i += 1
            values.append(''.join(s))
        else:
            # Unquoted value (number etc)
            j = i
            while j < len(inner) and inner[j] not in ',':
                j += 1
            values.append(inner[i:j].strip())
            i = j

        # Skip comma
        while i < len(inner) and inner[i] in ' \t\n,':
            if inner[i] == ',':
                i += 1
                break
            i += 1

    return values

def sql_val(v):
    """Format a Python value as a SQL value."""
    if v is None:
        return 'NULL'
    # Escape backslashes first, then quotes, then newlines/tabs
    v = v.replace('\\', '\\\\')
    v = v.replace("'", "\\'")
    v = v.replace('\n', '\\n')
    v = v.replace('\r', '\\r')
    return f"'{v}'"

all_rows = []
for block in insert_blocks:
    row_strings = parse_rows(block)
    for rs in row_strings:
        vals = parse_values(rs)
        if len(vals) >= 10:
            row = {
                'id_product':        vals[0],
                'id_shop':           vals[1],
                'id_lang':           vals[2],
                'description':       vals[3],
                'description_short': vals[4],
                'link_rewrite':      vals[5],
                'meta_description':  vals[6],
                'meta_keywords':     vals[7],
                'meta_title':        vals[8],
                'name':              vals[9],
            }
            all_rows.append(row)

print(f"Parsed {len(all_rows)} product-lang rows")

# Generate UPDATE SQL
updates = []
for r in all_rows:
    pid  = r['id_product']
    shop = r['id_shop']
    lang = r['id_lang']

    # Only update if we have something to restore
    has_content = any(r[f] is not None for f in
                      ['description', 'description_short', 'meta_title',
                       'meta_description', 'meta_keywords'])
    # Always update name and link_rewrite too (safety)

    sets = []
    sets.append(f"description={sql_val(r['description'])}")
    sets.append(f"description_short={sql_val(r['description_short'])}")
    if r['name'] is not None:
        sets.append(f"name={sql_val(r['name'])}")
    if r['link_rewrite'] is not None:
        sets.append(f"link_rewrite={sql_val(r['link_rewrite'])}")
    if r['meta_title'] is not None:
        sets.append(f"meta_title={sql_val(r['meta_title'])}")
    if r['meta_description'] is not None:
        sets.append(f"meta_description={sql_val(r['meta_description'])}")
    if r['meta_keywords'] is not None:
        sets.append(f"meta_keywords={sql_val(r['meta_keywords'])}")

    sql = (f"UPDATE `l9n7b_product_lang` SET {', '.join(sets)} "
           f"WHERE id_product={pid} AND id_shop={shop} AND id_lang={lang};")
    updates.append(sql)

with open(OUTPUT, 'w', encoding='utf-8') as f:
    f.write("-- Restore product descriptions from July 2025 backup\n")
    f.write(f"-- Generated from: 1753088504-255a1d97.sql\n")
    f.write(f"-- Total UPDATE statements: {len(updates)}\n\n")
    f.write("SET NAMES utf8mb4;\n\n")
    for sql in updates:
        f.write(sql + '\n')

print(f"\nGenerated {len(updates)} UPDATE statements -> {OUTPUT}")
print("Run restore_descriptions.sql in phpMyAdmin to restore all descriptions.")
