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
from scraper.apollo_people import find_best_person, enrich_person


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

@app.route("/api/scrape-growjo-batch", methods=["POST"])
def scrape_growjo_batch():
    try:
        data_list = request.get_json()

        # :rotating_light: Validate: must be a list
        if not isinstance(data_list, list):
            return jsonify({"error": "Expected a JSON array (list of companies)"}), 400

        # :rocket: Initialize scraper (always headless=False for now, you can change later)
        scraper = GrowjoScraper(headless=True)

        results = []
        for idx, entry in enumerate(data_list, start=1):
            company_name = entry.get("company") or entry.get("name")

            if not company_name:
                error_msg = f"Missing 'company' or 'name' field at item {idx}"
                print(f"[ERROR] {error_msg}")
                results.append({
                    "error": error_msg,
                    "input_name": None
                })
                continue

            try:
                print(f"[INFO] Scraping company: {company_name}")
                result = scraper.scrape_full_pipeline(company_name)

                if not result:
                    result = {
                        "error": f"Scraping returned no data for '{company_name}'",
                        "company_name": company_name
                    }

                result["input_name"] = company_name
                results.append(result)

            except Exception as scrape_error:
                error_msg = f"Scraping failed for '{company_name}': {str(scrape_error)}"
                print(f"[ERROR] {error_msg}")
                results.append({
                    "error": error_msg,
                    "input_name": company_name
                })

        scraper.close()
        return jsonify(results), 200

    except Exception as e:
        print(f"[FATAL ERROR] {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/find-best-person-batch", methods=["POST"])
def api_find_best_person_batch():
    try:
        data = request.get_json()
        domains = data.get("domains")

        if not domains or not isinstance(domains, list):
            return jsonify({"error": "Missing or invalid 'domains' field"}), 400

        results = []
        for domain in domains:
            best_person = find_best_person(domain)
            if not best_person:
                results.append({
                    "domain": domain,
                    "error": "No person found"
                })
                continue

            enriched = enrich_person(best_person.get("first_name", ""), best_person.get("last_name", ""), domain)

            if not enriched:
                results.append({
                    "domain": domain,
                    "first_name": best_person.get("first_name", ""),
                    "last_name": best_person.get("last_name", ""),
                    "title": best_person.get("title", ""),
                    "email": "email_not_found@domain.com",
                    "phone_number": "No phone found",
                    "linkedin_url": best_person.get("linkedin_url", ""),
                    "company": best_person.get("organization", {}).get("name", "")
                })
                continue

            results.append({
                "domain": domain,
                "first_name": enriched.get("first_name", best_person.get("first_name", "")),
                "last_name": enriched.get("last_name", best_person.get("last_name", "")),
                "title": enriched.get("title", best_person.get("title", "")),
                "email": enriched.get("email", "email_not_found@domain.com"),
                "phone_number": enriched.get("phone_numbers", [{}])[0].get("sanitized_number", "No phone found") if enriched.get("phone_numbers") else "No phone found",
                "linkedin_url": enriched.get("linkedin_url", best_person.get("linkedin_url", "")),
                "company": enriched.get("organization_name", best_person.get("organization", {}).get("name", ""))
            })

        return jsonify(results), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))  # Render will provide the port
    app.run(host="0.0.0.0", port=port, debug=True)

