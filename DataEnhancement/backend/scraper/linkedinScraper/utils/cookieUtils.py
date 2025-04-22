import os
import time
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def inject_li_at_cookie(driver):
    """
    Inject only the li_at cookie into the current Selenium session.
    """
    li_at = os.getenv("LI_AT")
    if not li_at:
        raise ValueError("❌ Missing environment variable: LI_AT")

    # Navigate to LinkedIn root to set correct domain context
    driver.get("https://www.linkedin.com")
    time.sleep(2)

    # Clear any existing cookies
    driver.delete_all_cookies()

    logging.info("🍪 Injecting li_at session cookie...")
    driver.add_cookie({
        "name": "li_at",
        "value": li_at.strip(),
        "domain": ".linkedin.com",
        "path": "/",
        "secure": True,
        "httpOnly": True,
    })
    logging.info("✅ li_at cookie injected successfully.")
