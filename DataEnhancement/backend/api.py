from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os, time
import pandas as pd
import asyncio
import uuid
import logging
from scraper.revenueScraper import get_company_revenue_from_growjo
from scraper.websiteNameScraper import find_company_website
from scraper.apollo_scraper import enrich_single_company
from scraper.linkedinScraper.scraping.scraper import scrape_linkedin
from scraper.linkedinScraper.scraping.login import login_to_linkedin
from scraper.linkedinScraper.utils.chromeUtils import get_chrome_driver
from selenium.webdriver.common.by import By

# from scraper.linkedinScraper.main import run_batch
# from scraper.linkedinScraper.utils.chromeUtils import CHROME_INFO_FILE
from scraper.growjoScraper import GrowjoScraper
from security import generate_token, token_required, VALID_USERS


app = Flask(__name__)
load_dotenv()

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "message": "leadgen API is alive"}), 200

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Missing credentials"}), 400

    if VALID_USERS.get(username) != password:
        return jsonify({"error": "Invalid credentials"}), 401

    return jsonify({
        "message": "Login successful",
        "token": generate_token(username),
        "username": username
    }), 200

# Protected Test Endpoint
@app.route('/api/protected-test', methods=['GET'])
@token_required
def protected_test():
    return jsonify({"message": "This is a protected route"}), 200

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

class DummyTQDM:
    def update(self, _):
        pass

from flask import request, jsonify
from selenium.webdriver.common.by import By
from scraper.linkedinScraper.utils.chromeUtils import  generate_smartproxy_url
from scraper.linkedinScraper.scraping.scraper import scrape_linkedin

@app.route("/api/linkedin-info-batch", methods=["POST"])
def get_linkedin_info_batch():
    try:
        payload = request.get_json()
        if not isinstance(payload, dict) or "li_at" not in payload or "data" not in payload:
            return jsonify({"error": "Expected JSON with 'li_at' and 'data'"}), 400

        li_at = payload["li_at"]
        data_list = payload["data"]

        # 🔐 Inject token into runtime env
        os.environ["LI_AT"] = li_at

        # ✅ Log which proxy is in use
        proxy_url = generate_smartproxy_url("linkedin_batch_1")
        print(f"🌐 Using proxy: {proxy_url}")

        driver = get_chrome_driver(headless=False)

        # Optional sanity check
        try:
            driver.get("https://api.myip.com")
            time.sleep(2)
            ip_info = driver.find_element(By.TAG_NAME, "body").text
            print(f"🔎 Current IP Session Info: {ip_info}")
        except Exception as e:
            print(f"⚠️ Could not fetch IP info: {e}")

        # 🔄 Scrape loop
        results = []
        for entry in data_list:
            company = entry.get("company")
            city = entry.get("city")
            state = entry.get("state")
            website = entry.get("website")

            if not company:
                results.append({"error": "Missing 'company' field."})
                continue

            result = scrape_linkedin(driver, company, city, state, website)
            result["company"] = company
            results.append(result)

        driver.quit()
        return jsonify(results), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route("/api/growjo", methods=["POST"])
def scrape():
    data = request.get_json()
    if not data or "company" not in data:
        return jsonify({"error": "Missing 'company' in request JSON"}), 400

    company = data["company"]
    headless = data.get("headless", True)

    scraper = GrowjoScraper(headless=headless)
    try:
        results = scraper.scrape_company(company)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        scraper.close()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))  # Render will provide the port
    app.run(host="0.0.0.0", port=port, debug=True)

