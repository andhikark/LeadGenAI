from flask import Flask, request, jsonify
from scraper.revenueScraper import get_company_revenue
from scraper.websiteNameScraper import find_company_website


app = Flask(__name__)

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

    revenue_data = get_company_revenue(company)
    return jsonify(revenue_data)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
