from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
import pandas as pd
import asyncio
from scraper.revenueScraper import get_company_revenue_from_growjo
from scraper.websiteNameScraper import find_company_website
from scraper.apollo_scraper import enrich_single_company
from scraper.linkedinScraper.scraping.scraper import scrape_linkedin
from scraper.linkedinScraper.scraping.login import login_to_linkedin
from scraper.linkedinScraper.utils.chromeUtils import get_chrome_driver


app = Flask(__name__)
load_dotenv()

@app.route("/api/find-website", methods=["GET"])
def get_website():
    company = request.args.get("company")
    if not company:
        return jsonify({"error": "Missing company parameter"}), 400

    website = find_company_website(company)
    print(website)
    if website:
        return jsonify({"company": company, "website": website})
    else:
        return jsonify({"error": "Website not found"}), 404

@app.route("/api/get-revenue", methods=["GET"])
def get_revenue():
    company = request.args.get("company")
    if not company:
        return jsonify({"error": "Missing company parameter"}), 400

    data = get_company_revenue_from_growjo(company)
    return jsonify(data)

@app.route("/api/apollo-info", methods=["POST"])
def get_apollo_info_batch():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Missing request body"}), 400

        if isinstance(data, dict):
            data = [data]

        results = []
        for company in data:
            domain = company.get("domain")
            if domain:
                enriched = enrich_single_company(domain)
                results.append(enriched)
            else:
                results.append({"error": "Missing domain"})

        return jsonify(results), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/linkedin-info", methods=["POST"])
def get_linkedin_info():
    try:
        data = request.get_json()
        company = data.get("company")
        city = data.get("city")
        state = data.get("state")
        website = data.get("website")

        if not company:
            return jsonify({"error": "Missing required field: company"}), 400

        driver = get_chrome_driver(headless=True)

        # 🔐 Note: For production, reuse logged-in session instead of logging in every time
        login_to_linkedin(driver, "", "")  # use cookies/session if available

        result = scrape_linkedin(
            driver,
            company=company,
            expected_city=city,
            expected_state=state,
            website=website
        )
        driver.quit()

        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True,use_reloader=False, port=5000)
