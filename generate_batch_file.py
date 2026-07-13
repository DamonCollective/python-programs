"""
Generates one combined text file with all 'pending' products from
review_state.json, for bulk editing in a single Notepad session
(instead of one file per product).

Usage:
    python generate_batch_file.py
"""
import json, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')

STATE_FILE = r'C:\Users\Damon\Desktop\review_state.json'
BATCH_FILE = r'C:\Users\Damon\Desktop\descriptions_batch.txt'

with open(STATE_FILE, encoding='utf-8') as f:
    state = json.load(f)

pending = [item for item in state if item['status'] == 'pending']

lines = []
lines.append('INSTRUCTIONS: Edit the Greek text below (English too if you want).')
lines.append('Keep every [[[...]]] marker line EXACTLY as it is (including the ID')
lines.append('number) so the script can read everything back correctly. Do not')
lines.append('delete or reorder the marker lines. Save this file when done and')
lines.append('let Claude know.')
lines.append('=' * 70)
lines.append('')

for item in pending:
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

with open(BATCH_FILE, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print(f'Wrote {len(pending)} products to {BATCH_FILE}')
subprocess.Popen(['notepad.exe', BATCH_FILE])
print('Opened in Notepad.')
