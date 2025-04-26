from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os, time
# import pandas as pd
import asyncio
import uuid
import logging
from scraper.apollo_scraper import enrich_single_company
from selenium.webdriver.common.by import By
import shutil
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

@app.route("/api/apollo-scrape-batch", methods=["POST"])
def apollo_scrape_batch():
    data = request.get_json()
    domains = data.get("domains")

    if not domains or not isinstance(domains, list):
        return jsonify({"error": "Missing or invalid 'domains' (must be a list)"}), 400

    results = []
    for domain in domains:
        enriched_data = enrich_single_company(domain)
        enriched_data["domain"] = domain  # always return domain
        results.append(enriched_data)

    return jsonify(results)

@app.route("/api/scrape-growjo", methods=["POST"])
def scrape_growjo():
    data = request.get_json()
    
    if not data or "company" not in data:
        return jsonify({"error": "Missing 'company' in request JSON"}), 400

    company = data["company"]
    headless = data.get("headless", False)  # default: headless browser = False

    scraper = GrowjoScraper(headless=headless)
    try:
        results = scraper.scrape_company(company)
        return jsonify(results), 200
    except Exception as e:
        print(f"[ERROR] API scraping error: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        try:
            scraper.close()
        except Exception as e:
            print(f"[ERROR] Failed closing browser: {str(e)}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))  # Render will provide the port
    app.run(host="0.0.0.0", port=port, debug=True)

