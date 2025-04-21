import os
import time
import argparse
import pandas as pd
from dotenv import load_dotenv
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException,StaleElementReferenceException
# Load environment variables
load_dotenv()

# Constants
GROWJO_LOGIN_URL = "https://growjo.com/login"
GROWJO_SEARCH_URL = "https://growjo.com/"
LOGIN_EMAIL = os.getenv("GROWJO_EMAIL")
LOGIN_PASSWORD = os.getenv("GROWJO_PASSWORD")

# For debugging
print(f"Email: {LOGIN_EMAIL}")
print(f"Password: {LOGIN_PASSWORD[:3]}***** (first 3 chars shown for verification)")

class GrowjoScraper:
    """A class to scrape decision makers' information from Growjo.com."""
    
    def __init__(self, headless=False):
        """Initialize the scraper with browser settings."""
        self.setup_browser(headless)
        self.wait = WebDriverWait(self.driver, 20)  # Increased timeout to 20 seconds
        self.logged_in = False
        
    def setup_browser(self, headless):
        """Set up the Edge browser with appropriate options."""
        edge_options = Options()
        if headless:
            edge_options.add_argument("--headless")
        
        # Add additional options to make Edge more stable
        edge_options.add_argument("--no-sandbox")
        edge_options.add_argument("--disable-dev-shm-usage")
        edge_options.add_argument("--disable-gpu")
        edge_options.add_argument("--window-size=1920,1080")
            
        # Using Edge WebDriver which is built into Windows 10
        self.driver = webdriver.Edge(options=edge_options)
        self.driver.maximize_window()
    
    def login(self):
        """Log in to Growjo.com with credentials from environment variables."""
        if not LOGIN_EMAIL or not LOGIN_PASSWORD:
            raise ValueError("Login credentials not found. Make sure your .env file contains GROWJO_EMAIL and GROWJO_PASSWORD.")
        
        try:
            print("Logging in to Growjo.com...")
            self.driver.get(GROWJO_LOGIN_URL)
            
            # Wait for page to load completely
            time.sleep(5)
                
            print("Page title:", self.driver.title)
            print("Current URL:", self.driver.current_url)
            
            # Using exact selectors from the login page
            form = self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))
            email_field = self.wait.until(EC.element_to_be_clickable((By.ID, "email")))
            password_field = self.wait.until(EC.element_to_be_clickable((By.ID, "password")))
            
            # Clear and enter email
            email_field.clear()
            email_field.send_keys(LOGIN_EMAIL)
            
            # Clear and enter password
            password_field.clear()
            password_field.send_keys(LOGIN_PASSWORD)
            
            # Submit the form instead of clicking the button
            print("Submitting login form...")
            form.submit()
            
            # Wait for login success
            time.sleep(5)
            
            # Check if we're redirected away from login page
            if "/login" not in self.driver.current_url:
                self.logged_in = True
                print("Login successful!")
            else:
                print("Still on login page after submitting form")
                # Try clicking the button as a fallback
                try:
                    login_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Sign In')]")
                    print("Clicking login button as fallback...")
                    login_button.click()
                    time.sleep(5)
                    
                    if "/login" not in self.driver.current_url:
                        self.logged_in = True
                        print("Login successful via button click!")
                    else:
                        # Check for error messages
                        error_elements = self.driver.find_elements(By.CSS_SELECTOR, ".error, .alert, .notification")
                        for error in error_elements:
                            print(f"Error message found: {error.text}")
                        raise Exception("Login failed: still on login page after form submit and button click")
                except Exception as e:
                    print(f"Button click fallback failed: {str(e)}")
                    raise
            
        except Exception as e:
            print(f"Login failed with exception: {str(e)}")
            
            # Try direct navigation as a last resort
            try:
                print("Attempting direct navigation to main page...")
                self.driver.get(GROWJO_SEARCH_URL)
                time.sleep(3)
                
                # Check if we're on the main page and not redirected back to login
                if "/login" not in self.driver.current_url:
                    print("Direct navigation successful!")
                    self.logged_in = True
                    return
            except:
                pass
            
            raise
    
    def search_company(self, company_name):
        """Search for a company on Growjo.com."""
        try:
            print(f"Searching for company: {company_name}")
            self.driver.get(GROWJO_SEARCH_URL)
            
            # Wait for page to load
            time.sleep(3)
            
            # Try different methods to find the search box
            try:
                # First try by placeholder
                search_box = self.wait.until(EC.presence_of_element_located((By.XPATH, "//input[contains(@placeholder, 'Search')]")))
            except TimeoutException:
                try:
                    # Try by type search
                    search_box = self.wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='search']")))
                except TimeoutException:
                    try:
                        # Try by common search class names
                        search_box = self.wait.until(EC.presence_of_element_located(
                            (By.CSS_SELECTOR, "input.search-input, input.form-control, input.search")))
                    except TimeoutException:
                        
                        # Try to find all inputs for debugging
                        inputs = self.driver.find_elements(By.TAG_NAME, "input")
                        print(f"Found {len(inputs)} input fields")
                        for i, inp in enumerate(inputs):
                            print(f"Input {i}: type={inp.get_attribute('type')}, placeholder={inp.get_attribute('placeholder')}")
                        
                        # If we still can't find the search box, raise an exception
                        raise Exception("Could not find search box on page")
            
            # Clear and enter company name
            search_box.clear()
            search_box.send_keys(company_name)
            search_box.send_keys(Keys.RETURN)
            
            # Wait for search results to load
            time.sleep(5)
            
            
            # Try different methods to find the company link
            try:
                # Exact match
                company_link = self.wait.until(EC.presence_of_element_located(
                    (By.XPATH, f"//a[contains(text(), '{company_name}')]")))
            except TimeoutException:
                try:
                    # Partial match
                    company_link = self.wait.until(EC.presence_of_element_located(
                        (By.XPATH, f"//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{company_name.lower()}')]")))
                except TimeoutException:
                    try:
                        # Try to find any search result
                        company_links = self.driver.find_elements(By.CSS_SELECTOR, ".search-result a, .company-name a, .result-item a")
                        if company_links:
                            company_link = company_links[0]  # Take the first result
                            print(f"Could not find exact match, using first result: {company_link.text}")
                        else:
                            print(f"No search results found for '{company_name}'")
                            return False
                    except:
                        print(f"Company '{company_name}' not found in search results")
                        return False
            
            # Click on the company link
            print(f"Found company: {company_link.text}")
            company_link.click()
            time.sleep(5)
                
            return True
                
        except Exception as e:
            print(f"Error searching for company: {str(e)}")
            return False
    
    def is_phone_number(self, text):
        """Check if a string is likely to be a phone number.
        
        A string is considered a phone number if:
        1. It contains only digits, spaces, and phone separators (+, -, (, ), .)
        2. It contains at least 7 digits (common minimum for phone numbers)
        """
        # Count digits in the text
        digit_count = sum(c.isdigit() for c in text)
        
        # Check if it contains only digits and common phone separators
        valid_chars = set("0123456789+- ().")
        is_valid_format = all(c in valid_chars or c.isspace() for c in text)
        
        return is_valid_format and digit_count >= 7

    def get_decision_makers(self):
        """Extract decision makers' information from the company page."""
        decision_makers = []
        
        try:
            print("Looking for decision makers table...")
            
            # Try to find the table with decision makers
            try:
                # Look for table with headers "Name", "Title", "Email/Phone"
                people_table = self.wait.until(EC.presence_of_element_located(
                    (By.XPATH, "//table[contains(@class, 'table') and .//th[contains(text(), 'Name')] and .//th[contains(text(), 'Title')] and .//th[contains(text(), 'Email/Phone')]]")))
                rows = people_table.find_elements(By.TAG_NAME, "tr")[1:]
                print("Found decision makers table!")
            except TimeoutException:
                # Try a more generic approach
                try:
                    people_table = self.wait.until(EC.presence_of_element_located(
                        (By.XPATH, "//h2[contains(text(), 'People') or contains(text(), 'Decision Maker')]/following::table[1]")))
                    print("Found table after 'People' heading")
                except TimeoutException:
                    # Try to find any table on the page
                    tables = self.driver.find_elements(By.TAG_NAME, "table")
                    if tables:
                        people_table = tables[0]  # Use the first table
                        print(f"Using first table found of {len(tables)} tables")
                    else:
                        print("No tables found on the page")
                        return []
            
            # Find all rows in the table (skip the header row)
            rows = people_table.find_elements(By.TAG_NAME, "tr")[1:]  # Skip header row
            print(f"Found {len(rows)} decision makers")
            
            # Process each row - but get a fresh reference to each row, one at a time
            for idx in range(len(rows)):
                try:
                    print(f"Processing row {idx+1}/{len(rows)}")
                    
                    # Get fresh reference to table and rows each time
                    try:
                        # Look for table with headers "Name", "Title", "Email/Phone"
                        # Wait for any previous row to go stale (optional but useful after .back())
                        if idx > 0 and 'row' in locals():
                            try:
                                self.wait.until(EC.staleness_of(row))
                            except:
                                pass

                        # Re-fetch table and rows
                        people_table = self.wait.until(EC.presence_of_element_located(
                            (By.XPATH, "//table[contains(@class, 'table') and .//th[contains(text(), 'Name')] and .//th[contains(text(), 'Title')] and .//th[contains(text(), 'Email/Phone')]]")))
                        current_rows = people_table.find_elements(By.TAG_NAME, "tr")[1:]

                        
                        # Get all rows again (skip header)
                        current_rows = people_table.find_elements(By.TAG_NAME, "tr")[1:]
                        
                        # Only proceed if we still have enough rows
                        if idx < len(current_rows):
                            row = current_rows[idx]
                        else:
                            print(f"Row {idx+1} no longer exists, skipping")
                            continue
                    except Exception as e:
                        print(f"Could not get fresh reference to table or row {idx+1}: {str(e)}")
                        continue
                    
                    # Get the columns
                    cols = row.find_elements(By.TAG_NAME, "td")
                    
                    if len(cols) >= 3:  # Name, Title, Email/Phone
                        # Extract name - look for the link within the first column
                        name_col = cols[0]
                        name = ""
                        try:
                            # Exact the number and remove it from the display
                            name_text = name_col.text.strip()
                            if name_text.startswith("#"):
                                # Remove the leading #number
                                name_text = name_text[name_text.find(" "):].strip()
                            elif name_text[0].isdigit():
                                # If it starts with a digit, find the first space
                                idx_space = name_text.find(" ")
                                if idx_space > 0:
                                    name_text = name_text[idx_space:].strip()
                            
                            # Look for name in an <a> tag
                            links = name_col.find_elements(By.TAG_NAME, "a")
                            for link in links:
                                link_text = link.text.strip()
                                if link_text and not "linkedin.com" in link.get_attribute("href").lower():
                                    name = link_text
                                    break
                            
                            # If no name found in links, use the text content
                            if not name:
                                name = name_text
                        except Exception as e:
                            print(f"Error extracting name: {str(e)}")
                            name = name_col.text.strip()
                        
                        # Extract title from second column
                        title = cols[1].text.strip()
                        
                        # Extract LinkedIn URL if available
                        linkedin_url = ""
                        try:
                            linkedin_elems = name_col.find_elements(By.XPATH, ".//a[contains(@href, 'linkedin.com')]")
                            if linkedin_elems:
                                linkedin_url = linkedin_elems[0].get_attribute("href")
                        except:
                            pass
                        
                        # Look for the "Reveal Email/Phone" button in the third column
                        contact_info = ""
                        reveal_button = None
                        try:
                            # Find reveal button
                            reveal_buttons = cols[2].find_elements(By.XPATH, 
                                ".//a[contains(text(), 'Reveal Email/Phone')] | .//button[contains(text(), 'Reveal Email/Phone')]")
                            
                            if reveal_buttons:
                                reveal_button = reveal_buttons[0]
                                print(f"Found reveal button for {name}")
                                
                                # Save the href attribute which contains the employee URL
                                employee_url = reveal_button.get_attribute("href")
                                
                                # If there's no href, construct the URL from the person's name
                                if not employee_url:
                                    # Create a URL-friendly name format
                                    name_for_url = name.replace(" ", "-").replace("/", "-")
                                    # Construct employee URL based on Growjo's URL pattern
                                    employee_url = f"https://growjo.com/employee/{name_for_url}"
                                    print(f"Constructed employee URL: {employee_url}")
                                
                                print(f"Employee URL: {employee_url}")
                                
                                # Always navigate to the employee page
                                self.driver.get(employee_url)
                                time.sleep(2)
                                
                                # Extract LinkedIn URL from the employee page - this is more accurate than from company page
                                linkedin_url = ""
                                try:
                                    linkedin_elems = self.driver.find_elements(By.XPATH, 
                                        "//a[contains(@href, 'linkedin.com')]")
                                    if linkedin_elems:
                                        linkedin_url = linkedin_elems[0].get_attribute("href")
                                        print(f"Found LinkedIn URL on employee page: {linkedin_url}")
                                except Exception as e:
                                    print(f"Error extracting LinkedIn URL: {str(e)}")
                                
                                # On the employee page, find and click the "Reveal" button
                                email = ""
                                phone = ""
                                try:
                                    # Look for reveal buttons on the employee page
                                    reveal_buttons = self.driver.find_elements(By.XPATH, 
                                        "//button[contains(text(), 'Reveal')] | //a[contains(text(), 'Reveal')]")
                                    
                                    if reveal_buttons:
                                        print(f"Found {len(reveal_buttons)} reveal buttons on employee page")
                                        for btn in reveal_buttons:
                                            try:
                                                print(f"Attempting to click reveal button: {btn.text}")
                                                # Try different methods to click
                                                try:
                                                    # Try regular click first
                                                    btn.click()
                                                except:
                                                    # If that fails, try JavaScript click
                                                    self.driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                                                    self.driver.execute_script("arguments[0].click();", btn)
                                                    
                                                time.sleep(2)  # Wait for reveal
                                            except Exception as e:
                                                print(f"Failed to click reveal button: {str(e)}")
                                    
                                    # Look for revealed contact info
                                    # Email is often in elements with data attributes or specific classes
                                    try:
                                        # Target div with class="head" and "wpr" as specified by user
                                        email_elements = self.driver.find_elements(By.XPATH, 
                                            "//div[contains(@class, 'head')]//div[contains(@class, 'wpr')]//*[contains(text(), '@')] | //a[contains(@href, 'mailto:')] | //*[contains(@class, 'email')] | //*[contains(text(), '@')]")
                                        
                                        for elem in email_elements:
                                            text = elem.text.strip()
                                            if '@' in text and '.' in text and not text.startswith('http'):
                                                email = text
                                                print(f"Found email: {email}")
                                                break
                                                
                                            href = elem.get_attribute('href')
                                            if href and 'mailto:' in href:
                                                email = href.replace('mailto:', '').strip()
                                                print(f"Found email from href: {email}")
                                                break
                                    except Exception as e:
                                        print(f"Error extracting email: {str(e)}")
                                    
                                    # Look for phone numbers - often has specific formatting
                                    try:
                                        # First check the specific path mentioned in the HTML structure:
                                        # class="info" > class="wpr" > href="/join"
                                        phone_specific_path = self.driver.find_elements(By.XPATH, 
                                            "//div[contains(@class, 'info')]//div[contains(@class, 'wpr')]//a[contains(@href, '/join')]")
                                        
                                        # Check elements in the specific path
                                        for elem in phone_specific_path:
                                            text = elem.text.strip()
                                            if text and self.is_phone_number(text):
                                                phone = text
                                                print(f"Found phone from specific path: {phone}")
                                                break
                                                
                                        # If no phone found yet, try the generic approach
                                        if not phone:
                                            # Target div with class="head" and "wpr" as specified by user
                                            phone_elements = self.driver.find_elements(By.XPATH, 
                                                "//div[contains(@class, 'head')]//div[contains(@class, 'wpr')]//*[contains(text(), '(') or contains(text(), '+') or contains(text(), '-')] | //*[contains(@class, 'phone')] | //*[contains(text(), '(') and contains(text(), ')')]")
                                            
                                            for elem in phone_elements:
                                                text = elem.text.strip()
                                                # Check if text is a phone number
                                                if self.is_phone_number(text):
                                                    phone = text
                                                    print(f"Found phone: {phone}")
                                                    break
                                                    
                                                # Also check href
                                                href = elem.get_attribute('href')
                                                if href and 'tel:' in href:
                                                    phone = href.replace('tel:', '').strip()
                                                    print(f"Found phone from href: {phone}")
                                                    break
                                                    
                                        # Check any link text that could be a phone number
                                        if not phone:
                                            all_links = self.driver.find_elements(By.TAG_NAME, "a")
                                            for link in all_links:
                                                text = link.text.strip()
                                                if text and self.is_phone_number(text):
                                                    phone = text
                                                    print(f"Found phone from link text: {phone}")
                                                    break
                                    except Exception as e:
                                        print(f"Error extracting phone: {str(e)}")
                                    
                                    # Also look for contact info in text format
                                    if not email or not phone:
                                        # Add direct extraction from div.head and div.wpr
                                        try:
                                            # Get all text from the divs with class="head" and "wpr"
                                            wpr_divs = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'head')]//div[contains(@class, 'wpr')]")
                                            
                                            for div in wpr_divs:
                                                div_text = div.text.strip()
                                                print(f"Found div.wpr content: {div_text}")
                                                
                                                # Extract email if not already found
                                                if not email:
                                                    email_lines = [line for line in div_text.split('\n') if '@' in line and '.' in line]
                                                    if email_lines:
                                                        email = email_lines[0].strip()
                                                        print(f"Found email from div.wpr: {email}")
                                                
                                                # Extract phone if not already found
                                                if not phone:
                                                    # Check each line to see if it's a phone number
                                                    for line in div_text.split('\n'):
                                                        if self.is_phone_number(line):
                                                            phone = line.strip()
                                                            print(f"Found phone from div.wpr: {phone}")
                                                            break
                                        except Exception as e:
                                            print(f"Error extracting from div.wpr: {str(e)}")
                                        
                                        # Also check original contact sections
                                        contact_sections = self.driver.find_elements(By.XPATH, 
                                            "//h2[contains(text(), 'Contact Information')]/following-sibling::div[1] | //div[contains(@class, 'contact')]")
                                        
                                        for section in contact_sections:
                                            text = section.text.strip()
                                            print(f"Contact section text: {text}")
                                            
                                            # Extract email if not already found
                                            if not email:
                                                email_match = [line for line in text.split('\n') if '@' in line and '.' in line]
                                                if email_match:
                                                    email = email_match[0].strip()
                                                    print(f"Found email from text: {email}")
                                            
                                            # Extract phone if not already found
                                            if not phone:
                                                for line in text.split('\n'):
                                                    if self.is_phone_number(line):
                                                        phone = line.strip()
                                                        print(f"Found phone from contact section: {phone}")
                                                        break
                                except Exception as e:
                                    print(f"Error revealing contact info: {str(e)}")
                                
                                # Save the complete contact info
                                contact_info = ""
                                if email:
                                    contact_info += f"Email: {email}\n"
                                if phone:
                                    contact_info += f"Phone: {phone}\n"
                                    
                                # If we still have no contact info, save any text that might be helpful
                                if not contact_info:
                                    try:
                                        contact_info = "Could not extract specific contact info. Page saved to employee HTML file."
                                    except:
                                        pass
                                    
                                # Go back to the company page
                                self.driver.back()
                                time.sleep(3)  # Increased wait time for page to load completely
                                
                            else:
                                # No reveal button, see if contact info is already visible
                                contact_info = cols[2].text.strip()
                                if contact_info == "Reveal Email/Phone":
                                    contact_info = ""
                        except Exception as e:
                            print(f"Error processing reveal button: {str(e)}")
                        
                        # Add to our list
                        decision_makers.append({
                            "name": name,
                            "title": title,
                            "contact_info": contact_info,
                            "linkedin": linkedin_url,
                            "company": "Lyten"  # This will be overwritten correctly later
                        })
                        print(f"Added decision maker: {name}, {title}")
                    
                except Exception as e:
                    print(f"Error processing row: {str(e)}")
                    continue
            
            return decision_makers
            
        except Exception as e:
            print(f"Error getting decision makers: {str(e)}")
            return []
    
    def scrape_company(self, company_name):
        """Search for a company and scrape its decision makers' information."""
        if not self.logged_in:
            self.login()
            
        if self.search_company(company_name):
            # Wait a moment for the company page to fully load
            time.sleep(3)
            
            # Get decision makers
            decision_makers = self.get_decision_makers()
            
            # Add company name to each decision maker
            for dm in decision_makers:
                dm["company"] = company_name

            self.driver.get(GROWJO_SEARCH_URL)
                
            return decision_makers
        
        return []
    
    def close(self):
        """Close the browser."""
        if hasattr(self, 'driver'):
            self.driver.quit()


def main():
    """Main function to run the scraper."""
    parser = argparse.ArgumentParser(description="Scrape decision makers from Growjo.com")
    parser.add_argument("--input", "-i", required=True, help="Input CSV file with company names")
    parser.add_argument("--output", "-o", required=True, help="Output CSV file for results")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    args = parser.parse_args()
    
    # Read input CSV
    try:
        companies_df = pd.read_csv(args.input)
        if "company" not in companies_df.columns:
            raise ValueError("Input CSV must contain a 'company' column")
    except Exception as e:
        print(f"Error reading input file: {str(e)}")
        return
    
    # Initialize scraper
    scraper = GrowjoScraper(headless=args.headless)
    
    try:
        # List to store all decision makers
        all_decision_makers = []
        
        # Process each company
        for company in tqdm(companies_df["company"], desc="Scraping companies"):
            decision_makers = scraper.scrape_company(company)
            
            # If no decision makers found, add a placeholder entry with "not found" in each column
            if not decision_makers:
                print(f"No decision makers found for {company}. Adding 'not found' placeholder.")
                all_decision_makers.append({
                    "name": "not found",
                    "title": "not found",
                    "contact_info": "not found",
                    "linkedin": "not found",
                    "company": company
                })
            else:
                all_decision_makers.extend(decision_makers)
            
            # Save progress after each company
            pd.DataFrame(all_decision_makers).to_csv(args.output, index=False)
            
            # Small delay between companies to avoid excessive requests
            time.sleep(2)
        
        print(f"Scraping complete! Found {len(all_decision_makers)} decision makers across {len(companies_df)} companies.")
        print(f"Results saved to {args.output}")
        
    except KeyboardInterrupt:
        print("Scraping interrupted by user.")
    except Exception as e:
        print(f"Error during scraping: {str(e)}")
    finally:
        scraper.close()


if __name__ == "__main__":
    main() 