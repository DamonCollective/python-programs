import os
import subprocess
import time

MEMORY_DIR = r"C:\Users\Damon\.claude\projects\C--Users-Damon\memory"
SCRIPTS_DIR = r"C:\Users\Damon\Documents\alegro-scripts"
STAMP_FILE = os.path.join(os.environ.get("TEMP", r"C:\Temp"), "claude_last_pull.txt")
MIN_INTERVAL = 300  # seconds — only pull once per 5 minutes

now = int(time.time())
last = 0
if os.path.exists(STAMP_FILE):
    try:
        with open(STAMP_FILE) as f:
            last = int(f.read().strip())
    except Exception:
        pass

if now - last < MIN_INTERVAL:
    raise SystemExit(0)

with open(STAMP_FILE, "w") as f:
    f.write(str(now))

subprocess.run(["git", "pull", "--rebase", "origin", "main"], cwd=MEMORY_DIR, check=False)
subprocess.run(["git", "pull", "origin", "master"], cwd=SCRIPTS_DIR, check=False)
