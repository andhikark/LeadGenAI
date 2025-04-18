import logging
from linkedinScraper.utils.urlUtils import extract_domain
from linkedinScraper.scraping.navigation import search_company_links, select_company_link
from linkedinScraper.scraping.location import validate_location
from linkedinScraper.scraping.companyDetails import extract_company_details

logger = logging.getLogger(__name__)

def scrape_linkedin(driver, business_name, expected_city=None, expected_state=None, expected_website=None):
    logger.info(f"🔍 Starting LinkedIn scrape for: {business_name}")

    # Step 1: Normalize expected domain (if any)
    expected_domain = extract_domain(expected_website) if expected_website else None

    # Step 2: Search for company links
    links = search_company_links(driver, business_name)
    if not links:
        logger.warning(f"❌ No search results found for: {business_name}")
        return {
            "LinkedIn Link": None,
            "Company Website": None,
            "Company Size": None,
            "Industry": None,
            "Headquarters": None,
            "Founded": None,
            "Specialties": None,
            "Location Match": "No results",
            "Domain Match": "Not applicable"
        }

    # Step 3: Validate location (city/state)
    selected_link, location_status = validate_location(driver, links, expected_city, expected_state)
    linkedin_url = selected_link.get_attribute("href")
    logger.info(f"✅ Selected company link: {linkedin_url} (Location: {location_status})")

    # Step 4: Navigate to company profile page
    select_company_link(driver, selected_link)

    # Step 5: Extract detailed info from About page
    details = extract_company_details(driver, linkedin_url, business_name)

    # Step 6: Validate domain match (if expected)
    domain_match_status = "Not applicable"
    if expected_domain and details["Company Website"] != "Not found":
        actual_domain = extract_domain(details["Company Website"])
        domain_match_status = (
            "Domain matched" if actual_domain == expected_domain else "Domain mismatch"
        )
        logger.info(f"🌐 Domain comparison: expected={expected_domain}, actual={actual_domain} → {domain_match_status}")

    # Final structured output
    return {
        "LinkedIn Link": linkedin_url,
        **details,
        "Location Match": location_status,
        "Domain Match": domain_match_status
    }
