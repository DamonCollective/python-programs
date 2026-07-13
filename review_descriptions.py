"""
Step 2 of the description-review pipeline.

Interactive, resumable review of the products flagged by
fetch_priority_products.py. For each product:
  - writes its current EN/EL name + description + short description to a
    text file and opens it in Notepad
  - you edit (mainly the Greek text), save the file, and press Enter here
  - the edited text is read back and saved to review_state.json
  - moves on to the next product automatically

Progress is saved after every product, so you can stop (Ctrl+C, or 'q' at
a prompt) and resume later — it picks up wherever you left off.

Usage:
    python review_descriptions.py
"""
import json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')

QUEUE_FILE = r'C:\Users\Damon\Desktop\priority_queue.json'
STATE_FILE = r'C:\Users\Damon\Desktop\review_state.json'
EDIT_FILE  = r'C:\Users\Damon\Desktop\review_current.txt'

MARKER_START = '===EN DESCRIPTION==='
MARKERS = [
    '===EN DESCRIPTION===',
    '===EL DESCRIPTION===',
    '===EN SHORT DESCRIPTION===',
    '===EL SHORT DESCRIPTION===',
    '===END===',
]


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, encoding='utf-8') as f:
            return json.load(f)
    with open(QUEUE_FILE, encoding='utf-8') as f:
        queue = json.load(f)
    for item in queue:
        item['status'] = 'pending'
    return queue


def save_state(state):
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def write_edit_file(item):
    url_el = f'https://alegro.gr/{item["id"]}-{item["slug_el"]}.html' if item.get('slug_el') else '(no slug saved)'
    url_en = f'https://alegro.gr/en/{item["id"]}-{item["slug_en"]}.html' if item.get('slug_en') else '(no slug saved)'
    content = f"""INSTRUCTIONS: Edit the text below (mainly the Greek description/short
description — English too if you want). Keep the "===...===" marker lines
exactly as they are so the script can read the sections back correctly.
Save this file (Ctrl+S), then go back to the terminal window and press Enter.

PRODUCT ID: {item['id']}
NAME (EN): {item['name_en']}
NAME (EL): {item['name_el']}
View live (EL): {url_el}
View live (EN): {url_en}
thin_en={item['thin_en']}  thin_el={item['thin_el']}  costume_related={item['costume_related']}

{MARKERS[0]}
{item['desc_en']}

{MARKERS[1]}
{item['desc_el']}

{MARKERS[2]}
{item['short_en']}

{MARKERS[3]}
{item['short_el']}

{MARKERS[4]}
"""
    with open(EDIT_FILE, 'w', encoding='utf-8') as f:
        f.write(content)


def read_edit_file():
    with open(EDIT_FILE, encoding='utf-8') as f:
        content = f.read()
    sections = {}
    for i in range(4):
        start = content.find(MARKERS[i])
        end = content.find(MARKERS[i + 1])
        if start == -1 or end == -1:
            return None  # markers got mangled — bail out safely
        sections[i] = content[start + len(MARKERS[i]):end].strip('\n').strip()
    return {
        'desc_en': sections[0],
        'desc_el': sections[1],
        'short_en': sections[2],
        'short_el': sections[3],
    }


def open_in_notepad(path):
    subprocess.Popen(['notepad.exe', path])


def main():
    state = load_state()
    pending = [item for item in state if item['status'] == 'pending']
    total = len(state)
    done_count = total - len(pending)

    print(f'{done_count}/{total} already reviewed. {len(pending)} remaining.\n')

    for item in pending:
        print('=' * 60)
        print(f'PID {item["id"]}  |  {item["name_en"]}  /  {item["name_el"]}')
        print(f'  thin_en={item["thin_en"]}  thin_el={item["thin_el"]}  costume_related={item["costume_related"]}')

        write_edit_file(item)
        open_in_notepad(EDIT_FILE)

        while True:
            resp = input('Edit + save the file, then press Enter to continue '
                          '(s=skip this product, q=save progress and quit): ').strip().lower()
            if resp == 'q':
                save_state(state)
                print(f'\nProgress saved. {done_count}/{total} done.')
                return
            if resp == 's':
                item['status'] = 'skipped'
                save_state(state)
                print('Skipped.\n')
                break
            parsed = read_edit_file()
            if parsed is None:
                print('Could not read the file back — markers seem to be missing/edited. '
                      'Please check the file and try again, or type q to quit.')
                continue
            item.update(parsed)
            item['status'] = 'done'
            done_count += 1
            save_state(state)
            print(f'Saved. ({done_count}/{total} done)\n')
            break

    print('\nAll products reviewed!')
    still_pending = [i for i in state if i['status'] == 'pending']
    skipped = [i for i in state if i['status'] == 'skipped']
    print(f'Done: {done_count}  Skipped: {len(skipped)}  Still pending: {len(still_pending)}')
    print(f'\nWhen ready, run upload_reviewed_descriptions.py to push the "done" ones to alegro.gr.')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\n\nInterrupted — progress up to the last completed product was already saved.')
