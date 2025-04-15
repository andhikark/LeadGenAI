import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import re

# ✅ Import fallback Growjo search
from growjo_list_scraper import get_growjo_company_list

def clean_company_name_variants(name):
    variants = []

    original = name.strip()
    variants.append(original)

    if "&" in original:
        variants.append(original.replace("&", "and"))

    if "-" in original:
        variants.append(original.replace("-", " "))

    no_special = re.sub(r"[^\w\s\-&]", "", original)
    if no_special != original:
        variants.append(no_special)

    normalized_space = " ".join(original.split())
    if normalized_space != original:
        variants.append(normalized_space)

    return list(dict.fromkeys(variants))

def get_company_revenue_from_growjo(company_name, depth=0):
    base_url = "https://growjo.com/company/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    name_variants = clean_company_name_variants(company_name)

    for name_variant in name_variants:
        company_url = base_url + quote(name_variant)

        try:
            res = requests.get(company_url, headers=headers, timeout=10)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, "html.parser")

            page_text = soup.get_text().lower()

            if (
                "page not found" in page_text or 
                "company not found" in page_text or 
                "rank not available" in page_text or 
                "estimated annual revenue" not in page_text
            ):
                continue  # Not a real match

            revenue = "<$5M"
            for li in soup.find_all("li"):
                text = li.get_text(strip=True)
                if "estimated annual revenue" in text.lower():
                    match = re.search(r"\$\d[\d\.]*[MB]?", text)
                    if match:
                        revenue = match.group(0)
                        break

            return {
                "company": company_name,
                "matched_variant": name_variant,
                "estimated_revenue": revenue,
                "url": company_url
            }


        except requests.exceptions.Timeout:
            return {
                "company": company_name,
                "url": company_url,
                "error": "Request timed out"
            }
        except Exception:
            continue

    # ✅ Fallback: search Growjo and retry with top result
    if depth == 0:
        for variant in clean_company_name_variants(company_name):
            fallback_names = get_growjo_company_list(variant)
            print(f"🔎 Fallback search for variant '{variant}' returned: {fallback_names}")

            if fallback_names:
                top_result = fallback_names[0]
                print(f"🔁 Retrying with top Growjo match: '{top_result}'")
                return get_company_revenue_from_growjo(top_result, depth=1)

    return {
        "company": company_name,
        "error": "Not found in Growjo after variants + fallback search",
        "attempted_variants": name_variants
    }

# Example test
if __name__ == "__main__":
    result = get_company_revenue_from_growjo("Louis Dreyfus")
    print(result)
