# backend/linkedinScraper/scraping/companyDetails.py

import logging
import time
import random
import os
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from .utils import extract_domain
from .jsonParser import extract_industry_from_json_data

os.makedirs("output", exist_ok=True)

def extract_company_details(driver, company_url, business_name):
    logging.info(f"Navigating to company URL: {company_url}")
    driver.get(company_url)
    time.sleep(2 + random.random())

    if '/about/' not in driver.current_url:
        about_url = company_url.rstrip('/') + '/about/'
        logging.info(f"Redirecting to about page: {about_url}")
        driver.get(about_url)
        time.sleep(2 + random.random())

    # Scroll to ensure dynamic content loads
    for _ in range(3):
        driver.execute_script("window.scrollBy(0, 600)")
        time.sleep(0.5 + 0.5 * random.random())

    # Dump HTML + screenshot for debugging
    timestamp = int(time.time())
    html = driver.page_source
    driver.save_screenshot(f"output/about_debug_{timestamp}.png")
    with open(f"output/about_source_{timestamp}.html", "w", encoding="utf-8") as f:
        f.write(html)

    soup = BeautifulSoup(html, 'html.parser')

    # Initialize fields
    company_website = "Not found"
    company_size = "Not found"
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
        # Generic dt/dd pairs
        dts = soup.find_all("dt")
        for dt in dts:
            label = dt.get_text(strip=True).lower()
            dd = dt.find_next_sibling("dd")
            if not dd:
                continue
            value = dd.get_text(strip=True)

            if "website" in label and value.startswith("http"):
                company_website = value
            elif "company size" in label:
                company_size = value
            elif "founded" in label:
                founded = value
            elif "specialties" in label:
                specialties = value
            elif "industry" in label:
                industry = value

        # Headquarters from location card
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

    logging.info(f"[Parsed] HQ: {headquarters} | Website: {company_website} | Size: {company_size} | Industry: {industry}")

    return {
        "Company Website": company_website,
        "Company Size": company_size,
        "Industry": industry,
        "Headquarters": headquarters,
        "HQ City": hq_city,
        "HQ State": hq_state,
        "Founded": founded,
        "Specialties": specialties
    }