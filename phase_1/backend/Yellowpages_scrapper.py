from playwright.sync_api import sync_playwright
import time
import random
import csv
import os

def setup_browser(playwright):
    """Set up and return a configured Playwright browser instance."""
    # Random user agent
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:97.0) Gecko/20100101 Firefox/97.0',
    ]
    
    # Launch browser with specific options
    browser = playwright.chromium.launch(
        headless=True,  # Set to False for debugging
        args=[
            '--no-sandbox',
            '--disable-dev-shm-usage',
            f'--user-agent={random.choice(user_agents)}',
        ]
    )
    
    # Create a context with specific options
    context = browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent=random.choice(user_agents),
        has_touch=False,
        java_script_enabled=True,
        locale='en-US',
        timezone_id='America/New_York',
        # Bypass WebDriver detection
        bypass_csp=True,
    )
    
    # Emulate a real browser by setting specific properties
    page = context.new_page()
    page.add_init_script("""
    Object.defineProperty(navigator, 'webdriver', {
        get: () => false
    });
    """)
    
    return browser, context, page

def scrape_yellowpages_playwright(search_term, location, max_pages=1):
    """
    Scrapes Yellow Pages using Playwright.
    
    Args:
        search_term (str): The type of business to search for
        location (str): City, state, or zip code
        max_pages (int): Maximum number of pages to scrape
    
    Returns:
        list: List of dictionaries containing business information
    """
    businesses = []
    
    with sync_playwright() as playwright:
        browser, context, page = setup_browser(playwright)
        
        try:
            for page_num in range(1, max_pages + 1):
                
                url = f"https://www.yellowpages.com/search?search_terms={search_term}&geo_location_terms={location}"
                if page_num > 1:
                    url += f"&page={page_num}"
                
                print(f"Accessing page {page_num}: {url}")
                
                # Navigate to the page with a timeout
                page.goto(url, wait_until='domcontentloaded', timeout=60000)
                
                # Add random wait time to simulate human behavior
                wait_time = random.uniform(3, 7)
                print(f"Waiting {wait_time:.2f} seconds for page to load...")
                time.sleep(wait_time)
                
                
                try:
                    page.wait_for_selector('.result', timeout=15000)
                except Exception as e:
                    print(f"Could not find business listings with .result: {e}")
                    
                    # Take screenshot for debugging
                    page.screenshot(path=f"debug_page_{page_num}.png")
                    print(f"Saved screenshot to debug_page_{page_num}.png")
                    
                    # Save page content for debugging
                    with open(f"debug_source_{page_num}.html", "w", encoding="utf-8") as f:
                        f.write(page.content())
                    print(f"Saved page source to debug_source_{page_num}.html")
                    
                    # Try alternative selectors
                    try:
                        page.wait_for_selector('.info', timeout=5000)
                        print("Found listings with .info selector instead")
                    except:
                        print("Could not find alternative listing elements.")
                        continue
                
                # Parse all business listings
                listings = page.query_selector_all('.result')
                if not listings:
                    listings = page.query_selector_all('.info')
                
                if not listings:
                    print(f"No business listings found on page {page_num}.")
                    continue
                    
                print(f"Found {len(listings)} business listings on page {page_num}.")
                
                for listing in listings:
                    business_info = {}
                    
                    # Extract business name
                    try:
                        name_element = listing.query_selector('.business-name')
                        if name_element:
                            business_info['name'] = name_element.inner_text().strip()
                        else:
                            name_element = listing.query_selector('h2')
                            business_info['name'] = name_element.inner_text().strip() if name_element else "N/A"
                    except:
                        business_info['name'] = "N/A"
                    
                    # Extract industry/category
                    try:
                        category_element = listing.query_selector('.categories')
                        business_info['industry'] = category_element.inner_text().strip() if category_element else "N/A"
                    except:
                        business_info['industry'] = "N/A"
                    
                    # Extract address
                    address_parts = []
                    try:
                        address_element = listing.query_selector('.street-address')
                        if address_element:
                            address_parts.append(address_element.inner_text().strip())
                    except:
                        pass
                    
                    try:
                        locality_element = listing.query_selector('.locality')
                        if locality_element:
                            address_parts.append(locality_element.inner_text().strip())
                    except:
                        pass
                    
                    business_info['address'] = ", ".join(address_parts) if address_parts else "N/A"
                    
                    # Extract phone number
                    try:
                        phone_element = listing.query_selector('.phones')
                        business_info['phone'] = phone_element.inner_text().strip() if phone_element else "N/A"
                    except:
                        business_info['phone'] = "N/A"
                    
                    # Extract website
                    try:
                        website_element = listing.query_selector('.track-visit-website')
                        business_info['website'] = website_element.get_attribute('href') if website_element else "N/A"
                    except:
                        business_info['website'] = "N/A"
                    
                    businesses.append(business_info)
                    print(f"Added business: {business_info['name']}")
                
                # Random delay between pages
                if page_num < max_pages:
                    delay = random.uniform(5, 10)
                    print(f"Waiting {delay:.2f} seconds before loading next page...")
                    time.sleep(delay)
        
        except Exception as e:
            print(f"Error during scraping: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Close the browser
            browser.close()
        
        return businesses

def save_to_csv(businesses, filename='yellowpages_data.csv'):
    """Saves the scraped business data to a CSV file."""
    if not businesses:
        print("No data to save.")
        return
        
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['name', 'industry', 'address', 'phone', 'website']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for business in businesses:
            writer.writerow(business)
    
    print(f"Data saved to {filename}")

def main():
    # Example usage
    search_term = input("Enter business type to search for (e.g., 'restaurants'): ")
    location = input("Enter location (city, state, or zip code): ")
    max_pages = int(input("Enter maximum number of pages to scrape (recommended: 1-5): "))
    
    print(f"\nScraping Yellow Pages for {search_term} in {location}...")
    businesses = scrape_yellowpages_playwright(search_term, location, max_pages)
    
    if businesses:
        print(f"\nFound {len(businesses)} businesses.")
        save_to_csv(businesses)
    else:
        print("No businesses found.")

if __name__ == "__main__":
    main()