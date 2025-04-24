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
from ..utils.chromeUtils import DEBUG_FOLDER
from .login import login_to_linkedin, random_scrolling
from ..utils.locationUtils import city_names_match


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


def scrape_linkedin(driver, business_name, expected_city=None, expected_state=None, expected_website=None):
    """
    Scrape the LinkedIn 'About' page or fallback to search if needed.
    Returns a dict with company details or an 'Error' key on failure.
    """
    try:
        logging.info(f"🔍 Scraping LinkedIn for {business_name}")

        # Prepare expected domain
        expected_domain = extract_domain(expected_website) if expected_website else None
        if expected_domain:
            logging.debug(f"Expected domain: {expected_domain}")

        # Direct /about URL
        slug = slugify_company_name(business_name)
        about_url = f"https://www.linkedin.com/company/{slug}/about/"
        
        # Load page with natural behavior
        load_page_naturally(driver, about_url)
        
        # Add a random human interaction
        human_interaction(driver)

        # Login if needed
        if "login" in driver.current_url or "uas/login" in driver.current_url:
            logging.info("🔐 Detected login page. Attempting login.")
            if not login_to_linkedin(driver, os.getenv("LINKEDIN_USERNAME"), os.getenv("LINKEDIN_PASSWORD")):
                logging.warning("Login failed, using fallback.")
                return _fallback_scrape(driver, business_name, expected_city, expected_state, expected_domain)
            
            # After login, reload the page
            load_page_naturally(driver, about_url)
            human_interaction(driver)

        # Unavailable page
        if "linkedin.com/company/unavailable" in driver.current_url:
            logging.warning("Company unavailable, using fallback.")
            return _fallback_scrape(driver, business_name, expected_city, expected_state, expected_domain)

        # Extract details
        details = extract_company_details(driver, about_url, business_name)
        
        # Add more human-like behavior
        human_interaction(driver)

        # Check if all core fields are empty
        core_vals = [details.get(k) for k in (
            "Company Website", "Company Size", "Headquarters", "Industry", "Founded"
        )]
        if all(val in (None, "", "Not found") for val in core_vals):
            logging.info("Incomplete /about data, using fallback.")
            return _fallback_scrape(driver, business_name, expected_city, expected_state, expected_domain)

        # Success
        domain_match = extract_domain(details.get("Company Website") or "")
        return {
            "LinkedIn Link": about_url,
            **details,
            "Location Match": "Direct link",
            "Domain Match": ("Domain matched" if expected_domain and domain_match == expected_domain else "Domain mismatch")
        }

    except Exception as e:
        logging.error(f"Unexpected scrape error for {business_name}: {e}", exc_info=True)
        return {"Business Name": business_name, "Error": str(e)}


def _fallback_scrape(driver, business_name, expected_city, expected_state, expected_domain):
    """
    Fallback scraping via LinkedIn search results.
    Handles its own exceptions and returns a dict or error.
    """
    try:
        name_tokens = business_name.split()
        for i in range(len(name_tokens) - 1, 0, -1):
            query = " ".join(name_tokens[:i])
            search_url = f"https://www.linkedin.com/search/results/companies/?keywords={query.replace(' ', '%20')}"

            logging.info(f"Fallback query: {query}")
            
            # Load search page naturally
            load_page_naturally(driver, search_url)
            
            # Add random human interaction
            human_interaction(driver)

            if has_no_results(driver):
                logging.debug(f"No results for '{query}'")
                continue

            links = search_company_links(driver, query)
            if not links:
                continue
                
            # Add random human-like pause as if looking at results
            time.sleep(random.uniform(1.5, 3.5))

            # Pick the best match by city if possible
            selected = None
            for link in links:
                try:
                    container = link
                    for _ in range(4):
                        container = container.find_element(By.XPATH, "./..")
                    snippet = container.text.lower()
                    if expected_city and city_names_match(expected_city.lower(), snippet):
                        selected = link
                        break
                except Exception:
                    continue

            # Default to first if no city match
            selected = selected or links[0]
            url = selected.get_attribute("href")
            if not url:
                continue

            # Visit the /about page with natural behavior
            load_page_naturally(driver, url.rstrip("/") + "/about")
            
            # Add random scrolling
            random_scrolling(driver)

            details = extract_company_details(driver, driver.current_url, business_name)
            website = details.get("Company Website") or ""
            domain_match = extract_domain(website)

            return {
                "LinkedIn Link": driver.current_url,
                **details,
                "Location Match": f"Fallback ({query})",
                "Domain Match": ("Domain matched" if expected_domain and domain_match == expected_domain else "Domain mismatch")
            }

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
