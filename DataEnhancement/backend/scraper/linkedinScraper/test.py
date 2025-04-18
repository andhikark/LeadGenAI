# backend/linkedinScraper/test.py

import os
import shutil
import uuid
import logging
import pandas as pd
from dotenv import load_dotenv
from linkedinScraper.utils.chromeUtils import get_chrome_driver
from linkedinScraper.scraping.login import login_to_linkedin
from linkedinScraper.scraping.scraper import scrape_linkedin

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Constants
DEBUG_OUTPUT = "output/debug_output.csv"
USERNAME = os.getenv("LINKEDIN_USERNAME") or "rafleadgen07@gmail.com"
PASSWORD = os.getenv("LINKEDIN_PASSWORD") or "123Testing90."

# Sample data
SAMPLE_DATA = [
   {
    "Company": "The Innovation Garage XYZ",
    "City": "Cleveland",
    "State": "OH",
    "Website": "https://theinnovationgarage.com"
},
    # Add more test rows if needed
]

def process_single_test_row(row, max_retries=2):
    attempts = 0
    user_data_dir = None

    while attempts <= max_retries:
        try:
            logging.info(f"\n🔄 [STEP] Initializing ChromeDriver... (Attempt {attempts + 1})")
            driver = get_chrome_driver(headless=False)

            user_data_dir = driver.capabilities.get("goog:chromeOptions", {}).get("args", [None])[0]
            logging.debug(f"📂 Using profile: {user_data_dir}")

            logging.info(f"🔐 [STEP] Logging in to LinkedIn...")

            logging.info(f"🔎 [STEP] Scraping data for: {row['Company']}")
            result = scrape_linkedin(
                driver,
                row["Company"],
                expected_city=row.get("City"),
                expected_state=row.get("State"),
                expected_website=row.get("Website")
            )
            result["Business Name"] = row["Company"]
            logging.info(f"✅ [SUCCESS] Scraped: {row['Company']}\n")
            return result

        except Exception as e:
            attempts += 1
            logging.error(f"❌ [ERROR] Attempt {attempts} failed for {row['Company']}: {e}")
            if attempts > max_retries:
                return {
                    "Business Name": row["Company"],
                    "Error": f"Failed after {max_retries} attempts: {str(e)}"
                }

        finally:
            try:
                driver.quit()
            except Exception:
                pass
            if user_data_dir and os.path.exists(user_data_dir):
                shutil.rmtree(user_data_dir, ignore_errors=True)
                logging.debug(f"🧹 Cleaned up temp profile: {user_data_dir}")

def test_scraping():
    logging.info("🚀 Starting LinkedIn test scraping...\n")
    os.makedirs("output", exist_ok=True)

    results = []
    for idx, row in enumerate(SAMPLE_DATA):
        logging.info(f"🧪 [TEST] Processing {idx+1}/{len(SAMPLE_DATA)}: {row['Company']}")
        result = process_single_test_row(row)
        logging.debug(f"📊 Result: {result}")
        results.append(result)

    df = pd.DataFrame(results)
    df.to_csv(DEBUG_OUTPUT, index=False)
    logging.info(f"\n📁 [DONE] Test complete. Saved results to: {DEBUG_OUTPUT}")
    logging.debug(f"\n🧾 Preview:\n{df.head()}")
    logging.info("🎉 Finished processing all sample data. Exiting cleanly.")
    
if __name__ == "__main__":
    test_scraping()