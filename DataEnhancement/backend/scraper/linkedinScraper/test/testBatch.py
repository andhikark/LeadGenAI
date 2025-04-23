import os
import pandas as pd
import logging
from dotenv import load_dotenv
from pathlib import Path
import nodriver as uc

# ✅ Import monkey patch BEFORE any uc.start()
from backend.scraper.linkedinScraper.monkeyPatch import *

from backend.scraper.linkedinScraper.scraper import run_batch_scraper
from backend.scraper.linkedinScraper.utils.chromeUtils import CHROME_INFO_FILE

def write_test_csv(temp_csv_path):
    """Creates a temporary test CSV with dummy company data."""
    test_data = [
        {"Company": "OpenAI"},
        {"Company": "Google"},
    ]
    df = pd.DataFrame(test_data)
    df.to_csv(temp_csv_path, index=False)
    return temp_csv_path

async def main():
    # Load environment variables
    load_dotenv()

    # Cookie/session path
    session_path = "linkedin_headless_session.dat"
    if not os.path.exists(session_path):
        print(f"❌ Session file not found: {session_path}")
        return

    # Clean up any previous Chrome debug info
    if CHROME_INFO_FILE.exists():
        CHROME_INFO_FILE.unlink()

    # Prepare input test data
    input_dir = "input"
    os.makedirs(input_dir, exist_ok=True)
    csv_path = write_test_csv(os.path.join(input_dir, "test_companies.csv"))

    print("🚀 Running test batch...")
    await run_batch_scraper(csv_path, session_path)
    print("\n✅ Scraping complete. Check output/results.csv")

if __name__ == "__main__":
    uc.loop().run_until_complete(main())
