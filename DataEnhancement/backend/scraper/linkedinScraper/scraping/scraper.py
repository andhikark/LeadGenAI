import os
import time
import logging
import random
import re
from selenium.webdriver.common.by import By
from .utils import extract_domain, get_name_parts
from .navigation import search_company_links, select_company_link
from .companyDetails import extract_company_details
from .location import validate_location
from ..utils.chromeUtils import DEBUG_FOLDER
from .login import login_to_linkedin
from ..utils.locationUtils import city_names_match


def slugify_company_name(name):
    return re.sub(r'[^a-z0-9-]', '', name.lower().replace(" ", "-"))


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
        driver.get(about_url)
        time.sleep(random.uniform(1.5, 2.5))

        # Login if needed
        if "login" in driver.current_url or "uas/login" in driver.current_url:
            logging.info("🔐 Detected login page. Attempting login.")
            if not login_to_linkedin(driver, os.getenv("LINKEDIN_USERNAME"), os.getenv("LINKEDIN_PASSWORD")):
                logging.warning("Login failed, using fallback.")
                return _fallback_scrape(driver, business_name, expected_city, expected_state, expected_domain)
            driver.get(about_url)
            time.sleep(random.uniform(1.5, 2.5))

        # Unavailable page
        if "linkedin.com/company/unavailable" in driver.current_url:
            logging.warning("Company unavailable, using fallback.")
            return _fallback_scrape(driver, business_name, expected_city, expected_state, expected_domain)

        # Extract details
        details = extract_company_details(driver, about_url, business_name)

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
            driver.get(search_url)
            time.sleep(random.uniform(1.5, 2.5))

            if has_no_results(driver):
                logging.debug(f"No results for '{query}'")
                continue

            links = search_company_links(driver, query)
            if not links:
                continue

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

            # Visit the /about page
            driver.get(url.rstrip("/") + "/about")
            time.sleep(random.uniform(1.5, 2.5))

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
