from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
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
from scraper.linkedinScraper.main import run_batch
from scraper.linkedinScraper.utils.chromeUtils import CHROME_INFO_FILE
from scraper.growjoScraper import GrowjoScraper
from security import generate_token, token_required, VALID_USERS


app = Flask(__name__)
load_dotenv()

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

@app.route("/api/linkedin-info-batch", methods=["POST"])
def get_linkedin_info_batch():
    try:
        payload = request.get_json()

        if not isinstance(payload, dict) or "data" not in payload or "li_at" not in payload:
            return jsonify({"error": "Expected JSON object with 'data' (list) and 'li_at' (string)"}), 400

        data_list = payload["data"]
        li_at = payload["li_at"]

        if not isinstance(data_list, list):
            return jsonify({"error": "Field 'data' must be a list"}), 400
        if not isinstance(li_at, str) or not li_at.strip():
            return jsonify({"error": "Field 'li_at' must be a non-empty string"}), 400

        df = pd.DataFrame(data_list)
        df.rename(columns=lambda col: col.capitalize(), inplace=True)

        if df.empty or "Company" not in df.columns:
            return jsonify({"error": "Missing or empty 'Company' column"}), 400

        BATCH_SIZE = 5
        all_results = []

        # Remove stale Chrome session if needed
        if CHROME_INFO_FILE.exists():
            CHROME_INFO_FILE.unlink()

        batches = [df[i:i + BATCH_SIZE] for i in range(0, len(df), BATCH_SIZE)]
        total_batches = len(batches)

        for idx, batch_df in enumerate(batches):
            batch_results = run_batch(
                batch_df=batch_df,
                batch_index=idx,
                total_batches=total_batches,
                global_progress=all_results,
                global_bar=DummyTQDM(),   # no CLI progress in API mode
                output_path=None,         # disable CSV writing in API mode
                li_at=li_at               # pass user-provided li_at
            )
            all_results.extend(batch_results)

        return jsonify(all_results), 200

    except Exception as e:
        logging.error(f"🔥 API Fatal error: {e}", exc_info=True)
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
    port = int(os.environ.get("PORT", 5000))  # Render will provide the port
    app.run(host="0.0.0.0", port=port, debug=True)

