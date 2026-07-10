import time
import math
import random
import threading
import winsound
import tkinter as tk
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# ─── CONFIG ───────────────────────────────────────────────────────────
FEDEX_URL   = "https://www.fedex.com/secure-login/el-gr/"
CHECK_EVERY = 15 * 60   # 15 minutes
# ──────────────────────────────────────────────────────────────────────

COLORS = [
    '#FF4444', '#FF8800', '#FFFF00', '#44FF44',
    '#4488FF', '#FF44FF', '#00FFFF', '#FF6600', '#FFFFFF'
]

class Particle:
    def __init__(self, canvas, x, y, color):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(3, 12)
        self.dx = math.cos(angle) * speed
        self.dy = math.sin(angle) * speed
        self.canvas = canvas
        self.x = x
        self.y = y
        size = random.randint(4, 9)
        self.id = canvas.create_oval(x, y, x + size, y + size, fill=color, outline='')
        self.life = random.randint(35, 65)
        self.age = 0

    def update(self):
        self.age += 1
        self.dy += 0.35  # gravity
        self.x += self.dx
        self.y += self.dy
        self.canvas.move(self.id, self.dx, self.dy)
        if self.age >= self.life:
            self.canvas.delete(self.id)
            return False
        return True

def play_fanfare():
    notes = [
        (523, 120), (659, 120), (784, 120),
        (1047, 350), (784, 120), (1047, 500),
        (1175, 700)
    ]
    for freq, dur in notes:
        winsound.Beep(freq, dur)
    time.sleep(0.3)
    for _ in range(3):
        winsound.Beep(1047, 150)
        time.sleep(0.05)

def show_fireworks():
    root = tk.Tk()
    root.title("FedEx Monitor")
    root.attributes('-fullscreen', True)
    root.configure(bg='black')

    canvas = tk.Canvas(root, bg='black', highlightthickness=0)
    canvas.pack(fill='both', expand=True)
    root.update()

    W = root.winfo_width()
    H = root.winfo_height()

    canvas.create_text(W // 2, H // 2 - 90,
                       text="** FEDEX IS UP! **",
                       font=('Arial Black', 72, 'bold'), fill='#FFFF00')
    canvas.create_text(W // 2, H // 2 + 10,
                       text="GO SHIP NOW!",
                       font=('Arial Black', 54, 'bold'), fill='#FF4444')
    canvas.create_text(W // 2, H // 2 + 100,
                       text="click or press any key to close",
                       font=('Arial', 22), fill='#888888')

    root.bind('<Key>', lambda e: root.destroy())
    root.bind('<Button-1>', lambda e: root.destroy())

    particles = []
    counter = [0]

    def launch(x=None, y=None):
        fx = x if x else random.randint(W // 6, 5 * W // 6)
        fy = y if y else random.randint(H // 8, H // 2)
        color = random.choice(COLORS)
        for _ in range(50):
            particles.append(Particle(canvas, fx, fy, color))

    def animate():
        counter[0] += 1
        if counter[0] % 18 == 0:
            launch()
        dead = [p for p in particles if not p.update()]
        for p in dead:
            particles.remove(p)
        root.after(25, animate)

    for _ in range(6):
        launch()

    animate()
    threading.Thread(target=play_fanfare, daemon=True).start()
    root.mainloop()

def check_fedex_login():
    opts = Options()
    opts.add_argument('--headless')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=opts)
    try:
        driver.get(FEDEX_URL)
        time.sleep(8)
        url = driver.current_url
        print(f"  URL: {url}")
        return '#/error' not in url
    except Exception as e:
        print(f"  Browser error: {e}")
        return False
    finally:
        driver.quit()

print("=" * 50)
print("FedEx login monitor — checking every 15 min")
print("Keep this window open. Ctrl+C to stop.")
print("=" * 50)

while True:
    print(f"\n[{time.strftime('%H:%M:%S')}] Checking FedEx...")
    if check_fedex_login():
        print("  FedEx login is UP! Launching fireworks...")
        show_fireworks()
        print("Done.")
        break
    else:
        nxt = time.strftime('%H:%M', time.localtime(time.time() + CHECK_EVERY))
        print(f"  Still down. Next check at {nxt}.")
    time.sleep(CHECK_EVERY)
