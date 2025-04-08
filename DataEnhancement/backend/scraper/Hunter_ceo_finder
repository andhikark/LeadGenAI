import requests
import pandas as pd
import time
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class CompanyInfoRetriever:
    def __init__(self, hunter_api_key=None):
        """Initialize with your Hunter.io API key."""
        self.hunter_api_key = hunter_api_key or os.getenv("HUNTER_API_KEY")
        if not self.hunter_api_key:
            raise ValueError("Hunter.io API key is required. Set it as HUNTER_API_KEY environment variable or pass it directly.")
    
    def get_company_domain(self, company_name):
        """Use Hunter.io to find a company's domain name."""
        url = "https://api.hunter.io/v2/domain-search"
        params = {
            "company": company_name,
            "api_key": self.hunter_api_key,
            "limit": 1
        }
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data.get('data', {}).get('domain'):
                    return data['data']['domain']
            return None
        except Exception as e:
            print(f"Error finding domain for {company_name}: {str(e)}")
            return None
    
    def find_company_emails(self, domain, seniority=None):
        """Find email addresses at a company with optional seniority filter."""
        if not domain:
            return []
            
        url = "https://api.hunter.io/v2/domain-search"
        params = {
            "domain": domain,
            "api_key": self.hunter_api_key,
            "limit": 10  # Increase if needed, but consider API limits
        }
        
        if seniority:
            params["seniority"] = seniority
            
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                return data.get('data', {}).get('emails', [])
            return []
        except Exception as e:
            print(f"Error finding emails for {domain}: {str(e)}")
            return []
    
    def extract_ceo_info(self, emails):
        """Extract CEO information from a list of email data objects."""
        if not emails:
            return None
            
        # First look for CEO title
        for email in emails:
            if not email:  # Skip None values
                continue
                
            position = (email.get('position') or '').lower()  # Handle None positions safely
            if position and ('ceo' in position or 'chief executive officer' in position or 
                            ('founder' in position and 'chief' in position)):
                return {
                    'name': f"{email.get('first_name', '')} {email.get('last_name', '')}".strip(),
                    'email': email.get('value', ''),
                    'position': email.get('position', ''),
                    'linkedin': email.get('linkedin', '')
                }
        
        # If no CEO found but there's a founder
        for email in emails:
            if not email:  # Skip None values
                continue
                
            position = (email.get('position') or '').lower()  # Handle None positions safely
            if position and ('founder' in position or 'owner' in position or 'president' in position):
                return {
                    'name': f"{email.get('first_name', '')} {email.get('last_name', '')}".strip(),
                    'email': email.get('value', ''),
                    'position': email.get('position', ''),
                    'linkedin': email.get('linkedin', '')
                }
        
        # If no specific position found, take the first senior person
        for email in emails:
            if not email:  # Skip None values
                continue
                
            if email.get('seniority') == 'executive':
                return {
                    'name': f"{email.get('first_name', '')} {email.get('last_name', '')}".strip(),
                    'email': email.get('value', ''),
                    'position': email.get('position', ''),
                    'linkedin': email.get('linkedin', '')
                }
        
        # Fall back to first result if nothing else
        if emails and emails[0]:
            return {
                'name': f"{emails[0].get('first_name', '')} {emails[0].get('last_name', '')}".strip(),
                'email': emails[0].get('value', ''),
                'position': emails[0].get('position', 'Unknown'),
                'linkedin': emails[0].get('linkedin', '')
            }
            
        return None
    
    def get_company_ceo_info(self, company_name):
        """Get CEO information for a given company."""
        result = {
            "company_name": company_name,
            "domain": None,
            "ceo_name": None,
            "ceo_position": None,
            "ceo_email": None,
            "ceo_linkedin": None,
            "status": "Processing"
        }
        
        try:
            # Step 1: Find company domain
            print(f"Finding domain for {company_name}...")
            domain = self.get_company_domain(company_name)
            if not domain:
                result["status"] = "Company domain not found"
                return result
                
            result["domain"] = domain
            print(f"Found domain: {domain}")
            
            # Step 2: Find company emails (try executive seniority first)
            print(f"Finding executives for {domain}...")
            emails = self.find_company_emails(domain, seniority="executive")
            if not emails:
                # Try without seniority filter
                print("No executives found, trying general search...")
                emails = self.find_company_emails(domain)
                
            # Step 3: Extract CEO information
            if emails:
                print(f"Found {len(emails)} email contacts, extracting CEO info...")
                ceo_info = self.extract_ceo_info(emails)
                if ceo_info:
                    # Step 4: Populate result
                    result["ceo_name"] = ceo_info.get('name')
                    result["ceo_position"] = ceo_info.get('position')
                    result["ceo_email"] = ceo_info.get('email')
                    result["ceo_linkedin"] = ceo_info.get('linkedin')
                    result["status"] = "Success"
                    print(f"Successfully found CEO: {ceo_info.get('name')}")
                else:
                    result["status"] = "Could not identify CEO"
                    print("Could not identify CEO from contacts")
            else:
                result["status"] = "No contacts found"
                print("No contacts found")
                
        except Exception as e:
            print(f"Error processing {company_name}: {str(e)}")
            result["status"] = f"Error: {str(e)}"
            
        return result

def read_companies_from_csv(csv_file_path, company_name_column='company_name'):
    """Read company names from a CSV file."""
    try:
        # Read the CSV file
        df = pd.read_csv(csv_file_path)
        
        # Check if the company name column exists
        if company_name_column not in df.columns:
            print(f"Error: Column '{company_name_column}' not found in CSV. Available columns: {df.columns.tolist()}")
            print("Using the first column as company name column.")
            company_name_column = df.columns[0]
            
        # Extract company names
        companies = df[company_name_column].tolist()
        
        # Remove any NaN values and convert to string
        companies = [str(company).strip() for company in companies if pd.notna(company)]
        
        return companies
    except Exception as e:
        print(f"Error reading CSV file: {str(e)}")
        return []

def main():
    # Parse command line arguments
    if len(sys.argv) < 2:
        print("Usage: python script.py <path_to_csv_file> [company_name_column]")
        print("Example: python script.py companies.csv company_name")
        return
        
    csv_file_path = sys.argv[1]
    
    # If column name is provided as argument, use it
    company_name_column = 'company_name'  # Default column name
    if len(sys.argv) > 2:
        company_name_column = sys.argv[2]
        
    # Read companies from CSV
    print(f"Reading companies from {csv_file_path}...")
    companies = read_companies_from_csv(csv_file_path, company_name_column)
    
    if not companies:
        print("No companies found in the CSV file. Exiting.")
        return
        
    print(f"Found {len(companies)} companies in the CSV file.")
    
    # Create the retriever
    api_key = "4c079a55cab715a7195e9426d8b53840ee087e91"  # Your API key
    retriever = CompanyInfoRetriever(api_key)
    
    # Process each company
    results = []
    for i, company in enumerate(companies):
        print(f"\nProcessing {company} ({i+1}/{len(companies)})...")
        result = retriever.get_company_ceo_info(company)
        results.append(result)
        print(f"Status: {result['status']}")
        if i < len(companies) - 1:  # Don't sleep after the last item
            print(f"Waiting 2 seconds before next company...")
            time.sleep(2)  # Rate limiting to avoid hitting API limits
    
    # Convert to DataFrame and save to CSV
    output_file = "company_ceo_data_results.csv"
    df = pd.DataFrame(results)
    df.to_csv(output_file, index=False)
    print(f"\nData saved to {output_file}")
    print(f"Used {len(companies)} out of 25 free monthly searches.")

if __name__ == "__main__":
    main()