from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
from scraper.apollo_scraper import enrich_single_company
from scraper.growjoScraper import GrowjoScraper
from scraper.apollo_people import find_best_person
from scraper.apollo_scraper import enrich_single_company


app = Flask(__name__)
load_dotenv()


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"}), 200

# @app.route('/api/login', methods=['POST'])
# def login():
#     data = request.get_json()
#     username = data.get('username')
#     password = data.get('password')

#     if not username or not password:
#         return jsonify({"error": "Missing credentials"}), 400

#     if VALID_USERS.get(username) != password:
#         return jsonify({"error": "Invalid credentials"}), 401

#     return jsonify({
#         "message": "Login successful",
#         "token": generate_token(username),
#         "username": username
#     }), 200

# # Protected Test Endpoint
# @app.route('/api/protected-test', methods=['GET'])
# @token_required
# def protected_test():
#     return jsonify({"message": "This is a protected route"}), 200


@app.route("/api/scrape-growjo-batch", methods=["POST"])
def scrape_growjo_batch():
    try:
        data_list = request.get_json()

        # 🚨 Validate: must be a list
        if not isinstance(data_list, list):
            return jsonify({"error": "Expected a JSON array (list of companies)"}), 400

        # 🚀 Initialize scraper (always headless=False for now, you can change later)
        scraper = GrowjoScraper(headless=True)

        results = []
        for idx, entry in enumerate(data_list, start=1):
            company_name = entry.get("company") or entry.get("name")

            if not company_name:
                error_msg = f"Missing 'company' or 'name' field at item {idx}"
                print(f"[ERROR] {error_msg}")
                results.append({"error": error_msg, "input_name": None})
                continue

            try:
                print(f"[INFO] Scraping company: {company_name}")
                result = scraper.scrape_full_pipeline(company_name)

                if not result:
                    result = {
                        "error": f"Scraping returned no data for '{company_name}'",
                        "company_name": company_name,
                    }

                result["input_name"] = company_name
                results.append(result)

            except Exception as scrape_error:
                error_msg = f"Scraping failed for '{company_name}': {str(scrape_error)}"
                print(f"[ERROR] {error_msg}")
                results.append({"error": error_msg, "input_name": company_name})

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
            print(f"[DEBUG] Fetching decision maker for: {domain}")
            try:
                person = find_best_person(domain.strip())
                if person:
                    results.append(person)
                else:
                    results.append({"domain": domain, "error": "No person found"})
            except Exception as e:
                results.append({"domain": domain, "error": str(e)})

        return jsonify(results), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/apollo-scrape-batch", methods=["POST"])
def apollo_scrape_batch():
    try:
        data = request.get_json()
        domains = data.get("domains")

        if not domains or not isinstance(domains, list):
            return jsonify({"error": "Missing or invalid 'domains' field"}), 400

        results = []
        for domain in domains:
            print(f"[DEBUG] Scraping company info for: {domain}")
            try:
                enriched = enrich_single_company(domain.strip())
                enriched["domain"] = domain
                results.append(enriched)
            except Exception as e:
                results.append({"domain": domain, "error": str(e)})

        return jsonify(results), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))  # Render will provide the port
    app.run(host="0.0.0.0", port=port, debug=True)
