import time
import random
import logging
from selenium.webdriver.common.by import By

def search_company_links(driver, business_name):
    """Searches LinkedIn for company results and returns matching links."""
    formatted_name = business_name.replace(" ", "%20")
    search_url = f"https://www.linkedin.com/search/results/companies/?keywords={formatted_name}"

    logging.info(f"🔎 Navigating to LinkedIn company search: {search_url}")
    driver.get(search_url)
    time.sleep(random.uniform(1.5, 2.5))  # ⏱️ Shorter and randomized wait

    selectors = [
        "//a[contains(@class, 'app-aware-link') and contains(@href, '/company/')]",
        "//div[contains(@class, 'search-results')]//*[contains(@href, '/company/')]",
        "//ul[contains(@class, 'reusable-search__entity-result-list')]/li//a[contains(@href, '/company/')]",
        "//span[contains(@class, 'entity-result__title')]//a[contains(@href, '/company/')]"
    ]

    for selector in selectors:
        try:
            logging.debug(f"🔍 Trying selector: {selector}")
            links = driver.find_elements(By.XPATH, selector)
            if links:
                logging.info(f"✅ Found {len(links)} company links using selector: {selector}")
                return links
        except Exception as e:
            logging.warning(f"⚠️ Selector {selector} failed: {e}")

    logging.warning(f"❌ No company links found for business name: {business_name}")
    return []

def select_company_link(driver, link):
    """Attempts to click the company link using different strategies."""
    try:
        logging.debug("🖱️ Attempting direct click...")
        link.click()
    except Exception as e:
        logging.warning(f"⚠️ Direct click failed: {e}")
        try:
            logging.debug("💡 Attempting JavaScript click...")
            driver.execute_script("arguments[0].click();", link)
        except Exception as e2:
            logging.warning(f"⚠️ JavaScript click failed: {e2}")
            href = link.get_attribute("href")
            if href:
                logging.info(f"➡️ Falling back to direct navigation: {href}")
                driver.get(href)
    time.sleep(random.uniform(1.2, 2.0))  # ⏱️ Shorter post-click delay