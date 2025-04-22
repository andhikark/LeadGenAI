import os
import time
import logging
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium_stealth import stealth
from backend.scraper.linkedinScraper.utils.proxyUtils import generate_smartproxy_url, SMARTPROXY_GATEWAY, SMARTPROXY_PORT, SMARTPROXY_USER, SMARTPROXY_PASS
from backend.scraper.linkedinScraper.utils.chromeUtils import create_proxy_auth_extension

# === Load environment and li_at cookie ===
load_dotenv()
LI_AT = os.getenv("LI_AT")

if not LI_AT:
    raise ValueError("❌ LI_AT cookie not found in .env file.")

logging.basicConfig(level=logging.INFO)

# === Build stealth driver with proxy ===
def get_stealth_driver_with_proxy():
    chrome_options = Options()
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--start-maximized")
    # Optional: chrome_options.add_argument("--headless=new")

    proxy_url = generate_smartproxy_url(client_id="testcookie")

    # Inject proxy auth extension
    plugin_path = create_proxy_auth_extension(
        SMARTPROXY_GATEWAY, SMARTPROXY_PORT,
        SMARTPROXY_USER, SMARTPROXY_PASS
    )
    chrome_options.add_extension(plugin_path)

    driver = webdriver.Chrome(options=chrome_options)

    stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )

    driver.implicitly_wait(10)
    return driver

def test_li_at_cookie_login():
    driver = get_stealth_driver_with_proxy()
    try:
        logging.info("🌐 Visiting LinkedIn homepage...")
        driver.get("https://www.linkedin.com")
        time.sleep(2)

        logging.info("🧹 Clearing existing cookies...")
        driver.delete_all_cookies()

        logging.info("🍪 Injecting li_at cookie...")
        driver.add_cookie({
            "name": "li_at",
            "value": LI_AT.strip(),
            "domain": ".linkedin.com",
            "path": "/",
            "secure": True,
            "httpOnly": True,
        })

        logging.info("🔁 Navigating to /feed to test session...")
        driver.get("https://www.linkedin.com/feed")
        time.sleep(4)

        current_url = driver.current_url
        page_source = driver.page_source.lower()

        if "429" in page_source or "too many requests" in page_source:
            logging.error("❌ Rate limited by LinkedIn (429).")
        elif "err_too_many_redirects" in page_source or "too many redirects" in page_source:
            logging.error("❌ Too many redirects — possibly expired or invalid li_at.")
        elif "feed" in current_url and "sign" not in page_source:
            logging.info("✅ li_at injection successful. Feed page loaded.")
        else:
            logging.warning("⚠️ li_at may be invalid or expired. Current URL: " + current_url)

    except Exception as e:
        logging.error(f"❌ Error during cookie test: {e}", exc_info=True)
    finally:
        input("🧪 Press Enter to close browser...")
        driver.quit()

if __name__ == "__main__":
    test_li_at_cookie_login()
