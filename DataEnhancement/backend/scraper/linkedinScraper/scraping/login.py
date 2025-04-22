import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from .human import human_type, human_delay

def is_captcha_present(driver):
    try:
        return bool(driver.find_elements(By.XPATH, "//div[contains(@class, 'captcha')]"))
    except:
        return False

def wait_for_feed_or_captcha(driver, max_wait_minutes=5):
    total_wait_time = 0
    while total_wait_time < (max_wait_minutes * 60):
        current_url   = driver.current_url
        page_source   = driver.page_source.lower()

        if "/feed" in current_url:
            logging.info("✅ Detected login success via feed page.")
            return True
        elif "captcha" in current_url or is_captcha_present(driver):
            logging.warning("🛑 CAPTCHA detected. Waiting for user to solve it...")
        elif "checkpoint" in current_url or "verify your identity" in page_source:
            logging.warning("🔒 Security verification or checkpoint page.")
        else:
            logging.info("⏳ Waiting for user login completion or redirect...")

        time.sleep(5)
        total_wait_time += 5

    logging.error("❌ Timeout waiting for LinkedIn feed page.")
    return False

def login_to_linkedin(driver, username, password):
    """
    Assumes `driver` is already launched (with or without profile).
    Returns True once you hit /feed (or manual CAPTCHA solved).
    """
    logging.info("🔐 Starting login process...")
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

        # Human-like typing
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

    return wait_for_feed_or_captcha(driver)

def launch_and_login(username, password, profile_dir=None, headless=False):
    """
    1) Launches Chrome with a persistent profile (or default if None).
    2) Runs the LinkedIn login flow manually (so you can solve CAPTCHA).
    3) Returns the logged-in `driver` or None on failure.
    """
    # 1) Start Chrome
    driver = get_chrome_driver(
        headless     = headless,
        proxy_url    = None,
        user_data_dir= profile_dir
    )

    # 2) Perform login
    success = login_to_linkedin(driver, username, password)
    if not success:
        driver.quit()
        return None

    # 3) At this point your profile_dir holds all cookies, localStorage, etc.
    logging.info(f"🎉 Logged in; profile saved to {profile_dir}")
    return driver