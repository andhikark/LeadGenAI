from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")

def enrich_single_company(domain):
    """Call Apollo API and extract specific fields."""
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
            return {
                "domain": domain,
                "name": org.get("name", ""),
                "website_url": org.get("website_url", ""),
                "linkedin_url": org.get("linkedin_url", ""),
                "founded_year": org.get("founded_year", ""),
                "annual_revenue_printed": org.get("annual_revenue_printed", "")
            }
        else:
            return {"domain": domain, "error": f"Status {response.status_code}"}
    except Exception as e:
        return {"domain": domain, "error": str(e)}