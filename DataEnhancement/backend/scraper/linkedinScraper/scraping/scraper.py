import logging
import random
import re
import time
from urllib.parse import urlparse

from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .utils import extract_domain
from .companyDetails import extract_company_details

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def slugify_company_name(name: str) -> str:
    """Return a LinkedIn‑friendly slug for a company name."""
    return re.sub(r"[^a-z0-9-]", "", name.lower().replace(" ", "-"))


def _wait_for_dom_complete(driver, timeout: int = 4) -> None:
    """Block until document.readyState == 'complete'."""
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
    except Exception:
        logging.debug("readyState wait timed out, proceeding anyway")


# -----------------------------------------------------------------------------
# Public entry point (driver is expected to be authenticated already)
# -----------------------------------------------------------------------------

def scrape_linkedin(
    driver,
    business_name: str,
    expected_city: str | None = None,
    expected_state: str | None = None,
    expected_website: str | None = None,
):
    """Return a dict with company details. If the About page is missing core fields,
    fall back to a search‑based scrape.
    """
    logging.info(f"🔍 Scraping LinkedIn for {business_name}")

    slug = slugify_company_name(business_name)
    about_url = f"https://www.linkedin.com/company/{slug}/about/"
    expected_domain = extract_domain(expected_website) if expected_website else None

    # Navigate to /about/ only if we're not already there (run_batch might have done it).
    if "/about/" not in driver.current_url:
        driver.get(about_url)
        _wait_for_dom_complete(driver)

    # If LinkedIn claims the page is unavailable, fall back.
    if urlparse(driver.current_url).path.startswith("/company/unavailable"):
        logging.info("⚠️ Company page unavailable, using fallback search")
        return _fallback_scrape(driver, business_name, expected_city, expected_state, expected_domain)

    # Extract details
    details = extract_company_details(driver, driver.current_url, business_name, fast=True)
    core_keys = [
        "Company Website",
        "Company Size",
        "Headquarters",
        "Industry",
        "Founded",
    ]
    if all(details.get(k) in (None, "", "Not found") for k in core_keys):
        logging.info("⚠️ Core fields missing, invoking fallback search")
        return _fallback_scrape(driver, business_name, expected_city, expected_state, expected_domain)

    domain_match = extract_domain(details.get("Company Website") or "")
    return {
        "Business Name": business_name,
        "LinkedIn Link": driver.current_url,
        **details,
        "Location Match": "Direct",
        "Domain Match": "Matched" if expected_domain and domain_match == expected_domain else "Mismatch",
    }


# -----------------------------------------------------------------------------
# Fallback search flow (keyword search → first result → /about/)
# -----------------------------------------------------------------------------

def _fallback_scrape(driver, business_name, expected_city, expected_state, expected_domain):
    """Keyword‑search LinkedIn and scrape the first company result's About page."""
    tokens = business_name.split()
    for i in range(len(tokens) - 1, 0, -1):
        query = " ".join(tokens[:i])
        search_url = (
            "https://www.linkedin.com/search/results/companies/" f"?keywords={query.replace(' ', '%20')}"
        )
        logging.info(f"🔎 Fallback search for '{query}'")
        driver.get(search_url)

        try:
            first_link = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//div[contains(@class,'search-results')]//a[contains(@href,'/company/')][1]",
                    )
                )
            )
        except TimeoutException:
            logging.debug(f"No results for '{query}' within 5 s; trying shorter query")
            continue

        href = first_link.get_attribute("href")
        if not href:
            continue

        time.sleep(random.uniform(1.5, 3.0))
        about_page = href.rstrip("/") + "/about/"
        logging.info(f"→ Navigating to fallback result: {about_page}")
        driver.get(about_page)
        _wait_for_dom_complete(driver)

        details = extract_company_details(driver, driver.current_url, business_name)
        domain = extract_domain(details.get("Company Website") or "")

        return {
            "Business Name": business_name,
            "LinkedIn Link": driver.current_url,
            **details,
            "Location Match": f"Fallback({query})",
            "Domain Match": "Matched" if expected_domain and domain == expected_domain else "Mismatch",
        }

    logging.error(f"🛑 Fallback exhausted for {business_name}")
    return _empty_result("No results")


# -----------------------------------------------------------------------------
# Utility
# -----------------------------------------------------------------------------

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
        "Domain Match": "N/A",
    }
