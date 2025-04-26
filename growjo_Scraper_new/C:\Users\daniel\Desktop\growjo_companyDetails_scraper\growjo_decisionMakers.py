import time
import argparse
import pandas as pd
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import csv

GROWJO_SEARCH_URL = "https://growjo.com/"

class GrowjoCompanyDetailsScraper:
    def __init__(self, headless=False):
        self.setup_browser(headless)
        self.wait = WebDriverWait(self.driver, 10)

    def setup_browser(self, headless):
        edge_options = Options()
        if headless:
            edge_options.add_argument("--headless")
        edge_options.add_argument("--no-sandbox")
        edge_options.add_argument("--disable-dev-shm-usage")
        edge_options.add_argument("--disable-gpu")
        edge_options.add_argument("--window-size=1920,1080")
        self.driver = webdriver.Edge(options=edge_options)
        self.driver.maximize_window()

    def search_company(self, company_name):
        try:
            print(f"\n[DEBUG] Searching for company: '{company_name}'")
            self.driver.get(GROWJO_SEARCH_URL)
            time.sleep(3)
            try:
                print("[DEBUG] Trying search box by placeholder XPATH...")
                search_box = self.wait.until(EC.presence_of_element_located((By.XPATH, "//input[contains(@placeholder, 'Search')]")))
            except TimeoutException:
                try:
                    print("[DEBUG] Trying search box by type='search' XPATH...")
                    search_box = self.wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='search']")))
                except TimeoutException:
                    print("[DEBUG] Trying search box by CSS selectors...")
                    search_box = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input.search-input, input.form-control, input.search")))
            search_box.clear()
            search_box.send_keys(company_name)
            search_box.send_keys(Keys.RETURN)
            print("[DEBUG] Submitted search, waiting for results...")
            time.sleep(5)
            try:
                print("[DEBUG] Looking for exact match link...")
                company_link = self.wait.until(EC.presence_of_element_located((By.XPATH, f"//a[contains(text(), '{company_name}')]")))
                print(f"[DEBUG] Found exact match link: {company_link.text}")
            except TimeoutException:
                try:
                    print("[DEBUG] Looking for case-insensitive match link...")
                    company_link = self.wait.until(EC.presence_of_element_located((By.XPATH, f"//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{company_name.lower()}')]")))
                    print(f"[DEBUG] Found case-insensitive match link: {company_link.text}")
                except TimeoutException:
                    print("[DEBUG] Looking for company links with href starting with '/company/'...")
                    company_links = self.driver.find_elements(By.XPATH, "//a[starts-with(@href, '/company/')]")
                    print(f"[DEBUG] Found {len(company_links)} <a> links with href starting with '/company/'.")
                    # Try to match the beginning of the company name (case-insensitive, ignoring ellipsis)
                    company_name_lower = company_name.lower()
                    matched_link = None
                    for idx, link in enumerate(company_links):
                        link_text = link.text.strip().replace('...', '').lower()
                        print(f"[DEBUG] Link {idx}: '{link.text}' (href: {link.get_attribute('href')})")
                        if link_text and company_name_lower.startswith(link_text):
                            matched_link = link
                            print(f"[DEBUG] Matched link: '{link.text}'")
                            break
                    if matched_link:
                        company_link = matched_link
                        print(f"[DEBUG] Using matched company link: {company_link.text}")
                    elif company_links:
                        company_link = company_links[0]
                        print(f"[DEBUG] No strong match, using first company link: {company_link.text}")
                    else:
                        print(f"[DEBUG] No company links found for '{company_name}'.")
                        # Save the HTML for debugging
                        with open("debug_search_results.html", "w", encoding="utf-8") as f:
                            f.write(self.driver.page_source)
                        print("[DEBUG] Saved search results HTML to debug_search_results.html")
                        return False
            print(f"[DEBUG] Clicking company link: {company_link.text}")
            company_link.click()
            time.sleep(5)
            return True
        except Exception as e:
            print(f"[ERROR] Error searching for company '{company_name}': {str(e)}")
            return False

    def extract_company_details(self, company_name):
        details = {"company": company_name, "city": "", "state": "", "industry": "", "website": "", "employees": "", "revenue": "", "specialties": ""}
        try:
            # City
            try:
                city_elem = self.driver.find_element(By.XPATH, "//a[contains(@href, '/city/')]")
                details["city"] = city_elem.text.strip()
            except:
                pass
            # State
            try:
                state_elem = self.driver.find_element(By.XPATH, "//a[contains(@href, '/state/')]")
                details["state"] = state_elem.text.strip()
            except:
                pass
            # Industry
            try:
                industry_elem = self.driver.find_element(By.XPATH, "//a[contains(@href, '/industry/')]")
                details["industry"] = industry_elem.text.strip()
            except:
                pass
            # Website
            try:
                website_elem = self.driver.find_element(By.XPATH, "//a[contains(@target, '_blank') and contains(@href, '//') and img]")
                details["website"] = website_elem.get_attribute("href").replace("//", "https://") if website_elem.get_attribute("href").startswith("//") else website_elem.get_attribute("href")
            except:
                pass
            # Revenue (est)
            try:
                emp_elem = self.driver.find_elements(By.XPATH, "//p[contains(@style, 'font-size: 18px') and contains(@style, 'font-weight: bold')]")
                if emp_elem:
                    details["revenue"] = emp_elem[0].text.strip()
                if len(emp_elem) > 1:
                    details["employees"] = emp_elem[1].text.strip()
            except:
                pass
            # Keywords
            try:
                keywords_elem = self.driver.find_element(By.XPATH, "//strong[contains(text(), 'keywords:')]")
                parent = keywords_elem.find_element(By.XPATH, "..")
                parent_text = parent.text
                if 'keywords:' in parent_text:
                    specialties = parent_text.split('keywords:', 1)[1].strip()
                    details["specialties"] = specialties
                else:
                    details["specialties"] = ''
            except:
                details["specialties"] = ''
        except Exception as e:
            print(f"Error extracting details for {company_name}: {str(e)}")
        return details

    def scrape_company(self, company_name):
        if self.search_company(company_name):
            time.sleep(3)
            return self.extract_company_details(company_name)
        else:
            print(f"Company not found: {company_name}")
            return {"company": company_name, "city": "not found", "state": "not found", "industry": "not found", "website": "not found", "employees": "not found", "revenue": "not found", "specialties": "not found"}

    def close(self):
        if hasattr(self, 'driver'):
            self.driver.quit()

def main():
    parser = argparse.ArgumentParser(description="Scrape company details from Growjo.com")
    parser.add_argument("--input", "-i", required=True, help="Input CSV file with company names (column: company)")
    parser.add_argument("--output", "-o", required=True, help="Output CSV file for results")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    args = parser.parse_args()

    try:
        companies_df = pd.read_csv(args.input)
        if "company" not in companies_df.columns:
            raise ValueError("Input CSV must contain a 'company' column")
    except Exception as e:
        print(f"Error reading input file: {str(e)}")
        return

    scraper = GrowjoCompanyDetailsScraper(headless=args.headless)
    all_details = []
    try:
        for company in tqdm(companies_df["company"], desc="Scraping companies"):
            details = scraper.scrape_company(company)
            all_details.append(details)
            pd.DataFrame(all_details).to_csv(args.output, index=False, quoting=csv.QUOTE_ALL)
            time.sleep(2)
        print(f"Scraping complete! Results saved to {args.output}")
    except KeyboardInterrupt:
        print("Scraping interrupted by user.")
    except Exception as e:
        print(f"Error during scraping: {str(e)}")
    finally:
        scraper.close()

if __name__ == "__main__":
    main()
