from __future__ import annotations

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

URL = "https://www.reddit.com/r/ColorPuzzleGame/comments/1sjth6v/daily_color_puzzle_april_13_2026/"
COLORBLIND_SELECTOR = 'footer button[title="Toggle colorblind mode - show letters on colors"]'


def build_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
    return webdriver.Chrome(options=options)


def clear_cookie_overlays(driver: webdriver.Chrome) -> None:
    button_xpaths = [
        "//button[contains(., 'Accept')]",
        "//button[contains(., 'I agree')]",
        "//button[contains(., 'Agree')]",
        "//button[contains(., 'Accept all')]",
        "//button[contains(., 'Allow all')]",
        "//button[contains(., 'OK')]",
        "//button[contains(., 'Got it')]",
    ]

    for xpath in button_xpaths:
        try:
            btn = WebDriverWait(driver, 2).until(lambda d: d.find_element(By.XPATH, xpath))
            driver.execute_script("arguments[0].click();", btn)
            print("Accepted cookies via button")
            time.sleep(1.0)
            return
        except Exception:
            pass

    driver.execute_script(
        """
        const selectors = [
            '[role="dialog"]',
            '[aria-modal="true"]',
            '[id*="cookie"]',
            '[class*="cookie"]',
            '[id*="consent"]',
            '[class*="consent"]',
            '[id*="gdpr"]',
            '[class*="gdpr"]'
        ];

        selectors.forEach(sel => {
            document.querySelectorAll(sel).forEach(el => {
                try { el.remove(); } catch (e) {}
            });
        });

        document.body.style.overflow = 'auto';
        document.documentElement.style.overflow = 'auto';
        """
    )
    time.sleep(1.0)


def click_in_current_context(driver: webdriver.Chrome) -> bool:
    """
    Search current document + open shadow roots only.
    """
    js = """
    const selector = arguments[0];

    function search(root) {
      try {
        const hit = root.querySelector(selector);
        if (hit) return hit;

        const all = root.querySelectorAll('*');
        for (const el of all) {
          if (el.shadowRoot) {
            const found = search(el.shadowRoot);
            if (found) return found;
          }
        }
      } catch (e) {}
      return null;
    }

    return search(document);
    """

    try:
        btn = driver.execute_script(js, COLORBLIND_SELECTOR)
        if btn:
            driver.execute_script("arguments[0].click();", btn)
            return True
    except Exception:
        pass

    return False


def click_colorblind_toggle_recursive(driver: webdriver.Chrome, max_depth: int = 6) -> bool:
    """
    Search the current document, open shadow roots, and every iframe recursively.
    """
    def recurse(depth: int, path: str) -> bool:
        if depth > max_depth:
            return False

        if click_in_current_context(driver):
            print(f"Enabled colorblind mode at {path}")
            return True

        frames = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"{path}: found {len(frames)} iframe(s)")

        for i, frame in enumerate(frames, 1):
            src = frame.get_attribute("src") or ""
            name = frame.get_attribute("name") or ""
            entered = False

            try:
                driver.switch_to.frame(frame)
                entered = True
                print(f"Inspecting iframe {path}/{i}: src={src[:120]!r} name={name[:120]!r}")

                if recurse(depth + 1, f"{path}/{i}"):
                    return True

            except Exception as e:
                print(f"iframe {path}/{i} skipped: {e}")
            finally:
                if entered:
                    driver.switch_to.parent_frame()

        return False

    driver.switch_to.default_content()
    return recurse(0, "root")


def run() -> None:
    driver = build_driver()
    try:
        driver.get("https://www.reddit.com")
        driver.delete_all_cookies()

        driver.get(URL)
        time.sleep(5)

        clear_cookie_overlays(driver)

        if not click_colorblind_toggle_recursive(driver):
            print("Could not find the colorblind toggle anywhere.")
            return

        time.sleep(2)

        # carry on with screenshot / crop / extract here

    finally:
        driver.quit()


if __name__ == "__main__":
    run()