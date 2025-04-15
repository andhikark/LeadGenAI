from revenueScraper import get_company_revenue_from_growjo, clean_company_name_variants
from urllib.parse import quote

if __name__ == "__main__":
    # Test with different company names
    test_companies = [
        "Louis-Dreyfus",
    ]

    for company in test_companies:
        print(f"\n🧪 ========== Testing Company: '{company}' ==========")

        # Show all sanitization attempts
        sanitized_variants = clean_company_name_variants(company)
        print("🧼 Cleaned Variants + Encoded URLs:")
        for variant in sanitized_variants:
            encoded_url = f"https://growjo.com/company/{quote(variant)}"
            print(f"   - '{variant}' → {encoded_url}")

        # Run scraper
        print("\n⚙️ Running Revenue Scraper...")
        result = get_company_revenue_from_growjo(company)

        # Display results
        print("\n📊 Scraping Result:")
        if "estimated_revenue" in result:
            print(f"✅ Success")
            print(f"   - Original Name      : {result['company']}")
            print(f"   - Matched Variant    : {result['matched_variant']}")
            print(f"   - Estimated Revenue  : {result['estimated_revenue']}")
            print(f"   - Scraped URL        : {result['url']}")
        else:
            print(f"❌ Failed to retrieve revenue.")
            print(f"   - Error              : {result.get('error')}")
            print(f"   - Attempted Variants : {result.get('attempted_variants')}")
