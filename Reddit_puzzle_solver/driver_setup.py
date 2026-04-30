from __future__ import annotations

import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

URL = "https://www.reddit.com/r/ColorPuzzleGame/comments/1syh707/daily_color_puzzle_april_29_2026/"
SCREENSHOT_PATH = Path("puzzle_board.png")


# ----------------------------------------
# DRIVER SETUP
# ----------------------------------------
def build_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    return webdriver.Chrome(options=options)


# ----------------------------------------
# COOKIE HANDLING
# ----------------------------------------
def clear_cookie_overlays(driver: webdriver.Chrome) -> None:
    print("🍪 Attempting to clear cookie modal...")

    js = """
    function clickCookieButtons(root) {
        const buttons = root.querySelectorAll('button');

        for (const btn of buttons) {
            const text = (btn.innerText || '').toLowerCase();

            if (
                text.includes('accept') ||
                text.includes('agree') ||
                text.includes('allow')
            ) {
                btn.click();
                return true;
            }
        }

        for (const el of root.querySelectorAll('*')) {
            if (el.shadowRoot) {
                const found = clickCookieButtons(el.shadowRoot);
                if (found) return true;
            }
        }

        return false;
    }

    return clickCookieButtons(document);
    """

    try:
        clicked = driver.execute_script(js)

        if clicked:
            print("✅ Cookie modal accepted")
            time.sleep(1)
            return

        print("⚠️ No cookie button found — removing overlay manually")

        driver.execute_script("""
            document.querySelectorAll('[role="dialog"]').forEach(el => el.remove());
            document.body.style.overflow = 'auto';
        """)

        time.sleep(1)

    except Exception as e:
        print("❌ Cookie handling failed:", e)


# ----------------------------------------
# BOARD CAPTURE
# ----------------------------------------
def capture_board(driver: webdriver.Chrome, path: Path = SCREENSHOT_PATH) -> str:
    print("🔍 Attempting to locate puzzle board...")

    try:
        # 🎯 Target the Devvit container directly
        element = driver.find_element("css selector", "devvit2-surface")

        print("✅ Devvit surface FOUND — capturing element screenshot")
        element.screenshot(str(path))
        print(f"📸 Saved board screenshot to: {path}")
        return str(path)

    except Exception as e:
        print("❌ Could not find devvit2-surface:", e)

        # fallback debug screenshot
        debug_path = Path("debug_full_page.png")
        driver.save_screenshot(str(debug_path))
        print(f"📸 Debug screenshot saved to: {debug_path}")

        return str(debug_path)


# ----------------------------------------
# MAIN RUN PIPELINE
# ----------------------------------------
def run() -> str:
    driver = build_driver()

    try:
        driver.get(URL)

        # Wait for page load
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

        # Clear cookies
        clear_cookie_overlays(driver)
        time.sleep(1)
        clear_cookie_overlays(driver)

        print("⏳ Waiting for puzzle to render...")

        # ✅ IMPORTANT: simple wait instead of DOM detection
        time.sleep(3)

        return capture_board(driver)

    finally:
        driver.quit()