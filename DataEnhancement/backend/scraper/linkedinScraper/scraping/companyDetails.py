import logging
import time
import re
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from .utils import extract_domain
from .jsonParser import extract_industry_from_json_data
from .human import human_delay, human_scroll

def extract_company_details(driver, company_url, business_name, fast=False):
    """
    Scrape company details from the LinkedIn About page.
    If fast=True, minimize waits and scrolling.
    """
    logging.info(f"Navigating to company URL: {company_url}")
    driver.get(company_url)

    # If not in fast mode, give the page a chance to load and redirect to /about/
    if not fast:
        human_delay(2, 1)

    # Ensure we're on the About subpage
    if '/about/' not in driver.current_url:
        about_url = company_url.rstrip('/') + '/about/'
        logging.info(f"Redirecting to about page: {about_url}")
        driver.get(about_url)
        if not fast:
            human_delay(2, 1)

    # Trigger dynamic content with scroll
    human_scroll(driver, steps=2 if fast else 4, max_offset=500 if fast else 900)
    human_delay(0.3, 0.5)

    # Dump HTML + screenshot for debugging
    timestamp = int(time.time())
    html = driver.page_source
    try:
        driver.save_screenshot(f"output/about_debug_{timestamp}.png")
        with open(f"output/about_source_{timestamp}.html", "w", encoding="utf-8") as f:
            f.write(html)
    except Exception as e:
        logging.warning(f"Failed to save debug output: {e}")

    soup = BeautifulSoup(html, 'html.parser')

    # Initialize fields
    company_website = "Not found"
    employees = "Not found"
    associated_members = "Not found"
    industry = "Not found"
    headquarters = "Not found"
    hq_city = "Not found"
    hq_state = "Not found"
    founded = "Not found"
    specialties = "Not found"

    # --- Fallback: try parsing from JSON-LD ---
    extracted_industry = extract_industry_from_json_data(html)
    if extracted_industry:
        industry = extracted_industry

    try:
        for dt in soup.find_all("dt"):
            label = dt.get_text(strip=True).lower()
            dds = dt.find_next_siblings("dd", limit=2)
            if not dds:
                continue

            value = dds[0].get_text(strip=True)

            if "website" in label and value.startswith("http"):
                company_website = value
            elif "company size" in label:
                employees = value.replace(" employees", "").strip()
                if len(dds) > 1:
                    span = dds[1].find("span")
                    if span:
                        associated_text = span.get_text(strip=True)
                        match = re.search(r"\d+", associated_text)
                        if match:
                            associated_members = match.group()
            elif "founded" in label:
                founded = value
            elif "specialties" in label:
                specialties = value
            elif "industry" in label:
                industry = value

        # Headquarters parsing
        hq_block = soup.select_one("div.org-location-card p")
        if hq_block:
            full_hq = hq_block.get_text(strip=True)
            headquarters = full_hq
            parts = [p.strip() for p in full_hq.split(",")]
            if len(parts) >= 2:
                hq_city, hq_state = parts[0], parts[1]
            elif len(parts) == 1:
                hq_city = parts[0]

    except Exception as e:
        logging.warning(f"❗ Error parsing with BeautifulSoup: {e}")

    logging.info(
        f"[Parsed] HQ: {headquarters} | Employees: {employees} | Members: {associated_members} | Website: {company_website} | Industry: {industry}"
    )

    return {
        "Company Website": company_website,
        "Employees": employees,
        "Associated Members": associated_members,
        "Industry": industry,
        "Headquarters": headquarters,
        "HQ City": hq_city,
        "HQ State": hq_state,
        "Founded": founded,
        "Specialties": specialties,
    }