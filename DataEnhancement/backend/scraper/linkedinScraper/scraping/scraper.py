import os
import time
import logging
import random
import re
from urllib.parse import urlparse
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from .utils import extract_domain, get_name_parts
from .navigation import search_company_links, select_company_link
from .companyDetails import extract_company_details
from ..utils.chromeUtils import DEBUG_FOLDER
from ..utils.locationUtils import city_names_match
from .login import login_to_linkedin


def slugify_company_name(name):
    return re.sub(r'[^a-z0-9-]', '', name.lower().replace(" ", "-"))


def is_login_form(driver):
    """
    Detects if the current page displays a LinkedIn login form.
    """
    try:
        driver.find_element(By.ID, "username")
        driver.find_element(By.ID, "password")
        return True
    except NoSuchElementException:
        return False


def detect_page_type(driver):
    """
    Classify current page as 'signup', 'login', 'about', or 'other'.
    """
    url = driver.current_url
    path = urlparse(url).path.lower()
    if path.startswith("/signup"):
        return "signup"
    if path.startswith("/login") or is_login_form(driver):
        return "login"
    if "/company/" in path and "/about" in path:
        return "about"
    return "other"


def wait_for_page_load(driver, timeout=3):
    """
    Wait until document.readyState == 'complete', then short jitter.
    """
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
    except:
        logging.debug("Page load wait timed out, proceeding anyway.")
    time.sleep(random.uniform(0.5, 1.0))

def scrape_linkedin(driver, business_name, expected_city=None, expected_state=None, expected_website=None):
    """
    Sequential LinkedIn scraper with explicit waits and dynamic throttling.
    Returns company details or delegates to fallback.
    """
    try:
        logging.info(f"🔍 Scraping LinkedIn for {business_name}")

        slug = slugify_company_name(business_name)
        about_url = f"https://www.linkedin.com/company/{slug}/about/"
        expected_domain = extract_domain(expected_website) if expected_website else None

        # 1) Go to About
        driver.get(about_url)

        # 1a) If LinkedIn redirects to /company/unavailable, bail to fallback
        parsed = urlparse(driver.current_url)
        if parsed.path.startswith("/company/unavailable"):
            logging.info("⚠️ Company page unavailable, using fallback.")
            return _fallback_scrape(driver, business_name, expected_city, expected_state, expected_domain)

        # 1b) If we’re already on the About page, skip any waits and scrape immediately
        if detect_page_type(driver) == "about":
            logging.info("✅ Landed on About directly, extracting details now.")
            details = extract_company_details(driver, about_url, business_name, fast=True)
            core = ["Company Website", "Company Size", "Headquarters", "Industry", "Founded"]
            if all(details.get(k) in (None, "", "Not found") for k in core):
                logging.info("⚠️ Missing core fields on direct About, fallback.")
                return _fallback_scrape(driver, business_name, expected_city, expected_state, expected_domain)
            domain_match = extract_domain(details.get("Company Website") or "")
            return {
            "Business Name": business_name,
            "LinkedIn Link": about_url,
            **details,
            "Location Match": "Direct",
            "Domain Match": (
                "Matched" if expected_domain and domain_match == expected_domain else "Mismatch"
            )
        }

        # 2) Otherwise wait and go through the usual signup/login/fallback flow
        wait_for_page_load(driver)
        page = detect_page_type(driver)

        if page in ["signup", "login"]:
            logging.info(f"🔐 Detected {page} page. Attempting automatic login...")
            success = login_to_linkedin(driver, USERNAME, PASSWORD)
            if not success:
                logging.warning("❌ Auto-login failed. Aborting.")
                return {"Business Name": business_name, "Error": "Auto-login failed"}

            # Retry About page after login
            driver.get(about_url)
            wait_for_page_load(driver)
            parsed = urlparse(driver.current_url)

            if parsed.path.startswith("/company/unavailable"):
                logging.info("⚠️ Company page unavailable after login, using fallback.")
                return _fallback_scrape(driver, business_name, expected_city, expected_state, expected_domain)

            page = detect_page_type(driver)


        if page != "about":
            logging.warning(f"🚫 Landed on {page}, using fallback.")
            return _fallback_scrape(driver, business_name, expected_city, expected_state, expected_domain)

        # 3) Now extract (after login flow)
        details = extract_company_details(driver, about_url, business_name)
        core = ["Company Website", "Company Size", "Headquarters", "Industry", "Founded"]
        if all(details.get(k) in (None, "", "Not found") for k in core):
            logging.info("⚠️ Missing core fields, fallback.")
            return _fallback_scrape(driver, business_name, expected_city, expected_state, expected_domain)
        domain_match = extract_domain(details.get("Company Website") or "")
        return {
            "Business Name": business_name,
            "LinkedIn Link": about_url,
            **details,
            "Location Match": "Direct",
            "Domain Match": (
                "Matched" if expected_domain and domain_match == expected_domain else "Mismatch"
            )
        }

    except Exception as e:
        logging.error(f"Error scraping {business_name}: {e}", exc_info=True)
        return {"Business Name": business_name, "Error": str(e)}


def _fallback_scrape(driver, business_name, expected_city, expected_state, expected_domain):
    """
    Fallback via LinkedIn search: on each shortened query, pick the very first result immediately.
    """
    driver.implicitly_wait(1)
    try:
        tokens = business_name.split()
        for i in range(len(tokens) - 1, 0, -1):
            query = " ".join(tokens[:i])
            url = (
                "https://www.linkedin.com/search/results/companies/"
                f"?keywords={query.replace(' ', '%20')}"
            )
            logging.info(f"🔎 Fallback search for '{query}'")
            driver.get(url)

            # wait up to 5s for first company-link
            try:
                first_link = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((
                        By.XPATH,
                        "//div[contains(@class,'search-results')]//a[contains(@href,'/company/')]"
                    ))
                )
            except TimeoutException:
                logging.debug(f"No results for '{query}' within 5s")
                continue

            href = first_link.get_attribute("href")
            if not href:
                logging.debug(f"First link missing href for '{query}'")
                continue

            # ← insert random pause here!
            pause = random.uniform(1.5, 3.0)
            logging.debug(f"⏱️ Pausing {pause:.2f}s before navigating to About")
            time.sleep(pause)

            # go to its About page
            about_page = href.rstrip("/") + "/about/"
            logging.info(f"→ Navigating to first result: {about_page}")
            driver.get(about_page)
            wait_for_page_load(driver)

            details = extract_company_details(driver, driver.current_url, business_name)
            domain = extract_domain(details.get("Company Website") or "")

            return {
            "Business Name": business_name,
            "LinkedIn Link": driver.current_url,
            **details,
            "Location Match": f"Fallback({query})",
            "Domain Match": (
                "Matched" if expected_domain and domain == expected_domain else "Mismatch"
            )
        }

        logging.error(f"🛑 Fallback exhausted for {business_name}")
        return _empty_result(f"No results for {business_name}")

    except Exception as e:
        logging.error(f"Fallback error for {business_name}: {e}", exc_info=True)
        return {"Business Name": business_name, "Error": str(e)}

    finally:
        driver.implicitly_wait(10)


def has_no_results(driver):
    try:
        return bool(driver.find_elements(
            By.XPATH, "//h2[contains(@class,'artdeco-empty-state__headline')]"
        ))
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
        "Domain Match": "N/A"
    }