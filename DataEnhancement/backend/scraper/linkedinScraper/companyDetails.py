import logging
import time
import re
from bs4 import BeautifulSoup
# from .utils import extract_domain
# from .jsonParser import extract_industry_from_json_data
from .human import human_delay

async def extract_company_details(page, company_url, business_name, fast=False):
    """
    Scrape company details from the LinkedIn About page using Nodriver.
    If fast=True, minimize waits and scrolling.
    """
    logging.info(f"Navigating to company URL: {company_url}")
    await page.get(company_url)


    # Redirect to /about/ page if needed
    if '/about/' not in page.url:
        about_url = company_url.rstrip('/') + '/about/'
        logging.info(f"Redirecting to about page: {about_url}")
        await page.get(about_url)

    # Wait and mimic human scroll to trigger dynamic content
    if not fast:
        human_delay(2, 1)

    await page.scroll_down(500 if fast else 900)  # ✅ valid
    human_delay(0.3, 0.5)

    # Get page HTML
    html = await page.get_content()
    timestamp = int(time.time())
    # Optionally dump HTML or screenshot
    # with open(f"output/about_source_{timestamp}.html", "w", encoding="utf-8") as f:
    #     f.write(html)

    soup = BeautifulSoup(html, 'html.parser')

    # Default values
    company_website = "Not found"
    employees = "Not found"
    associated_members = "Not found"
    industry = "Not found"
    headquarters = "Not found"
    hq_city = "Not found"
    hq_state = "Not found"
    founded = "Not found"
    specialties = "Not found"

    # # JSON fallback
    # extracted_industry = extract_industry_from_json_data(html)
    # if extracted_industry:
    #     industry = extracted_industry

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
                        match = re.search(r"[\d,]+", associated_text)
                        if match:
                            associated_members = match.group().replace(",", "")
            elif "founded" in label:
                founded = value
            elif "specialties" in label:
                specialties = value
            elif "industry" in label:
                industry = value
            elif "headquarters" in label:
                headquarters = value
                parts = [p.strip() for p in value.split(",")]
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
