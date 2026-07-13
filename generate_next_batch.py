"""
Generates the NEXT batch of ~30 pending products from all_products_state.json
into a numbered text file, opens it in Notepad, and marks those products
'in_batch' so a second call won't hand out the same products again.

Refuses to start a new batch while one is still active (unapplied) —
run apply_current_batch.py first.

Usage:
    python generate_next_batch.py          # batch of 30
    python generate_next_batch.py 20       # custom batch size
"""
import json, os, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')

STATE_FILE = r'C:\Users\Damon\Desktop\all_products_state.json'
META_FILE  = r'C:\Users\Damon\Desktop\batch_meta.json'
BATCH_SIZE = int(sys.argv[1]) if len(sys.argv) > 1 else 30

if os.path.exists(META_FILE):
    with open(META_FILE, encoding='utf-8') as f:
        meta = json.load(f)
    print(f'A batch is already active: #{meta["batch_number"]} ({meta["file"]}), '
          f'{len(meta["pids"])} products.')
    print('Run apply_current_batch.py first before starting a new one.')
    sys.exit(1)

with open(STATE_FILE, encoding='utf-8') as f:
    state = json.load(f)

pending = [item for item in state if item['status'] == 'pending']
if not pending:
    print('No pending products left — all done!')
    sys.exit(0)

batch_items = pending[:BATCH_SIZE]
batch_pids = [item['id'] for item in batch_items]

# ── Determine next batch number from existing files on Desktop ─────────────
n = 1
while os.path.exists(rf'C:\Users\Damon\Desktop\descriptions_batch_{n:02d}.txt'):
    n += 1
batch_file = rf'C:\Users\Damon\Desktop\descriptions_batch_{n:02d}.txt'

lines = []
lines.append(f'BATCH #{n} — {len(batch_items)} products')
lines.append('INSTRUCTIONS: Edit the Greek text below (English too if you want).')
lines.append('Keep every [[[...]]] marker line EXACTLY as it is (including the ID')
lines.append('number) so the script can read everything back correctly. Save this')
lines.append('file when done and let Claude know THIS BATCH is finished.')
lines.append('=' * 70)
lines.append('')

for item in batch_items:
    pid = item['id']
    url_el = f'https://alegro.gr/{pid}-{item["slug_el"]}.html' if item.get('slug_el') else '(no slug)'
    url_en = f'https://alegro.gr/en/{pid}-{item["slug_en"]}.html' if item.get('slug_en') else '(no slug)'
    lines.append('#' * 70)
    lines.append(f'PID {pid}  |  {item["name_en"]}  /  {item["name_el"]}')
    lines.append(f'Live EL: {url_el}')
    lines.append(f'Live EN: {url_en}')
    lines.append('#' * 70)
    lines.append('')
    lines.append(f'[[[DESC_EL_{pid}]]]')
    lines.append(item['desc_el'])
    lines.append(f'[[[/DESC_EL_{pid}]]]')
    lines.append('')
    lines.append(f'[[[SHORT_EL_{pid}]]]')
    lines.append(item['short_el'])
    lines.append(f'[[[/SHORT_EL_{pid}]]]')
    lines.append('')
    lines.append(f'[[[DESC_EN_{pid}]]]')
    lines.append(item['desc_en'])
    lines.append(f'[[[/DESC_EN_{pid}]]]')
    lines.append('')
    lines.append(f'[[[SHORT_EN_{pid}]]]')
    lines.append(item['short_en'])
    lines.append(f'[[[/SHORT_EN_{pid}]]]')
    lines.append('')
    lines.append('')

with open(batch_file, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

# Mark these as in_batch so the next call skips them
for item in state:
    if item['id'] in batch_pids:
        item['status'] = 'in_batch'
with open(STATE_FILE, 'w', encoding='utf-8') as f:
    json.dump(state, f, ensure_ascii=False, indent=2)

with open(META_FILE, 'w', encoding='utf-8') as f:
    json.dump({'batch_number': n, 'file': batch_file, 'pids': batch_pids}, f, ensure_ascii=False, indent=2)

remaining = sum(1 for item in state if item['status'] == 'pending')
print(f'Batch #{n}: {len(batch_items)} products -> {batch_file}')
print(f'{remaining} products still pending after this batch.')
subprocess.Popen(['notepad.exe', batch_file])
print('Opened in Notepad.')
