from backend.scraper.linkedinScraper.scraper import run_batch_scraper
import asyncio

if __name__ == "__main__":
    uc.loop().run_until_complete(run_batch_scraper("input/companies.csv"))
