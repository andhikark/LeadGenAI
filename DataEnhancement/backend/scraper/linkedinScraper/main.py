import os
import logging
import random
import re
import time
from urllib.parse import urlparse

import pandas as pd
from dotenv import load_dotenv
from tqdm import tqdm

from .utils.chromeUtils import get_chrome_driver, CHROME_INFO_FILE
from .scraping.scraper import scrape_linkedin
from .utils.fileUtils import read_csv

# -----------------------------------------------------------------------------
# Logging / I/O helpers
# -----------------------------------------------------------------------------

def _init_logging() -> None:
    os.makedirs("log", exist_ok=True)
    i = 1
    while os.path.exists(f"log/log_{i}.log"):
        i += 1
    logging.basicConfig(
        filename=f"log/log_{i}.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

def _next_output_path(base: str) -> str:
    i = 1
    while os.path.exists(f"{base}{i}.csv"):
        i += 1
    return f"{base}{i}.csv"


# -----------------------------------------------------------------------------
# Batch runner
# -----------------------------------------------------------------------------


def run_batch(
    batch_df: pd.DataFrame,
    batch_index: int,
    total_batches: int,
    global_progress: list[dict],
    global_bar,
    output_path: str | None,
    li_at: str
) -> list[dict]:
    results: list[dict] = []
    driver = None

    try:
        driver = get_chrome_driver(li_at=li_at, headless=True)
        driver.get("https://www.linkedin.com/feed")
        if "login" in driver.current_url.lower():
            logging.error(":x: Cookie login failed; aborting batch.")
            return results
        logging.info(":white_check_mark: Authenticated; scraping %d companies", len(batch_df))

        with tqdm(total=len(batch_df), desc=f"Batch {batch_index+1}/{total_batches}", position=1, leave=False) as batch_bar:
            for _, row in batch_df.iterrows():
                company = row.get("Company", "UNKNOWN")
                logging.info(f":mag: Scraping company: {company}")
                slug = re.sub(r"[^a-z0-9-]", "", company.lower().replace(" ", "-"))
                about_url = f"https://www.linkedin.com/company/{slug}/about/"

                driver.get(about_url)
                time.sleep(random.uniform(1.5, 2.5))

                path = urlparse(driver.current_url).path.lower()
                if path.startswith(("/login", "/signup")):
                    logging.error(":no_entry_sign: Redirected to %s during %s, cookie expired; aborting batch", path, company)
                    results.append({"Business Name": company, "Error": f"Redirected to {path}"})
                    break

                try:
                    result = scrape_linkedin(
                        driver,
                        company,
                        expected_city=row.get("City"),
                        expected_state=row.get("State"),
                        expected_website=row.get("Website")
                    )
                    result["Business Name"] = company
                    results.append(result)
                    logging.info(":white_check_mark: Scraped: %s", company)
                except Exception as exc:
                    logging.error(":x: Error scraping %s: %s", company, exc, exc_info=True)
                    error_result = {"Business Name": company, "Error": str(exc)}
                    results.append(error_result)

                main_h = driver.current_window_handle
                for h in driver.window_handles:
                    if h != main_h:
                        driver.switch_to.window(h)
                        driver.close()
                driver.switch_to.window(main_h)

                delay = random.uniform(5, 10)
                logging.debug(":clock3: Sleeping %.2f seconds before next company...", delay)
                time.sleep(delay)

                if "Error" in results[-1] and "429" in results[-1]["Error"]:
                    sleep_min = random.uniform(3, 4)
                    logging.warning(":warning: 429 detected; sleeping %.1f min", sleep_min)
                    time.sleep(sleep_min * 60)

                global_bar.update(1)
                batch_bar.update(1)

                # Save CSV every 5 rows scraped
                if output_path and len(results) % 5 == 0:
                    pd.DataFrame(results).to_csv(output_path, index=False)
                    logging.info(":floppy_disk: Auto-saved %d rows → %s", len(results), output_path)

    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                logging.debug(":octagonal_sign: Driver quit raised during cleanup.")

    return results


# -----------------------------------------------------------------------------
# CLI entry point
# -----------------------------------------------------------------------------

def main() -> None:
    _init_logging()
    load_dotenv()

    global CSV_OUTPUT
    CSV_INPUT = "input/sample_data1.csv"
    CSV_OUTPUT_BASE = "output/linkedin_scraped_results"
    BATCH_SIZE = 5
    WAIT_BETWEEN_BATCHES = (10, 20)

    # Ensure output directory exists
    os.makedirs("output", exist_ok=True)

    if CHROME_INFO_FILE.exists():
        CHROME_INFO_FILE.unlink()

    if not os.path.exists(CSV_INPUT):
        logging.error("CSV file not found: %s", CSV_INPUT)
        return

    df = read_csv(CSV_INPUT)
    if df.empty or "Company" not in df.columns:
        logging.error("CSV missing required 'Company' column or is empty")
        return

    CSV_OUTPUT = _next_output_path(CSV_OUTPUT_BASE)
    all_results: list[dict] = []

    batches = [df[i: i + BATCH_SIZE] for i in range(0, len(df), BATCH_SIZE)]
    total_batches = len(batches)
    total_rows = len(df)

    with tqdm(total=total_rows, desc="📦 Rows Scraped", position=0) as global_bar:
        for idx, batch_df in enumerate(batches):
            logging.info("🚀 Starting batch %d/%d", idx + 1, total_batches)
            batch_results = run_batch(batch_df, idx, total_batches, all_results, global_bar, CSV_OUTPUT)
            all_results.extend(batch_results)

            if idx < total_batches - 1:
                sleep_s = random.uniform(*WAIT_BETWEEN_BATCHES)
                logging.info("⏱️ Waiting %.1f s before next batch", sleep_s)
                time.sleep(sleep_s)

    pd.DataFrame(all_results).to_csv(CSV_OUTPUT, index=False)
    logging.info("✅ Finished scraping; final results → %s", CSV_OUTPUT)


if __name__ == "__main__":
    main()
