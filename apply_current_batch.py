"""
Reads the currently active batch file back (per batch_meta.json), updates
all_products_state.json for those products (status -> 'done'), then clears
batch_meta.json so generate_next_batch.py can hand out the next batch.

Does NOT upload to alegro.gr — run upload_reviewed_descriptions.py
--state=all_products_state.json <pids...> after this, using the PIDs this
script prints out.

Usage:
    python apply_current_batch.py
"""
import json, os, sys

sys.stdout.reconfigure(encoding='utf-8')

STATE_FILE = r'C:\Users\Damon\Desktop\all_products_state.json'
META_FILE  = r'C:\Users\Damon\Desktop\batch_meta.json'

if not os.path.exists(META_FILE):
    print('No active batch found (batch_meta.json missing). '
          'Run generate_next_batch.py first.')
    sys.exit(1)

with open(META_FILE, encoding='utf-8') as f:
    meta = json.load(f)

batch_file = meta['file']
batch_pids = set(meta['pids'])

with open(batch_file, encoding='utf-8') as f:
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

for pid in sorted(batch_pids):
    item = by_id.get(pid)
    if item is None or item['status'] != 'in_batch':
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

print(f'Batch #{meta["batch_number"]}: updated {len(updated)} products.')
print(f'PIDs: {updated}')

if missing_markers:
    print(f'\nCould not parse {len(missing_markers)} products (left as in_batch, '
          f'still active): {missing_markers}')
    print('Fix the markers in the batch file and re-run this script.')
else:
    os.remove(META_FILE)
    print('\nBatch fully applied. batch_meta.json cleared — ready for the next batch.')
    print(f'\nNext: python upload_reviewed_descriptions.py --state=all_products_state.json {" ".join(map(str, updated))}')
