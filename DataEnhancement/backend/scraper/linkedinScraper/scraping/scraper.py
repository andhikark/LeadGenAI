import os
import time
import logging
import random
import re
from urllib.parse import urlparse
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .utils import extract_domain
from .navigation import search_company_links, select_company_link
from .companyDetails import extract_company_details
from .login import login_to_linkedin
from ..utils.chromeUtils import get_chrome_driver
from ..utils.proxyUtils import generate_smartproxy_url
from dotenv import load_dotenv

load_dotenv()
USERNAME = os.getenv("LINKEDIN_USERNAME") or "leadgenraf2@gmail.com"
PASSWORD = os.getenv("LINKEDIN_PASSWORD") or "123Testing90."

def slugify_company_name(name):
    return re.sub(r'[^a-z0-9-]', '', name.lower().replace(" ", "-"))

def is_login_form(driver):
    try:
        driver.find_element(By.ID, "username")
        driver.find_element(By.ID, "password")
        return True
    except NoSuchElementException:
        return False

def detect_page_type(driver):
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
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
    except:
        logging.debug("Page load wait timed out.")
    time.sleep(random.uniform(0.5, 1.0))

def scrape_linkedin(driver, business_name, expected_city=None, expected_state=None, expected_website=None, logged_in=False):
    try:
        if not logged_in:
            logging.info("🔐 Attempting login...")
            if not login_to_linkedin(driver, USERNAME, PASSWORD):
                return {"Business Name": business_name, "Error": "Login failed"}
            logged_in = True

        logging.info(f"🔍 Scraping LinkedIn for {business_name}")
        slug = slugify_company_name(business_name)
        about_url = f"https://www.linkedin.com/company/{slug}/about/"
        expected_domain = extract_domain(expected_website) if expected_website else None

        driver.get(about_url)
        parsed = urlparse(driver.current_url)
        if parsed.path.startswith("/company/unavailable"):
            logging.info("⚠️ Company page unavailable, using fallback.")
            return _fallback_scrape(driver, business_name, expected_city, expected_state, expected_domain)

        if detect_page_type(driver) == "about":
            logging.info("✅ Landed on About directly.")
            details = extract_company_details(driver, about_url, business_name, fast=True)
            if _missing_core(details):
                logging.info("⚠️ Missing details, fallback triggered.")
                return _fallback_scrape(driver, business_name, expected_city, expected_state, expected_domain)
            return _build_result(details, business_name, about_url, expected_domain)

        logging.warning(f"🚫 Unexpected page ({driver.current_url}), using fallback.")
        return _fallback_scrape(driver, business_name, expected_city, expected_state, expected_domain)

    except Exception as e:
        logging.error(f"Unhandled scrape error for {business_name}: {e}", exc_info=True)
        return {"Business Name": business_name, "Error": str(e)}

def _fallback_scrape(driver, business_name, expected_city, expected_state, expected_domain):
    driver.implicitly_wait(1)
    try:
        tokens = business_name.split()
        for i in range(len(tokens) - 1, 0, -1):
            query = " ".join(tokens[:i])
            search_url = f"https://www.linkedin.com/search/results/companies/?keywords={query.replace(' ', '%20')}"
            logging.info(f"🔍 Fallback search for '{query}'")
            driver.get(search_url)

            try:
                first_link = WebDriverWait(driver, 5).until(EC.presence_of_element_located(
                    (By.XPATH, "//div[contains(@class,'search-results')]//a[contains(@href,'/company/')]")))
            except TimeoutException:
                continue

            href = first_link.get_attribute("href")
            if not href:
                continue

            time.sleep(random.uniform(1.5, 3.0))
            driver.get(href.rstrip("/") + "/about/")
            wait_for_page_load(driver)

            details = extract_company_details(driver, driver.current_url, business_name)
            return _build_result(details, business_name, driver.current_url, expected_domain, query)

        logging.error("❌ Fallback exhausted.")
        return _empty_result("No results")

    except Exception as e:
        logging.error(f"Fallback failed for {business_name}: {e}", exc_info=True)
        return {"Business Name": business_name, "Error": str(e)}
    finally:
        driver.implicitly_wait(10)

def _missing_core(details):
    core = ["Company Website", "Company Size", "Headquarters", "Industry", "Founded"]
    return all(details.get(k) in (None, "", "Not found") for k in core)

def _build_result(details, business_name, url, expected_domain, fallback_query=None):
    domain = extract_domain(details.get("Company Website") or "")
    result = {
        "Business Name": business_name,
        "LinkedIn Link": url,
        **details,
        "Location Match": f"Fallback({fallback_query})" if fallback_query else "Direct",
        "Domain Match": "Matched" if expected_domain and domain == expected_domain else "Mismatch"
    }
    return result

def _empty_result(reason):
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