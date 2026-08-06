"""
Parses descriptions_batch_03B.txt (batch #3, fine-tuned) back into
all_products_state.json for its 30 PIDs, marks them 'done', clears
batch_meta.json since batch #3 is now finished, and prints the upload
command.

Usage:
    python apply_batch_03B.py
"""
import json, os, sys

sys.stdout.reconfigure(encoding='utf-8')

STATE_FILE = r'C:\Users\Damon\Desktop\all_products_state.json'
BATCH_FILE = r'C:\Users\Damon\Desktop\descriptions_batch_03B.txt'
META_FILE  = r'C:\Users\Damon\Desktop\batch_meta.json'

PIDS = list(range(95, 125))

with open(BATCH_FILE, encoding='utf-8') as f:
    content = f.read()

with open(STATE_FILE, encoding='utf-8') as f:
    state = json.load(f)

by_id = {item['id']: item for item in state}

FIELDS = [
    ('desc_el', 'DESC_EL'),
    ('short_el', 'SHORT_EL'),
    ('desc_en', 'DESC_EN'),
    ('short_en', 'SHORT_EN'),
]

updated = []
missing_markers = []

for pid in PIDS:
    item = by_id.get(pid)
    if item is None:
        missing_markers.append(pid)
        continue
    values = {}
    ok = True
    for field, tag in FIELDS:
        start_marker = f'[[[{tag}_{pid}]]]'
        end_marker = f'[[[/{tag}_{pid}]]]'
        start = content.find(start_marker)
        end = content.find(end_marker)
        if start == -1 or end == -1 or end < start:
            ok = False
            break
        values[field] = content[start + len(start_marker):end].strip('\n').strip()
    if not ok:
        missing_markers.append(pid)
        continue
    item.update(values)
    item['status'] = 'done'
    updated.append(pid)

with open(STATE_FILE, 'w', encoding='utf-8') as f:
    json.dump(state, f, ensure_ascii=False, indent=2)

print(f'Batch 3B: updated {len(updated)} products.')
print(f'PIDs: {updated}')

if missing_markers:
    print(f'\nCould not parse {len(missing_markers)} products: {missing_markers}')
else:
    if os.path.exists(META_FILE):
        os.remove(META_FILE)
        print('\nbatch_meta.json cleared — batch #3 complete.')
    print(f'\nNext: python upload_reviewed_descriptions.py --state="{STATE_FILE}" {" ".join(map(str, updated))}')
