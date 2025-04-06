import sys
import time
import random
import pandas as pd
import os
import asyncio
import re
# import yfinance as yf
import platform
import subprocess
import matplotlib.pyplot as plt
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
import ollama
from config.browser_config import PlaywrightManager

class AsyncCompanyScraper:
    def __init__(self):
        self.df = pd.DataFrame(columns=[
            'Overview', 'Product Services'
        ])
        self.sources = ["Overview", "Products & Services"]
        self.google_search = "https://www.bing.com/search?q="
        self.manager = PlaywrightManager(headless=True)

        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    async def fetch_page_text(self, page, url, tags_to_find):
        try:
            await page.goto(url)
            await page.wait_for_load_state("domcontentloaded")

            texts = []
            for tag in tags_to_find:
                elements = await page.query_selector_all(tag)
                texts.extend([await element.inner_text() for element in elements])

            return "\n".join(texts)
        except Exception as e:
            return f"Error loading page: {e}"

    async def process_company(self, company_name):
        urls = [
            f'https://www.bing.com/search?q={company_name}+Company+Overview',
            f'https://www.bing.com/search?q={company_name}+Company+Products+Services',
        ]

        async with async_playwright() as p:
            # browser = await p.chromium.launch(headless=True)
            # context = await browser.new_context()
            # page = await context.new_page()
            page = await self.manager.start_browser()

            tasks = [self.fetch_page_text(page, url, ['p', 'h1', 'h2', 'h3']) for url in urls]
            texts = await asyncio.gather(*tasks)  # 🔥 Menunggu semua selesai

            print(f"Total texts extracted: {len(texts)}")  # Debugging

            # Menghindari IndexError
            overview_text = texts[0] if len(texts) > 0 else "No overview data"
            services_text = texts[1] if len(texts) > 1 else "No services data"

            prompts = [
                f"Re-explain about {company_name} using this info: {overview_text}. Explain in about 250 words.",
                f"Re-expplain about the products & services of {company_name} using this info: {services_text}. Explain in about 250 words.",
            ]

            # answers = await asyncio.gather(*[self.ask_ollama(prompt) for prompt in prompts])
            answers = await asyncio.gather(*[
                asyncio.to_thread(lambda prompt=prompt:
                                  ollama.chat(model='phi', messages=[{'role': 'user', 'content': prompt}])['message'][
                                      'content'])
                for prompt in prompts
            ])

            await self.manager.stop_browser()

        return {
            "Overview": answers[0] if len(answers) > 0 else "Not Found",
            "Products & Services": answers[1] if len(answers) > 1 else "Not Found",
        }

    async def save(self, df, folder='../data'):
        os.makedirs(folder, exist_ok=True)
        df = pd.DataFrame([df])
        # df.to_csv(os.path.join(folder, 'overview & products/services.csv'), index=False)
        # df.to_excel(os.path.join(folder, 'overview & products/services.xlsx'), index=False)
        
        # # Make sure the folder exists
        # os.makedirs(folder, exist_ok=True)
    
        # Set file paths
        csv_path = os.path.join(folder, 'overview_and_products_services.csv')
        excel_path = os.path.join(folder, 'overview_and_products_services.xlsx')
    
        if os.path.exists(csv_path):
            data = pd.read_csv(csv_path)
            data = pd.concat([data, df], axis=0).reset_index(drop=True)
            data.to_csv(csv_path, index=False)
            data.to_excel(excel_path, index=False)
        else:
            df.to_csv(csv_path, index=False)
            df.to_excel(excel_path, index=False)
        
if __name__ == "__main__":
    scraper = AsyncCompanyScraper()
    result = asyncio.run(scraper.process_company("Yamada"))
    asyncio.run(scraper.save(result))
    print(result)