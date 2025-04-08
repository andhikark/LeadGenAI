import requests
from bs4 import BeautifulSoup
import re

def get_company_revenue_from_growjo(company_name):
    base_url = "https://growjo.com/company/"
    company_url = base_url + company_name.replace(" ", "")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    try:
        res = requests.get(company_url, headers=headers, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        revenue = "<$5M"
        for li in soup.find_all("li"):
            text = li.get_text(strip=True)
            if "estimated annual revenue" in text:
                match = re.search(r"\$\d[\d\.]*[MB]?", text)
                if match:
                    revenue = match.group(0)
                    break

        return {
            "company": company_name,
            "estimated_revenue": revenue
        }

    except Exception as e:
        return {
            "company": company_name,
            "url": company_url,
            "error": str(e)
        }
