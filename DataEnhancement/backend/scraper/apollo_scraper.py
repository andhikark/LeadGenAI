from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
app = Flask(__name__)

APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")
DEEPSEEK_API_KEY = os.getenv(
    "DEEPSEEK_API_KEY"
)  # Assuming you're using an LLM with an OpenAI-compatible API

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com/v1",  # Replace with actual base URL if different
)


def infer_business_type(description):
    if not description or not description.strip():
        return "N/A"

    prompt = (
        "You are a classifier. Based only on the description below, respond with one of the following labels: B2B, B2C, or B2B2C. "
        "Respond only with the label and nothing else.\n\n"
        f'Description:\n"{description}"\n\nBusiness Type:'
    )

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",  # or the model you're using
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        label = response.choices[0].message.content.strip().upper()
        if label in ["B2B", "B2C", "B2B2C"]:
            return label
        else:
            return "N/A"
    except Exception as e:
        print(f"[ERROR] Failed to classify business type: {e}")
        return "N/A"


def enrich_single_company(domain):
    """Call Apollo API and extract founded_year, linkedin_url, keywords, annual_revenue_printed, website_url, employee_count."""
    url = "https://api.apollo.io/api/v1/organizations/enrich"
    headers = {
        "accept": "application/json",
        "Cache-Control": "no-cache",
        "Content-Type": "application/json",
        "X-Api-Key": APOLLO_API_KEY,
    }
    params = {"domain": domain}

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            org = response.json().get("organization", {})
            founded_year = org.get("founded_year", "")
            linkedin_url = org.get("linkedin_url", "")

            # Limit keywords to 5
            keywords_list = org.get("keywords", [])
            keywords_trimmed = keywords_list[:5] if isinstance(keywords_list, list) else []
            keywords_combined = ", ".join(keywords_trimmed)

            industry = org.get("industry", "")
            # industry_list = org.get("industries")

            # # Prefer list if it exists and is non-empty
            # if isinstance(industry_list, list) and industry_list:
            #     industry = ", ".join(industry_list[:5])  # limit to 5
            # elif isinstance(industry_raw, str) and industry_raw.strip():
            #     industry = industry_raw.strip()
            # else:
            #     industry = "N/A"

            keywords_raw = org.get("keywords")
            if isinstance(keywords_raw, list) and keywords_raw:
                keywords_combined = ", ".join(keywords_raw[:5])
            else:
                keywords_combined = "N/A"

            annual_revenue_printed = org.get("annual_revenue_printed", "")
            website_url = org.get("website_url", "")
            employee_count = org.get("estimated_num_employees", "")
            about = org.get("short_description", "")
            business_type = infer_business_type(about)

            return {
                "founded_year": founded_year,
                "linkedin_url": linkedin_url,
                "keywords": keywords_combined,
                "annual_revenue_printed": annual_revenue_printed,
                "website_url": website_url,
                "employee_count": employee_count,
                "industry": industry,
                "business_type": business_type,
            }
        else:
            return {"error": f"Status {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}
