import os
import shutil
import logging
import pandas as pd
import time
import random
import re
from dotenv import load_dotenv
from backend.scraper.linkedinScraper.utils.chromeUtils import get_chrome_driver
from backend.scraper.linkedinScraper.scraping.scraper import scrape_linkedin

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Constants
DEBUG_OUTPUT = "output/debug_output.csv"

# Sample data
SAMPLE_DATA = [
    {
        "Company": "The Innovation Garage XYZ",
        "City": "Cleveland",
        "State": "OH",
        "Website": "https://theinnovationgarage.com"
    },
    {
        "Company": "openAI",
        "City": "San Francisco",
        "State": "CA",
        "Website": "https://openai.com"
    }
]

def process_test_rows(data):
    results = []
    driver = None
    user_data_dir = None

    try:
        logging.info("🔄 Initializing ChromeDriver...")
        driver = get_chrome_driver(headless=False)
        user_data_dir = driver.capabilities.get("goog:chromeOptions", {}).get("args", [None])[0]
        logging.debug(f"📂 Using profile: {user_data_dir}")

        for idx, row in enumerate(SAMPLE_DATA):
            company = row["Company"]
            logging.info(f"🧪 Scraping {idx + 1}/{len(SAMPLE_DATA)}: {company}")

            try:
                # 🔗 Force navigation to About page
                slug = re.sub(r"[^a-z0-9-]", "", company.lower().replace(" ", "-"))
                about_url = f"https://www.linkedin.com/company/{slug}/about/"
                driver.get(about_url)
                time.sleep(1.5)

                # 🧠 Scrape
                result = scrape_linkedin(
                    driver,
                    company,
                    expected_city=row.get("City"),
                    expected_state=row.get("State"),
                    expected_website=row.get("Website")
                )
                result["Business Name"] = company
                results.append(result)
                logging.info(f"✅ Scraped: {company}")

            except Exception as e:
                logging.error(f"❌ Error scraping {company}: {e}", exc_info=True)
                results.append({"Business Name": company, "Error": str(e)})

            # 👣 Add human-like random delay after each scrape
            delay = random.uniform(4, 8)
            logging.debug(f"🕒 Sleeping {delay:.2f} seconds before next test row...")
            time.sleep(delay)

    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
        if user_data_dir and os.path.exists(user_data_dir):
            shutil.rmtree(user_data_dir, ignore_errors=True)
            logging.debug(f"🧹 Cleaned up profile: {user_data_dir}")

    return results


def run_test():
    os.makedirs("output", exist_ok=True)
    logging.info("🚀 Starting LinkedIn test scraping...")
    results = process_test_rows(SAMPLE_DATA)
    pd.DataFrame(results).to_csv(DEBUG_OUTPUT, index=False)
    logging.info(f"📁 Test complete. Saved results to: {DEBUG_OUTPUT}")


if __name__ == "__main__":
    run_test()
