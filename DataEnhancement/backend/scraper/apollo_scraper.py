from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")

def enrich_single_company(domain):
    """Call Apollo API and extract founded_year, linkedin_url, keywords, annual_revenue_printed, website_url, employee_count."""
    url = "https://api.apollo.io/api/v1/organizations/enrich"
    headers = {
        "accept": "application/json",
        "Cache-Control": "no-cache",
        "Content-Type": "application/json",
        "X-Api-Key": APOLLO_API_KEY
    }
    params = {"domain": domain}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            org = response.json().get("organization", {})
            founded_year = org.get("founded_year", "")
            linkedin_url = org.get("linkedin_url", "")
            keywords_list = org.get("keywords", [])
            keywords_combined = ", ".join(keywords_list) if keywords_list else ""
            annual_revenue_printed = org.get("annual_revenue_printed", "")
            website_url = org.get("website_url", "")
            employee_count = org.get("estimated_num_employees", "")

            return {
                "founded_year": founded_year,
                "linkedin_url": linkedin_url,
                "keywords": keywords_combined,
                "annual_revenue_printed": annual_revenue_printed,
                "website_url": website_url,
                "employee_count": employee_count
            }
        else:
            return {"error": f"Status {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}
