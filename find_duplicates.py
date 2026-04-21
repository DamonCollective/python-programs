"""
Find duplicate files in D:\ALL GRAPHΙCS and move them to D:\DUPLICATES.
For each group of identical files, keeps the one with the shortest path
(closest to root / least nested), moves the rest to D:\DUPLICATES.
If two moved files would have the same filename, appends _2, _3, etc.
"""

import os
import hashlib
import shutil
from collections import defaultdict

SOURCE = r"D:\ALL GRAPHΙCS"
DEST   = r"D:\DUPLICATES"

def file_hash(path, buf=1 << 20):
    h = hashlib.md5()
    with open(path, "rb") as f:
        while chunk := f.read(buf):
            h.update(chunk)
    return h.hexdigest()

def pick_keeper(paths):
    """Keep the file with the fewest path components (shallowest).
    Tie-break: shortest full path string."""
    return min(paths, key=lambda p: (p.count(os.sep), len(p)))

def safe_dest_name(dest_dir, filename):
    """Return a unique filename inside dest_dir, appending _2, _3 if needed."""
    base, ext = os.path.splitext(filename)
    candidate = filename
    counter = 2
    while os.path.exists(os.path.join(dest_dir, candidate)):
        candidate = f"{base}_{counter}{ext}"
        counter += 1
    return candidate

def main():
    print(f"Scanning {SOURCE} ...")
    os.makedirs(DEST, exist_ok=True)

    hash_map = defaultdict(list)
    total = 0
    errors = 0

    for root, dirs, files in os.walk(SOURCE):
        # Skip the DUPLICATES folder if somehow nested
        dirs[:] = [d for d in dirs if os.path.join(root, d) != DEST]
        for fname in files:
            fpath = os.path.join(root, fname)
            try:
                h = file_hash(fpath)
                hash_map[h].append(fpath)
                total += 1
                if total % 500 == 0:
                    print(f"  Hashed {total} files...")
            except Exception as e:
                print(f"  ERROR reading {fpath}: {e}")
                errors += 1

    print(f"\nTotal files hashed: {total}  (errors: {errors})")

    dup_groups = {h: paths for h, paths in hash_map.items() if len(paths) > 1}
    print(f"Duplicate groups found: {len(dup_groups)}")

    moved = 0
    for h, paths in dup_groups.items():
        keeper = pick_keeper(paths)
        to_move = [p for p in paths if p != keeper]
        for src in to_move:
            fname = os.path.basename(src)
            dest_name = safe_dest_name(DEST, fname)
            dest_path = os.path.join(DEST, dest_name)
            try:
                shutil.move(src, dest_path)
                moved += 1
            except Exception as e:
                print(f"  ERROR moving {src}: {e}")

    print(f"\nDone. Moved {moved} duplicate files to {DEST}")
    print(f"Kept 1 copy of each in {SOURCE}")

if __name__ == "__main__":
    main()
