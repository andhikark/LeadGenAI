import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import re
import time

def search_crunchbase_url(company_name):
    query = quote(f"{company_name} site:crunchbase.com/organization")
    url = f"https://duckduckgo.com/html/?q={query}"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        results = soup.select("a.result__a")
        for link in results:
            href = link.get("href", "")
            if "crunchbase.com/organization" in href:
                return href
    except Exception as e:
        print(f"[DuckDuckGo error] {e}")
    return None


def extract_revenue_from_crunchbase(url):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        text = soup.get_text(separator="\n")

        matches = re.findall(r'\$\d{1,3}(?:\.\d+)?[MB]?', text)
        for match in matches:
            if match:
                return match
    except Exception as e:
        print(f"[Crunchbase scrape error] {e}")
    return "Revenue info not found"

def get_company_revenue(company_name):
    crunchbase_url = search_crunchbase_url(company_name)
    if not crunchbase_url:
        return {"error": "Crunchbase page not found"}

    time.sleep(2) 
    revenue = extract_revenue_from_crunchbase(crunchbase_url)
    return {
        "company": company_name,
        "source": crunchbase_url,
        "estimated_revenue": revenue
    }
