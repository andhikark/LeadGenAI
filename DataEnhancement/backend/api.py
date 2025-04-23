from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
import pandas as pd
import logging
from scraper.revenueScraper import get_company_revenue_from_growjo
from scraper.websiteNameScraper import find_company_website
from scraper.apollo_scraper import enrich_single_company
from backend.scraper.linkedinScraper.scraper import run_batch_scraper
from scraper.growjoScraper import GrowjoScraper
from security import generate_token, token_required, VALID_USERS
import tempfile
import asyncio


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
        # Check file and form data
        if "file" not in request.files or "csv" not in request.files:
            return jsonify({"error": "Both 'file' (.dat) and 'csv' (.csv) must be provided"}), 400

        cookie_file = request.files["file"]
        csv_file = request.files["csv"]

        # Save uploaded cookie file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".dat") as session_file:
            session_path = session_file.name
            cookie_file.save(session_path)

        # Save uploaded CSV file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as temp_csv:
            csv_path = temp_csv.name
            csv_file.save(csv_path)

        # Run async scraper in event loop
        asyncio.run(run_batch_scraper(csv_path, session_path))

        # Load and return result
        if not os.path.exists("output/results.csv"):
            return jsonify({"error": "Scraping failed — no results.csv generated"}), 500

        results_df = pd.read_csv("output/results.csv")
        return jsonify(results_df.to_dict(orient="records")), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    finally:
        # Clean up uploaded files
        if os.path.exists(session_path):
            os.remove(session_path)
        if os.path.exists(csv_path):
            os.remove(csv_path)

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
    app.run(host="0.0.0.0", port=port, debug=False)

