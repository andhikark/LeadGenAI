# test_growjo_search.py

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

def setup_browser(headless=False):
    edge_options = Options()
    if headless:
        edge_options.add_argument("--headless")
    edge_options.add_argument("--no-sandbox")
    edge_options.add_argument("--disable-dev-shm-usage")
    edge_options.add_argument("--disable-gpu")
    edge_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Edge(options=edge_options)
    driver.maximize_window()
    return driver

def test_search_and_scrape_full_list(company_name):
    driver = None
    try:
        driver = setup_browser(headless=False)
        wait = WebDriverWait(driver, 15)

        print("[DEBUG] Navigating to Growjo homepage...")
        driver.get("https://growjo.com/")
        time.sleep(2)

        # Locate the search bar
        search_box = None
        search_methods = [
            (By.XPATH, "//input[contains(@placeholder, 'Search')]"),
            (By.XPATH, "//input[@type='search']"),
            (By.CSS_SELECTOR, "input.search-input, input.form-control, input.search")
        ]
        for by, selector in search_methods:
            try:
                search_box = driver.find_element(by, selector)
                break
            except:
                continue

        if not search_box:
            print("[ERROR] Search box not found.")
            return

        print("[DEBUG] Typing into search bar...")
        search_box.clear()
        search_box.send_keys(company_name)
        search_box.send_keys(Keys.RETURN)

        time.sleep(2)

        # 🛠️ Wait more smartly
        try:
            print("[DEBUG] Waiting for at least one company row to load...")
            wait.until(EC.presence_of_element_located(
                (By.XPATH, "//table//tbody//tr")
            ))
            print("[DEBUG] Company table and rows loaded ✅")
        except TimeoutException:
            print("[ERROR] Company rows not found ❌")
            return

        # Scrape company links under full list
        company_links = driver.find_elements(
            By.XPATH, "//table//tbody//a[starts-with(@href, '/company/')]"
        )

        print(f"[DEBUG] Total company links found: {len(company_links)}\n")
        for idx, link in enumerate(company_links, 1):
            link_text = link.text.strip()
            link_href = link.get_attribute("href")
            print(f"{idx}. {link_text} -> {link_href}")

            if idx >= 10:
                break

    except Exception as e:
        print(f"[ERROR] Test failed: {str(e)}")
    finally:
        if driver:
            time.sleep(5)
            driver.quit()

if __name__ == "__main__":
    test_search_and_scrape_full_list("Dermatologist Medical Group of North County")
