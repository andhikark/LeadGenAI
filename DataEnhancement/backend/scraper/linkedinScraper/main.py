import os
import shutil
import logging
import pandas as pd
import random
import time
from dotenv import load_dotenv
from tqdm import tqdm
from .utils.chromeUtils import get_chrome_driver, save_chrome_info
from .scraping.login import login_to_linkedin
from .scraping.scraper import scrape_linkedin
from .utils.fileUtils import read_csv
from .utils.proxyUtils import generate_smartproxy_url

# === Environment and Configs ===
load_dotenv()
CSV_INPUT = "input/sample_data1.csv"
CSV_OUTPUT_BASE = "output/linkedin_scraped_results"
USERNAME = os.getenv("LINKEDIN_USERNAME") or "leadgenraf2@gmail.com"
PASSWORD = os.getenv("LINKEDIN_PASSWORD") or "123Testing90."
BATCH_SIZE = 10
WAIT_BETWEEN_BATCHES = (10, 20)
CLIENT_ID = "client01"  # Replace with dynamic ID in multi-user setup

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


def get_next_output_filename(base):
    i = 3
    while os.path.exists(f"{base}{i}.csv"):
        i += 1
    return f"{base}{i}.csv"

CSV_OUTPUT = get_next_output_filename(CSV_OUTPUT_BASE)


def run_batches(df, client_id):
    results = []
    total_batches = (len(df) + BATCH_SIZE - 1) // BATCH_SIZE

    for batch_index, i in enumerate(range(0, len(df), BATCH_SIZE)):
        batch = df.iloc[i:i + BATCH_SIZE]
        logging.info(f"🚀 Starting batch {batch_index + 1}/{total_batches}")

        proxy_url = generate_smartproxy_url(client_id=f"{client_id}_batch{batch_index+1}")
        driver = get_chrome_driver(
            headless=False,
            proxy_url=proxy_url
        )

        # Save unique profile info for debug/tracking (optional)
        save_chrome_info(port=9222 + batch_index, user_data_dir=f"profile_{client_id}_batch{batch_index+1}")

        user_data_dir = driver.capabilities.get("goog:chromeOptions", {}).get("args", [None])[0]

        try:
            if not login_to_linkedin(driver, USERNAME, PASSWORD):
                logging.error("❌ Login failed. Skipping batch.")
                continue

            for _, row in tqdm(batch.iterrows(), total=len(batch), desc=f"🔄 Batch {batch_index + 1}/{total_batches}", leave=False, position=1):
                company = row.get("Company", "UNKNOWN")
                try:
                    result = scrape_linkedin(
                        driver,
                        company,
                        expected_city=row.get("City"),
                        expected_state=row.get("State"),
                        expected_website=row.get("Website"),
                        logged_in=True
                    )
                    result["Business Name"] = company
                    results.append(result)
                    logging.info(f"✅ Scraped: {company}")
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

        if batch_index < total_batches - 1:
            sleep_time = random.uniform(*WAIT_BETWEEN_BATCHES)
            logging.info(f"⏱️ Waiting {sleep_time:.2f}s before next batch")
            time.sleep(sleep_time)

    return results


def main():
    if not os.path.exists(CSV_INPUT):
        logging.error(f"CSV file not found: {CSV_INPUT}")
        return

    df = read_csv(CSV_INPUT)
    if df.empty or "Company" not in df.columns:
        logging.error("CSV is empty or missing 'Company' column.")
        return

    all_results = run_batches(df, client_id=CLIENT_ID)

    if all_results:
        df_results = pd.DataFrame(all_results)

        if "Business Name" in df_results.columns:
            cols = ["Business Name"] + [col for col in df_results.columns if col != "Business Name"]
            df_results = df_results[cols]

        df_results.to_csv(CSV_OUTPUT, index=False)
        logging.info(f"💾 Final save: {len(all_results)} rows → {CSV_OUTPUT}")

    logging.info("✅ Finished scraping.")


if __name__ == "__main__":
    main()