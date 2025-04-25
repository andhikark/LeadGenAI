import os
import shutil
import logging
import pandas as pd
import random
import time
from dotenv import load_dotenv
from tqdm import tqdm
from linkedinScraper.utils.chromeUtils import get_chrome_driver
from linkedinScraper.scraping.login import login_to_linkedin, random_scrolling
from linkedinScraper.scraping.scraper import scrape_linkedin
from linkedinScraper.utils.fileUtils import read_csv

# === Setup Logging ===
def get_next_log_filename(log_dir="log", base_name="log"):
    os.makedirs(log_dir, exist_ok=True)
    i = 1
    while os.path.exists(f"{log_dir}/{base_name}_{i}.log"):
        i += 1
    return f"{log_dir}/{base_name}_{i}.log"

log_file = get_next_log_filename()
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# === Environment and Configs ===
load_dotenv()
CSV_INPUT = "input/sample_data1.csv"
CSV_OUTPUT_BASE = "output/linkedin_scraped_results"
USERNAME = os.getenv("LINKEDIN_USERNAME") 
PASSWORD = os.getenv("LINKEDIN_PASSWORD") 

# Reduced batch size to minimize detection risk
BATCH_SIZE = 2

# Increased wait time between requests to appear more human-like
# Min/max seconds to wait between companies in a batch
WAIT_BETWEEN_REQUESTS = (30, 120)  

# Min/max seconds to wait between batches
WAIT_BETWEEN_BATCHES = (300, 600)  # 5-10 minutes between batches

def get_next_output_filename(base):
    i = 3
    while os.path.exists(f"{base}{i}.csv"):
        i += 1
    return f"{base}{i}.csv"

CSV_OUTPUT = get_next_output_filename(CSV_OUTPUT_BASE)

def humanize_wait(min_time, max_time, description="Waiting"):
    """Human-like waiting with progress feedback"""
    wait_time = random.uniform(min_time, max_time)
    logging.info(f"⏱️ {description} for {wait_time:.1f}s")
    
    # For longer waits, show a progress bar
    if wait_time > 10:
        for _ in tqdm(range(int(wait_time)), desc=description, leave=False):
            # Add randomness to each second
            time.sleep(1 + random.uniform(-0.1, 0.1))
    else:
        time.sleep(wait_time)

def run_batch(batch_rows):
    user_data_dir = None
    results = []

    try:
        driver = get_chrome_driver(headless=False)
        user_data_dir = driver.capabilities.get("goog:chromeOptions", {}).get("args", [None])[0]
        
        # Login at the beginning of each batch
        success = login_to_linkedin(driver, USERNAME, PASSWORD)
        if not success:
            logging.error("❌ Failed to login at batch start")
            raise Exception("Login failed")
            
        # Browse the feed for a bit to look more human
        driver.get("https://www.linkedin.com/feed/")
        random_scrolling(driver)
        humanize_wait(5, 15, "Browsing feed")
            
        for i, (_, row) in enumerate(tqdm(enumerate(batch_rows.iterrows()), total=len(batch_rows), desc="🔄 Scraping batch", leave=False)):
            company = row[1].get("Company", "UNKNOWN")
            
            try:
                # Visit a random LinkedIn page occasionally to look more natural
                if random.random() < 0.3:  # 30% chance
                    random_pages = [
                        "https://www.linkedin.com/feed/",
                        "https://www.linkedin.com/mynetwork/",
                        "https://www.linkedin.com/jobs/"
                    ]
                    driver.get(random.choice(random_pages))
                    random_scrolling(driver)
                    humanize_wait(3, 10, "Browsing LinkedIn")
                
                # Scrape the target company
                result = scrape_linkedin(
                    driver,
                    company,
                    expected_city=row[1].get("City"),
                    expected_state=row[1].get("State"),
                    expected_website=row[1].get("Website")
                )
                result["Business Name"] = company
                results.append(result)
                logging.info(f"✅ Scraped: {company}")
                
                # Wait between requests if not the last item
                if i < len(batch_rows) - 1:
                    humanize_wait(*WAIT_BETWEEN_REQUESTS, f"Cooling down after {company}")
                    
            except Exception as e:
                logging.error(f"❌ Error in {company}: {e}")
                results.append({"Business Name": company, "Error": str(e)})

    finally:
        try:
            driver.quit()
        except:
            pass
        if user_data_dir and "temp_profiles" in user_data_dir and os.path.exists(user_data_dir):
            shutil.rmtree(user_data_dir, ignore_errors=True)
            logging.debug(f"🧹 Cleaned profile: {user_data_dir}")

    return results

def process_company(row):
    results = []
    user_data_dir = None
    try:
        driver = get_chrome_driver(headless=False)
        user_data_dir = driver.capabilities.get("goog:chromeOptions", {}).get("args", [None])[0]
        login_to_linkedin(driver, USERNAME, PASSWORD)

        company = row.get("Company", "UNKNOWN")
        result = scrape_linkedin(
            driver,
            company,
            expected_city=row.get("City"),
            expected_state=row.get("State"),
            expected_website=row.get("Website")
        )
        result["Business Name"] = company
        logging.info(f"✅ API scraped: {company}")
        return result

    except Exception as e:
        logging.error(f"❌ API scrape failed for {row.get('Company')}: {e}")
        return {"Business Name": row.get("Company", "UNKNOWN"), "Error": str(e)}

    finally:
        try:
            driver.quit()
        except:
            pass
        if user_data_dir and "temp_profiles" in user_data_dir and os.path.exists(user_data_dir):
            shutil.rmtree(user_data_dir, ignore_errors=True)
            logging.debug(f"🧹 API cleaned profile: {user_data_dir}")

def main():
    if not os.path.exists(CSV_INPUT):
        logging.error(f"CSV file not found: {CSV_INPUT}")
        return

    df = read_csv(CSV_INPUT)
    if df.empty or "Company" not in df.columns:
        logging.error("CSV is empty or missing 'Company' column.")
        return

    all_results = []
    
    # Shuffle the data slightly to avoid predictable patterns
    if len(df) > BATCH_SIZE * 2:
        df = df.sample(frac=1, random_state=random.randint(1, 100))
        
    batches = [df[i:i+BATCH_SIZE] for i in range(0, len(df), BATCH_SIZE)]

    for idx, batch_rows in enumerate(tqdm(batches, desc="📦 All Batches")):
        logging.info(f"🚀 Starting batch {idx + 1}/{len(batches)}")
        batch_results = run_batch(batch_rows)
        all_results.extend(batch_results)

        # Save results more frequently
        if (len(all_results) % 5 == 0) or (idx == len(batches) - 1):
            pd.DataFrame(all_results).to_csv(CSV_OUTPUT, index=False)
            logging.info(f"💾 Partial save: {len(all_results)} rows → {CSV_OUTPUT}")

        # Wait longer between batches to avoid detection
        if idx < len(batches) - 1:
            humanize_wait(*WAIT_BETWEEN_BATCHES, "Waiting between batches")

    logging.info(f"✅ Finished scraping. Final results saved to {CSV_OUTPUT}")

if __name__ == "__main__":
    main()