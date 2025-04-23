import os
import logging
import pandas as pd
import nodriver as uc
from backend.scraper.linkedinScraper.companyDetails import extract_company_details
from backend.scraper.linkedinScraper.util import generate_proxy_url, human_delay
from backend.scraper.linkedinScraper.monkeyPatch import *  # Monkey-patch headless
from nodriver import cdp

# Ensure output directory exists
os.makedirs("output", exist_ok=True)

async def run_batch_scraper(csv_path, session_path):
    df = pd.read_csv(csv_path)
    total_rows = len(df)

    BATCH_SIZE = 10
    SAVE_EVERY = 5
    results = []

    for batch_start in range(0, total_rows, BATCH_SIZE):
        batch_df = df.iloc[batch_start:batch_start + BATCH_SIZE]
        logging.info(f"🚀 Starting new batch from row {batch_start} to {batch_start + len(batch_df) - 1}")

        browser = await uc.start(
            headless=False,
            no_sandbox=True,
            user_data_dir=os.getenv("USER_DATA_DIR", "/tmp/.linkedin_profile"),
            browser_executable_path=os.getenv("CHROME_BIN", "/usr/bin/google-chrome"),
        )

        await browser.cookies.load(session_path)
        logging.info("✅ Cookies loaded")

        page = await browser.get("https://www.linkedin.com", new_tab=True)
        resp, *_ = await page.send(cdp.runtime.evaluate(expression="document.title"))
        title = resp.value
        logging.info(f"📄 Page title: {title}")

        if "Log In" in title:
            logging.warning("⚠️ Cookie invalid. Redirected to login.")
            return

        for i, row in batch_df.iterrows():
            company_name = row["Company"]
            slug = company_name.lower().replace(" ", "-")
            company_url = f"https://www.linkedin.com/company/{slug}/about/"

            try:
                result = await extract_company_details(page, company_url, company_name)
                results.append(result)
            except Exception as e:
                logging.warning(f"❌ Failed to scrape {company_name}: {e}")
                continue

            if len(results) % SAVE_EVERY == 0:
                pd.DataFrame(results).to_csv("output/results.csv", index=False)
                logging.info(f"💾 Auto-saved {len(results)} rows.")

            human_delay(1.5, 2.5)

        await page.close()
        logging.info("🧹 Page closed for this batch.")

    pd.DataFrame(results).to_csv("output/results.csv", index=False)
    logging.info("✅ Final save completed.")
