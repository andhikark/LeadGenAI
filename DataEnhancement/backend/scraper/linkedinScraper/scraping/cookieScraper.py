import time
import os
import logging
from dotenv import set_key, load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium_stealth import stealth  # 🥷 Stealth added here

# Path to .env for saving cookies
env_path = os.path.abspath(".env")

# Load existing environment variables
load_dotenv()
logging.basicConfig(level=logging.INFO)

USERNAME = os.getenv("LINKEDIN_USERNAME") or "leadgenraf2@gmail.com"
PASSWORD = os.getenv("LINKEDIN_PASSWORD") or "123Testing90."



def get_driver():
    options = Options()
    options.add_argument("--start-maximized")
    # options.add_argument("--headless=new")  # Optional for silent operation

    driver = webdriver.Chrome(service=Service(), options=options)

    # 🥷 Apply stealth to driver
    stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )

    return driver


def extract_cookies(driver):
    """
    Extract both li_at and JSESSIONID from current session cookies.
    """
    li_at = None
    jsessionid = None
    for cookie in driver.get_cookies():
        name = cookie.get("name")
        if name == "li_at":
            li_at = cookie.get("value")
            logging.info("✅ li_at cookie found.")
        elif name.upper() == "JSESSIONID":
            jsessionid = cookie.get("value")
            logging.info("✅ JSESSIONID cookie found.")
    return li_at, jsessionid


def save_cookies_to_env(li_at_value, jsessionid_value):
    """
    Save li_at and JSESSIONID into .env file.
    """
    try:
        set_key(env_path, "LI_AT", li_at_value)
        set_key(env_path, "JSESSIONID", jsessionid_value)
        logging.info(f"✅ li_at and JSESSIONID saved to {env_path}")
    except Exception as e:
        logging.error(f"❌ Failed to save cookies to .env: {e}")


def human_like_typing(element, text, delay=0.1):
    for char in text:
        element.send_keys(char)
        time.sleep(delay)


def wait_for_feed_or_captcha(driver, max_wait_minutes=5):
    total_wait_time = 0
    while total_wait_time < (max_wait_minutes * 60):
        current_url = driver.current_url
        if "/feed" in current_url:
            logging.info("✅ Detected login success via feed page.")
            return True
        elif "captcha" in current_url.lower() or is_captcha_present(driver):
            logging.warning("🛑 CAPTCHA detected. Waiting for user to solve it...")
        else:
            logging.info("⏳ Waiting for user login completion or redirect...")

        time.sleep(5)
        total_wait_time += 5
    return False


def is_captcha_present(driver):
    try:
        return bool(driver.find_elements(By.XPATH, "//div[contains(@class, 'captcha') or contains(@class, 'challenge')]"))
    except:
        return False


def login_to_linkedin(driver):
    logging.info("🔐 Starting automated LinkedIn login...")
    driver.get("https://www.linkedin.com/login")

    try:
        username_field = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "username")))
        password_field = driver.find_element(By.ID, "password")

        # Human-like typing
        human_like_typing(username_field, USERNAME, delay=0.08)
        time.sleep(0.3)
        human_like_typing(password_field, PASSWORD, delay=0.08)

        # Submit the form
        password_field.send_keys(Keys.RETURN)

        # Wait for either success or CAPTCHA handling
        return wait_for_feed_or_captcha(driver)

    except TimeoutException:
        logging.error("❌ Timeout waiting for login fields.")
        return False
    except Exception as e:
        logging.error(f"❌ LinkedIn login failed: {e}")
        return False


def scrape_and_save_li_at():
    driver = get_driver()
    try:
        if login_to_linkedin(driver):
            time.sleep(2)
            # Navigate to root to set cookies
            driver.get("https://www.linkedin.com")
            time.sleep(2)

            # Extract both cookies
            li_at, jsessionid = extract_cookies(driver)
            if li_at and jsessionid:
                logging.info(f"🍪 li_at preview: {li_at[:10]}... (truncated)")
                logging.info(f"🍪 JSESSIONID preview: {jsessionid[:10]}... (truncated)")
                save_cookies_to_env(li_at, jsessionid)
            else:
                logging.warning("❌ Missing cookies: li_at or JSESSIONID not found.")
        else:
            logging.warning("❌ Skipping cookie save due to login failure or captcha timeout.")
    except Exception as e:
        logging.error(f"❌ Unexpected error during cookie scrape: {e}", exc_info=True)
    finally:
        driver.quit()


if __name__ == "__main__":
    scrape_and_save_li_at()
