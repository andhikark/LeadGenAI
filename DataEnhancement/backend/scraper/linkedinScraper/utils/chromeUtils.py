import os
import time
import random
import logging
from urllib.parse import urlparse
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from dotenv import load_dotenv

load_dotenv()  # Make sure .env is loaded

def generate_smartproxy_url(batch_id: str, duration_hours: int = 15) -> str:
    session_segment = batch_id.replace(" ", "_")
    user_segment = f"user-{os.getenv('DECODO_USERNAME')}-sessionduration-{duration_hours}-session-{session_segment}"
    return f"http://{os.getenv('DECODO_HOSTNAME')}:{os.getenv('DECODO_PORT')}"

def get_chrome_driver(headless=False, max_retries=3):
    proxy_url = generate_smartproxy_url("linkedin_batch_1")
    parsed = urlparse(proxy_url)
    proxy_host = parsed.hostname
    proxy_port = parsed.port

    user_data_dir = os.path.abspath("linkedin_profile_1")
    li_at = os.getenv("LI_AT")

    for attempt in range(max_retries):
        try:
            options = uc.ChromeOptions()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-notifications")
            options.add_argument("--start-maximized")
            options.add_argument(f"--user-data-dir={user_data_dir}")
            options.add_argument(f"--proxy-server=http://{proxy_host}:{proxy_port}")
            options.add_argument(f"--user-agent={random_user_agent()}")

            driver = uc.Chrome(options=options, headless=headless, use_subprocess=True)
            driver.implicitly_wait(10)

            # ✅ Inject li_at cookie
            if li_at:
                driver.get("https://www.linkedin.com")
                driver.execute_cdp_cmd("Network.setCookie", {
                    "name": "li_at",
                    "value": li_at.strip(),
                    "domain": ".linkedin.com",
                    "path": "/",
                    "secure": True,
                    "httpOnly": True,
                })
                logging.info("🍪 Injected li_at cookie into session.")
            else:
                logging.warning("⚠️ LI_AT not found in environment. Cookie not injected.")

            logging.info("✅ Chrome driver launched with undetected-chromedriver and proxy.")
            return driver

        except Exception as e:
            logging.error(f"❌ Attempt {attempt + 1} failed: {e}")
            time.sleep(random.uniform(1.5, 3.5))

    raise RuntimeError("All attempts to launch Chrome failed.")

def random_user_agent():
    return random.choice([
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0"
    ])
