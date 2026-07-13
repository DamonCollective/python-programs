"""
Reads the edited descriptions_batch.txt back, updates review_state.json
for every product found in it (status -> 'done'), ready for
upload_reviewed_descriptions.py.

Usage:
    python apply_batch_file.py
"""
import json, re, sys

sys.stdout.reconfigure(encoding='utf-8')

STATE_FILE = r'C:\Users\Damon\Desktop\review_state.json'
BATCH_FILE = r'C:\Users\Damon\Desktop\descriptions_batch.txt'

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

for pid, item in by_id.items():
    if item['status'] != 'pending':
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

print(f'Updated {len(updated)} products: {updated}')
if missing_markers:
    print(f'\nCould not find complete markers for {len(missing_markers)} products '
          f'(left as pending): {missing_markers}')
    print('Check that none of the [[[...]]] marker lines were edited/deleted.')
