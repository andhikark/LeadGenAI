import os
import time
import logging
import random
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from .utils import extract_domain, get_name_parts
from .navigation import search_company_links, select_company_link
from .companyDetails import extract_company_details
from .location import validate_location
# from ..utils.chromeUtils import DEBUG_FOLDER
from .login import login_to_linkedin, random_scrolling
from ..utils.locationUtils import city_names_match

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)

def slugify_company_name(name):
    return re.sub(r'[^a-z0-9-]', '', name.lower().replace(" ", "-"))


def human_interaction(driver):
    """Adds random human-like interactions with the page"""
    # Random chance to perform different human actions
    action_type = random.choices(
        ["scroll", "mouse_move", "pause", "none"],
        weights=[0.4, 0.3, 0.2, 0.1]
    )[0]
    
    if action_type == "scroll":
        # Random scrolling behavior
        scroll_amount = random.randint(100, 600)
        scroll_direction = random.choice([1, -1])
        driver.execute_script(f"window.scrollBy(0, {scroll_amount * scroll_direction})")
        time.sleep(random.uniform(0.7, 2.0))
        
    elif action_type == "mouse_move":
        # Random mouse movements
        actions = ActionChains(driver)
        elements = driver.find_elements(By.TAG_NAME, "a")
        if elements:
            # Move to random element
            random_element = random.choice(elements)
            try:
                actions.move_to_element(random_element)
                actions.perform()
                time.sleep(random.uniform(0.3, 1.0))
            except:
                pass
                
    elif action_type == "pause":
        # Just pause like a human would when reading
        time.sleep(random.uniform(1.5, 4.0))


def load_page_naturally(driver, url):
    """Loads a page with natural human-like behavior"""
    driver.get(url)
    
    # Wait a natural amount of time for page to load
    time.sleep(random.uniform(2.0, 3.5))
    
    # Sometimes scroll down slightly as if reading
    if random.random() < 0.7:
        driver.execute_script(f"window.scrollBy(0, {random.randint(100, 300)})")
        time.sleep(random.uniform(0.5, 1.5))
    
    # Return to slightly random position
    if random.random() < 0.3:
        driver.execute_script(f"window.scrollBy(0, {random.randint(-100, -50)})")
    
    # Add a slight pause as if the user is looking at the content
    time.sleep(random.uniform(1.0, 2.5))


from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

def scrape_linkedin(driver, business_name, expected_city=None, expected_state=None, expected_website=None):
    try:
        logging.info(f"🔍 Starting scrape for: {business_name}")
        expected_domain = extract_domain(expected_website) if expected_website else None

        # Step 1: Go to feed
        driver.get("https://www.linkedin.com/feed")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='Search']"))
        )
        time.sleep(random.uniform(2.0, 3.0))

        # Step 2: Type business name into search bar
        search_box = driver.find_element(By.CSS_SELECTOR, "input[placeholder='Search']")
        search_box.click()
        time.sleep(random.uniform(0.3, 0.8))
        for char in business_name:
            search_box.send_keys(char)
            time.sleep(random.uniform(0.1, 0.25))
        search_box.send_keys(Keys.RETURN)

        # Step 3: Click "Companies" tab
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Companies')]"))
        ).click()
        time.sleep(random.uniform(2.5, 3.5))

        # Step 4: Click the first result
        try:
            top_result = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/company/')]"))
            )
            time.sleep(random.uniform(0.5, 1.0))
            top_result.click()
            time.sleep(random.uniform(2.5, 4.0))
        except Exception as e:
            logging.warning(f"❌ Failed to click company search result: {e}")
            return _fallback_scrape(driver, business_name, expected_city, expected_state, expected_domain)

        # Step 5: Go to /about page if not already there
        if "/about" not in driver.current_url:
            try:
                about_link = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/about')]"))
                )
                driver.get(about_link.get_attribute("href"))
                time.sleep(random.uniform(2.0, 3.0))
            except:
                logging.warning("❌ Could not find /about page")
                return _fallback_scrape(driver, business_name, expected_city, expected_state, expected_domain)

        # Check for unavailable page
        if "linkedin.com/company/unavailable" in driver.current_url:
            logging.warning("🚫 Unavailable page. Returning to /feed and retrying fallback.")
            driver.get("https://www.linkedin.com/feed")
            time.sleep(random.uniform(2.0, 3.5))
            fallback_name = " ".join(business_name.split()[:-1])
            return _fallback_scrape(driver, fallback_name, expected_city, expected_state, expected_domain)

        # Step 6: Extract data
        details = extract_company_details(driver, driver.current_url, business_name)
        human_interaction(driver)

        core_vals = [details.get(k) for k in (
            "Company Website", "Company Size", "Headquarters", "Industry", "Founded"
        )]
        if all(val in (None, "", "Not found") for val in core_vals):
            logging.info("⚠️ Incomplete /about data. Triggering fallback.")
            return _fallback_scrape(driver, business_name, expected_city, expected_state, expected_domain)

        domain_match = extract_domain(details.get("Company Website") or "")
        return {
            "LinkedIn Link": driver.current_url,
            **details,
            "Location Match": "Direct search",
            "Domain Match": "Domain matched" if expected_domain and domain_match == expected_domain else "Domain mismatch"
        }

    except Exception as e:
        logging.error(f"🔥 Unexpected scrape error for {business_name}: {e}", exc_info=True)
        return {"Business Name": business_name, "Error": str(e)}




def _fallback_scrape(driver, business_name, expected_city, expected_state, expected_domain):
    try:
        name_tokens = business_name.split()
        for i in range(len(name_tokens) - 1, 0, -1):
            query = " ".join(name_tokens[:i])

            driver.get("https://www.linkedin.com/feed")
            time.sleep(random.uniform(2.0, 3.0))
            human_interaction(driver)

            try:
                search_box = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='Search']"))
                )
                search_box.click()
                time.sleep(random.uniform(0.7, 1.3))
                search_box.clear()
                for char in query:
                    search_box.send_keys(char)
                    time.sleep(random.uniform(0.1, 0.2))
                search_box.send_keys(Keys.RETURN)
                time.sleep(random.uniform(2.5, 4.0))
                human_interaction(driver)
            except Exception as e:
                logging.warning(f"Fallback search failed: {e}")
                continue

            try:
                companies_tab = WebDriverWait(driver, 8).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Companies')]"))
                )
                companies_tab.click()
                time.sleep(random.uniform(2.0, 3.0))
            except:
                logging.warning("Companies tab not found, continuing without it")

            links = search_company_links(driver, query)
            if not links:
                logging.debug(f"No links found for fallback query: {query}")
                continue

            for link in links:
                try:
                    url = link.get_attribute("href")
                    if not url:
                        continue

                    logging.info(f"🧭 Fallback visiting: {url}")
                    load_page_naturally(driver, url.rstrip("/") + "/about")
                    random_scrolling(driver)

                    details = extract_company_details(driver, driver.current_url, business_name)
                    domain_match = extract_domain(details.get("Company Website") or "")

                    return {
                        "LinkedIn Link": driver.current_url,
                        **details,
                        "Location Match": f"Fallback ({query})",
                        "Domain Match": ("Domain matched" if expected_domain and domain_match == expected_domain else "Domain mismatch")
                    }
                except Exception as e:
                    logging.warning(f"Fallback scrape failed for one result: {e}")
                    continue

        logging.error(f"Fallback exhausted for {business_name}")
        return _empty_result(f"No results after fallback for {business_name}")

    except Exception as e:
        logging.error(f"Fallback error for {business_name}: {e}", exc_info=True)
        return {"Business Name": business_name, "Error": str(e)}



def has_no_results(driver):
    try:
        if driver.find_elements(By.XPATH, "//h2[contains(@class, 'artdeco-empty-state__headline')]"):
            return True
        return False
    except Exception:
        return False


def _empty_result(reason="No results"):
    return {
        "LinkedIn Link": None,
        "Company Website": None,
        "Company Size": None,
        "Industry": None,
        "Headquarters": None,
        "HQ City": None,
        "HQ State": None,
        "Founded": None,
        "Specialties": None,
        "Location Match": reason,
        "Domain Match": "Not applicable"
    }
