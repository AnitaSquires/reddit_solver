

COLORBLIND_SELECTOR = 'footer button[title="Toggle colorblind mode - show letters on colors"]'
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


if __name__ == "__main__":
    screenshot_path = run()
    print(f"Saved screenshot to: {screenshot_path}")