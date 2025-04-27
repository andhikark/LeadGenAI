import os
import time
import difflib
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

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
        self.wait = WebDriverWait(self.driver, 10)  # Increased timeout to 10 seconds
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
            # DEBUG: Capturing screenshot of failed login attempt to visually inspect the page state
            
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
        """
        Search for a company on Growjo and click its link if matched.
        Use similarity score between intended and found company name.
        """
        try:
            print(f"\n[DEBUG] Searching for company: '{company_name}'")

            intended = company_name.strip().lower()
            words = intended.split()

            while words:
                query = " ".join(words)
                print(f"[DEBUG] Trying search with query: '{query}'")

                search_url = f"https://growjo.com/?query={'%20'.join(query.split())}"
                self.driver.get(search_url)
                time.sleep(2)

                try:
                    print("[DEBUG] Waiting for at least one company row to load...")
                    self.wait.until(EC.presence_of_element_located(
                        (By.XPATH, "//table//tbody//tr")
                    ))
                    print("[DEBUG] Company table and rows loaded ✅")
                except TimeoutException:
                    print(f"[DEBUG] Company table not loaded for '{query}'.")
                    if len(words) <= 1:
                        print(f"[ERROR] Search failed even for single word '{query}'. Stopping.")
                        return False
                    words.pop()
                    continue

                company_links = self.driver.find_elements(
                    By.XPATH, "//table//tbody//a[starts-with(@href, '/company/')]"
                )

                if company_links:
                    link = company_links[0]
                    href = link.get_attribute("href")
                    if href and "/company/" in href:
                        href_company_part = href.split("/company/")[1]
                        link_full_text = href_company_part.replace("_", " ").lower()
                    else:
                        link_full_text = link.text.strip().lower()

                    print(f"[DEBUG] First result (reconstructed): '{link_full_text}'")

                    similarity = self._calculate_similarity(intended, link_full_text)
                    print(f"[DEBUG] Similarity score: {similarity:.2f}")

                    if similarity >= 0.65:  # ✅ Accept only if good similarity
                        print(f"[DEBUG] Found good match: '{link_full_text}', clicking...")
                        self.driver.execute_script("arguments[0].click();", link)
                        time.sleep(2)

                        if "/company/" in self.driver.current_url:
                            print(f"[DEBUG] Landed on company page: {self.driver.current_url}")
                            return True
                        else:
                            print(f"[ERROR] After click, not redirected properly.")
                            return False
                    else:
                        print(f"[DEBUG] Similarity too low for '{link_full_text}'. Trimming...")

                else:
                    print(f"[DEBUG] No company links found for '{query}'.")

                if len(words) <= 1:
                    print(f"[ERROR] No good match after all trims for '{company_name}'.")
                    return False
                words.pop()

            print(f"[ERROR] Company '{company_name}' not found after all attempts.")
            return False

        except Exception as e:
            print(f"[ERROR] Unexpected error in search_company: {str(e)}")
            return False


    def _calculate_similarity(self, a: str, b: str) -> float:
        """
        Helper to calculate similarity between two strings using difflib.
        Returns a float between 0 and 1.
        """
        a_clean = a.replace(",", "").replace(".", "").lower()
        b_clean = b.replace(",", "").replace(".", "").lower()
        return difflib.SequenceMatcher(None, a_clean, b_clean).ratio()





        
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
    
    def find_decision_maker(self):
        try:
            print("[DEBUG] Looking for decision makers...")

            # 🛠️ Step 1: Scroll to bottom to trigger full people loading
            print("[DEBUG] Scrolling to trigger lazy loading of all employees...")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

            # 🛠️ Step 2: Wait until at least 5 rows are loaded
            try:
                self.wait.until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//h2[contains(., 'People')]/following::table//tbody/tr[5]")
                    )
                )
                print("[DEBUG] People table and at least 5 rows loaded ✅")
            except TimeoutException:
                print("[ERROR] People table or enough rows not loaded after scrolling.")
                return None

            # 🛠️ Step 3: Locate and parse people
            people_table = self.driver.find_element(
                By.XPATH, "//h2[contains(., 'People')]/following::table[1]"
            )
            rows = people_table.find_elements(By.TAG_NAME, "tr")[1:]  # Skip header
            print(f"[DEBUG] Found {len(rows)} people listed.")

            candidates = []

            def assign_priority(title):
                """Assign decision maker priority based on strict title rules."""
                title = title.lower().replace("&", "and").replace("/", " ")
                words = title.split()
                if not words:
                    return 999
                first_word = words[0]
                if first_word in ["owner", "founder", "president", "director", "founding"]:
                    return 1
                elif first_word in ["co-founder", "cofounder"]:
                    return 2
                elif first_word == "ceo":
                    return 3
                elif first_word == "chief" and len(words) > 1:
                    second_word = words[1]
                    if second_word in [
                        "executive", "product", "marketing", "financial", "sales",
                        "growth", "operating", "audit", "compliance", "information"
                    ]:
                        return 3
                return 999

            for idx, row in enumerate(rows):
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) < 2:
                    continue

                name_col = cols[0]
                title_col = cols[1]

                try:
                    profile_link_elem = name_col.find_element(By.XPATH, ".//a[contains(@href, '/employee/')]")
                    href = profile_link_elem.get_attribute("href")
                    name = profile_link_elem.text.strip()
                    raw_title = title_col.text.strip()

                    if not href or not name:
                        continue

                    profile_url = "https://growjo.com" + href if href.startswith("/employee/") else href
                    priority = assign_priority(raw_title)

                    candidates.append({
                        "name": name,
                        "title": raw_title,
                        "profile_url": profile_url,
                        "priority": priority
                    })

                    print(f"[DEBUG] Candidate: {name} - {raw_title} (Priority: {priority})")

                except Exception as e:
                    print(f"[ERROR] Could not extract person info: {str(e)}")
                    continue

            # 🛠️ Step 4: Pick best candidate
            if candidates:
                candidates.sort(key=lambda x: x["priority"])
                best_candidate = candidates[0]

                print(f"[DEBUG] Best candidate found: {best_candidate['name']} - {best_candidate['title']} (Priority: {best_candidate['priority']})")

                return {
                    "name": best_candidate["name"],
                    "title": best_candidate["title"],
                    "profile_url": best_candidate["profile_url"]
                }

            print("[DEBUG] No decision makers found.")
            return None

        except Exception as e:
            print(f"[ERROR] Error finding decision maker: {str(e)}")
            return None





    def scrape_decision_maker_details(self, profile_url):
        try:
            print(f"[DEBUG] Navigating to decision maker profile: {profile_url}")
            self.driver.get(profile_url)
            time.sleep(3)

            # Click reveal buttons
            reveal_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Reveal')] | //a[contains(text(), 'Reveal')]")
            for btn in reveal_buttons:
                try:
                    self.driver.execute_script("arguments[0].click();", btn)
                    print(f"[DEBUG] Clicked a reveal button.")
                    time.sleep(2)
                except Exception as e:
                    print(f"[ERROR] Error clicking reveal button: {str(e)}")

            # Now start scraping Email and Phone
            email = None
            phone = None

            try:
                # Find all <a href="/join"> elements after reveal
                join_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/join')]")
                print(f"[DEBUG] Found {len(join_links)} elements with href='/join'")

                for elem in join_links:
                    text = elem.text.strip()
                    print(f"[DEBUG] join_link text: '{text}'")

                    if '@' in text and '.' in text and not email:
                        email = text
                    elif text.isdigit() and len(text) >= 8 and not phone:
                        phone = text

                if not email:
                    print("[DEBUG] Email not found after reveal.")
                if not phone:
                    print("[DEBUG] Phone number not found after reveal.")

            except Exception as e:
                print(f"[ERROR] Error extracting email/phone: {str(e)}")

            # Scrape LinkedIn link separately
            linkedin_url = None
            try:
                linkedin_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, 'linkedin.com')]")
                if linkedin_links:
                    linkedin_url = linkedin_links[0].get_attribute("href")
            except Exception as e:
                print(f"[ERROR] Error extracting LinkedIn URL: {str(e)}")

            return {
                "email": email or "not found",
                "phone": phone or "not found",
                "linkedin": linkedin_url or "not found",
            }

        except Exception as e:
            print(f"[ERROR] Error scraping decision maker details: {str(e)}")
            return {
                "email": "not found",
                "phone": "not found",
                "linkedin": "not found",
            }



    def scrape_company(self, company_name):
        """
        Full flow: login if needed, search company, scrape company details,
        find decision maker, scrape decision maker details, and return all combined info.
        """
        try:
            if not self.logged_in:
                self.login()

            success = self.search_company(company_name)
            if not success:
                print(f"[ERROR] Could not find company page for '{company_name}'")
                return self._build_default_result(company_name)

            # Extract company details
            company_info = self.extract_company_details(company_name)

            result = {
                "company_name": company_info.get("company", company_name),
                "company_website": company_info.get("website", "not found"),
                "revenue": company_info.get("revenue", "not found"),
                "location": ", ".join(filter(None, [company_info.get('city', ''), company_info.get('state', '')])) or "not found",
                "industry": company_info.get("industry", "not found"),
                "interests": company_info.get("specialties", "not found"),
                "employee_count": company_info.get("employees", "not found"),
            }

            # Find and scrape decision maker
            decider = self.find_decision_maker()
            if decider and decider.get("profile_url"):
                decider_details = self.scrape_decision_maker_details(decider["profile_url"])
                result.update({
                    "decider_name": decider.get("name", "not found"),
                    "decider_title": decider.get("title", "not found"),
                    "decider_email": decider_details.get("email", "not found"),
                    "decider_phone": decider_details.get("phone", "not found"),
                    "decider_linkedin": decider_details.get("linkedin", "not found"),
                })
            else:
                # If no decider found
                result.update({
                    "decider_name": "not found",
                    "decider_title": "not found",
                    "decider_email": "not found",
                    "decider_phone": "not found",
                    "decider_linkedin": "not found",
                })

            return result

        except Exception as e:
            print(f"[ERROR] Unexpected error in scrape_company for '{company_name}': {str(e)}")
            return self._build_default_result(company_name)

    def _build_default_result(self, company_name):
        """
        Helper to return default empty result if something fails.
        """
        return {
            "company_name": company_name,
            "company_website": "not found",
            "revenue": "not found",
            "location": "not found",
            "industry": "not found",
            "interests": "not found",
            "employee_count": "not found",
            "decider_name": "not found",
            "decider_title": "not found",
            "decider_email": "not found",
            "decider_phone": "not found",
            "decider_linkedin": "not found"
        }

    def close(self):
        """Safely close the browser driver."""
        try:
            if hasattr(self, 'driver') and self.driver:
                self.driver.quit()
        except Exception as e:
            print(f"[ERROR] Error during browser closing: {str(e)}")