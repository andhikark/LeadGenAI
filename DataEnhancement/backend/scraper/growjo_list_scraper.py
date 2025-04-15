from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import unquote
import time

def get_growjo_company_list(search_term):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920x1080")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        search_url = f"https://growjo.com/?query={search_term.replace(' ', '%20')}"
        driver.get(search_url)
        time.sleep(3)  # Let it render

        rows = driver.find_elements(By.CSS_SELECTOR, "table.jss31 tbody tr")
        results = []

        for row in rows:
            try:
                link = row.find_element(By.CSS_SELECTOR, "a[href^='/company/']")
                href = link.get_attribute("href")
                if "/company/" in href:
                    slug = href.split("/company/")[-1]
                    name = unquote(slug.replace("_", " ")).strip()
                    results.append(name)
            except:
                continue

        return results

    except Exception as e:
        print(f"❌ Growjo fallback error: {e}")
        return []
    finally:
        driver.quit()

# # Example usage
# if __name__ == "__main__":
#     term = "coca cola"
#     results = get_growjo_company_list(term)

#     if results:
#         print("\n✅ Growjo Search Results:")
#         for i, name in enumerate(results, 1):
#             print(f"{i}. {name}")
#     else:
#         print("\n❌ No results found or failed to fetch.")
