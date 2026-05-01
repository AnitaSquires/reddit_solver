from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


def enable_colorblind_mode(driver):
    print("🔍 Looking for colorblind toggle...")

    try:
        btn = WebDriverWait(driver, 5).until(
            lambda d: d.find_element(
                By.CSS_SELECTOR,
                'button[title="Toggle colorblind letters on colors"]'
            )
        )

        btn.click()
        print("✅ Colorblind toggle clicked")
        return True

    except Exception as e:
        print("❌ Toggle not found:", e)
        return False