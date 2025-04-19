import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from .human import human_type, human_delay

def login_to_linkedin(driver, username, password):
    logging.info("🔐 Starting login process...")

    # Go to login page directly
    driver.get('https://www.linkedin.com/login')
    human_delay(1.5, 2)

    try:
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'username'))
        )
        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'password'))
        )

        username_field.clear()
        password_field.clear()

        # Use human-like typing
        human_type(username_field, username)
        human_type(password_field, password)

        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@type="submit"]'))
        )

        human_delay(1, 1.5)
        login_button.click()
        human_delay(2.5, 2.5)

    except TimeoutException:
        logging.warning("⚠️ Login form not found. Aborting login.")
        return False

    # --- Checkpoint/Captcha handling ---
    for _ in range(3):
        page_source = driver.page_source.lower()
        current_url = driver.current_url

        if any(x in current_url for x in ["checkpoint", "login"]) or \
           any(x in page_source for x in ["captcha", "verify your identity", "security verification"]):
            screenshot_path = f"output/login_checkpoint_{int(time.time())}.png"
            driver.save_screenshot(screenshot_path)
            logging.warning(f"⚠️ CAPTCHA or checkpoint detected. Screenshot saved: {screenshot_path}")
            print(f"\n⚠️ Manual login required. Please complete it in the browser.")
            input("⏸️ Press [ENTER] when you're logged in and see your feed...")

            if any(x in driver.current_url for x in ["feed", "mynetwork", "/in/"]):
                logging.info("✅ Manual login successful.")
                return True
            else:
                logging.warning("❌ Still not logged in.")
                human_delay(1.5, 1.5)
        else:
            break

    if any(x in driver.current_url for x in ["feed", "mynetwork", "/in/"]):
        logging.info("✅ Logged in programmatically.")
        return True

    logging.error("❌ Login failed.")
    return False