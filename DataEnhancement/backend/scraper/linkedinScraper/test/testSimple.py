# test_simple.py

import os
from bs4 import BeautifulSoup

HTML_FILE = "output/about_source_1744899883.html"

def test_bs4_parsing():
    if not os.path.exists(HTML_FILE):
        print(f"[ERROR] File not found: {HTML_FILE}")
        return

    with open(HTML_FILE, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    # Initialize default fields
    fields = {
        "Website": "Not found",
        "Company size": "Not found",
        "Headquarters": "Not found",
        "Founded": "Not found",
        "Specialties": "Not found",
        "Industry": "Not found"
    }

    hq_city = "Not found"
    hq_state = "Not found"

    try:
        # First: Handle the simpler <dt>/<dd> based values
        dts = soup.find_all("dt")
        for dt in dts:
            label = dt.get_text(strip=True).lower()
            dd = dt.find_next_sibling("dd")
            if not dd:
                continue
            value = dd.get_text(strip=True)

            if "website" in label:
                fields["Website"] = value
            elif "company size" in label:
                fields["Company size"] = value
            elif "founded" in label:
                fields["Founded"] = value
            elif "specialties" in label:
                fields["Specialties"] = value
            elif "industry" in label:
                fields["Industry"] = value

        # Then: Parse the Headquarters location block
        hq_block = soup.select_one("div.org-location-card p")
        if hq_block:
            full_hq = hq_block.get_text(strip=True)
            fields["Headquarters"] = full_hq
            parts = [p.strip() for p in full_hq.split(",")]
            if len(parts) >= 2:
                hq_city, hq_state = parts[0], parts[1]
            elif len(parts) == 1:
                hq_city = parts[0]

    except Exception as e:
        print(f"[ERROR] Parsing failed: {e}")

    print("========== PARSED FIELDS ==========")
    print(f"Website      : {fields['Website']}")
    print(f"Size         : {fields['Company size']}")
    print(f"Industry     : {fields['Industry']}")
    print(f"Headquarters : {fields['Headquarters']}")
    print(f"City, State  : {hq_city}, {hq_state}")
    print(f"Founded      : {fields['Founded']}")
    print(f"Specialties  : {fields['Specialties']}")
    print("===================================")

if __name__ == "__main__":
    test_bs4_parsing()