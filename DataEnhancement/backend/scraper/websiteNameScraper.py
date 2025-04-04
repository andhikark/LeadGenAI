import requests
from bs4 import BeautifulSoup
from urllib.parse import quote, urlparse

def normalize_url(url):
    if not url:
        return ""
    parsed = urlparse(url)
    return parsed.netloc.lower().replace("www.", "").strip("/")

def find_company_website(company_name):
    query = quote(f"{company_name} official website")
    url = f"https://search.brave.com/search?q={query}"
    print(url)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        result_links = soup.select("a[href^='http']")
        for link in result_links:
            href = link.get("href", "")
            text = link.get_text(strip=True).lower()

            if company_name.lower().split()[0] in href.lower() or "official" in text:
                return href

        return None
    except Exception as e:
        print(f"[Error] {company_name} → {e}")
        return None
