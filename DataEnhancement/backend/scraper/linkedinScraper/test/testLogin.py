import os
import time
import logging
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from backend.scraper.linkedinScraper.scraping.login import login_to_linkedin
from backend.scraper.linkedinScraper.scraping.scraper import scrape_linkedin
from backend.scraper.linkedinScraper.utils.chromeUtils import get_chrome_driver

from backend.scraper.linkedinScraper.scraping.login import login_to_linkedin

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Load credentials
load_dotenv()
USERNAME = os.getenv("LINKEDIN_USERNAME") or "leadgenraf@gmail.com"
PASSWORD = os.getenv("LINKEDIN_PASSWORD") or "123Testing90."

# Sample data
SAMPLE_DATA = {
    "Company": "The Innovation Garage XYZ",
    "City": "Cleveland",
    "State": "OH",
    "Website": "https://theinnovationgarage.com"
}

def test_login_and_scrape():
    driver = get_chrome_driver(headless=False)
    try:
        # Step 1: Land on signup page
        logging.info("🌐 Opening LinkedIn signup page")
        driver.get("https://www.linkedin.com/signup")
        time.sleep(2)

        # Step 2: Redirect to login and perform auto-login
        logging.info("🔁 Redirecting to login")
        driver.get("https://www.linkedin.com/login")
        time.sleep(2)

        if not login_to_linkedin(driver, USERNAME, PASSWORD):
            logging.error("❌ Auto-login failed. Test aborted.")
            return

        # Step 3: Scrape company after login
        logging.info(f"🧠 Now scraping: {SAMPLE_DATA['Company']}")
        result = scrape_linkedin(
            driver,
            SAMPLE_DATA["Company"],
            expected_city=SAMPLE_DATA["City"],
            expected_state=SAMPLE_DATA["State"],
            expected_website=SAMPLE_DATA["Website"]
        )

        logging.info("✅ Scraping completed. Result:")
        for k, v in result.items():
            print(f"{k}: {v}")

    finally:
        input("⏸️ Press ENTER to close browser...")
        driver.quit()

if __name__ == "__main__":
    test_login_and_scrape()