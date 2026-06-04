"""
greecedest_traffic.py
Simulates human browsing on greecedestinations.weebly.com.
Each session: open browser → browse randomly → close.
Between sessions: wait 5–15 minutes. Runs until you press Ctrl+C.
"""

import time, random, sys
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "https://greecedestinations.weebly.com"

# ─── human-like helpers ──────────────────────────────────────────────────────

def pause(lo=1.0, hi=3.5):
    time.sleep(random.uniform(lo, hi))

def slow_scroll(driver, direction="down", steps=None):
    steps = steps or random.randint(3, 8)
    for _ in range(steps):
        dist = random.randint(150, 400) * (1 if direction == "down" else -1)
        driver.execute_script(f"window.scrollBy(0, {dist});")
        time.sleep(random.uniform(0.3, 0.9))

def random_mouse_move(driver):
    try:
        body = driver.find_element(By.TAG_NAME, "body")
        size = driver.get_window_size()
        ac = ActionChains(driver)
        for _ in range(random.randint(2, 5)):
            x = random.randint(50, size["width"] - 50)
            y = random.randint(50, size["height"] - 50)
            ac.move_to_element_with_offset(body, x - size["width"]//2, y - size["height"]//2)
            ac.pause(random.uniform(0.2, 0.6))
        ac.perform()
    except Exception:
        pass

def read_page(driver, seconds=None):
    """Scroll and linger as if reading."""
    seconds = seconds or random.uniform(15, 45)
    deadline = time.time() + seconds
    direction = "down"
    while time.time() < deadline:
        slow_scroll(driver, direction, steps=random.randint(2, 5))
        random_mouse_move(driver)
        pause(1.5, 4.0)
        if random.random() < 0.25:
            direction = "up" if direction == "down" else "down"

def click_random_link(driver):
    """Click a random internal link on the current page. Returns True on success."""
    try:
        links = driver.find_elements(By.CSS_SELECTOR, "a[href]")
        internal = [
            l for l in links
            if l.is_displayed()
            and ("weebly.com" in (l.get_attribute("href") or "") or
                 (l.get_attribute("href") or "").startswith("/"))
            and (l.get_attribute("href") or "") != driver.current_url
        ]
        if not internal:
            return False
        choice = random.choice(internal)
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", choice)
        pause(0.5, 1.5)
        choice.click()
        return True
    except Exception:
        return False

# ─── session ─────────────────────────────────────────────────────────────────

def make_driver():
    opts = Options()
    opts.set_preference("general.useragent.override",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0")
    # keep browser visible so it looks real
    driver = webdriver.Firefox(options=opts)
    driver.set_window_size(random.randint(1100, 1440), random.randint(750, 900))
    driver.set_window_position(random.randint(0, 80), random.randint(0, 40))
    return driver

def run_session(session_num):
    print(f"\n[Session {session_num}] Opening browser…")
    driver = make_driver()
    try:
        # land on homepage
        driver.get(BASE_URL)
        pause(2, 4)
        print(f"  → {driver.current_url}")

        # read homepage
        read_page(driver, seconds=random.uniform(20, 50))

        # browse 2–5 more pages
        pages_to_visit = random.randint(2, 5)
        visited = 0
        attempts = 0
        while visited < pages_to_visit and attempts < 12:
            attempts += 1
            if click_random_link(driver):
                pause(2, 5)
                print(f"  → {driver.current_url}")
                read_page(driver)
                visited += 1
                # occasionally go back
                if random.random() < 0.3 and visited > 1:
                    driver.back()
                    pause(2, 4)
                    read_page(driver, seconds=random.uniform(8, 20))
            else:
                # no link found — scroll a bit and try again
                slow_scroll(driver)
                pause(1, 2)

        # linger a moment before closing
        pause(3, 8)
        print(f"  Session {session_num} done — {visited} pages visited.")
    except Exception as e:
        print(f"  Session error: {e}")
    finally:
        try:
            driver.quit()
        except Exception:
            pass

# ─── main loop ───────────────────────────────────────────────────────────────

def main():
    session = 0
    print("greecedestinations traffic bot — Ctrl+C to stop.")
    while True:
        session += 1
        run_session(session)
        wait_min = random.uniform(5, 15)
        print(f"  Waiting {wait_min:.1f} minutes before next session…")
        time.sleep(wait_min * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
        sys.exit(0)
