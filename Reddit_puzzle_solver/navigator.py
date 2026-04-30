from selenium.webdriver.common.by import By

COLORBLIND_SELECTOR = 'footer button[title="Toggle colorblind mode - show letters on colors"]'


def click_colorblind_toggle_recursive(driver, max_depth: int = 6, debug=True):

    found = {"success": False}

    def log(msg):
        if debug:
            print(msg)

    def click_here(path):
        js = """
        const selector = arguments[0];
        function search(root) {
            const hit = root.querySelector(selector);
            if (hit) return hit;
            for (const el of root.querySelectorAll('*')) {
                if (el.shadowRoot) {
                    const found = search(el.shadowRoot);
                    if (found) return found;
                }
            }
            return null;
        }
        return search(document);
        """

        btn = driver.execute_script(js, COLORBLIND_SELECTOR)
        if btn:
            log(f"[FOUND] Toggle in {path}")
            driver.execute_script("arguments[0].click();", btn)
            found["success"] = True
            return True

        log(f"[MISS] {path}")
        return False

    def recurse(depth, path):
        if depth > max_depth:
            return False

        if click_here(path):
            return True

        frames = driver.find_elements(By.TAG_NAME, "iframe")
        log(f"[IFRAMES] {path} → {len(frames)}")

        for i, frame in enumerate(frames):
            src = frame.get_attribute("src") or ""

            # 🔥 IMPORTANT: leave unfiltered for now (debug phase)
            # if "color" not in src.lower():
            #     continue

            try:
                log(f"[ENTER] {path}/{i} → {src[:80]}")
                driver.switch_to.frame(frame)

                if recurse(depth + 1, f"{path}/{i}"):
                    return True  # ✅ stay inside correct iframe

                driver.switch_to.parent_frame()
                log(f"[EXIT] {path}/{i}")

            except Exception as e:
                log(f"[ERROR] {path}/{i}: {e}")
                try:
                    driver.switch_to.parent_frame()
                except Exception:
                    pass

        return False

    driver.switch_to.default_content()
    success = recurse(0, "root")

    if success:
        log("✅ Driver is now inside the correct iframe")
    else:
        log("❌ Failed to find toggle")

    return success