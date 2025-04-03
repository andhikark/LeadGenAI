import os
import asyncio
import csv
from typing import List, Dict
from config.browser_config import PlaywrightManager

BASE_URL = "https://www.google.com/maps"
OUTPUT_DIR = "../data"

def save_to_csv(data: List[Dict[str, str]], file_path: str) -> None:
    """Saves a list of dictionaries to a CSV file."""
    if not data:
        print("Error: No data provided to save.")
        return
    
    # Ensure the directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Define CSV field names
    fieldnames = ["Name", "Industry", "Address", "Rating", "Business_phone", "Website"]

    try:
        with open(file_path, mode="w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            
            # Write the header
            writer.writeheader()
            
            # Write the data
            for row in data:
                writer.writerow(row)
        
        print(f"Data successfully saved to {file_path}")
    
    except Exception as e:
        print(f"Error saving file: {e}")


async def scrape_lead_by_industry(industry: str, location: str) -> None:
    """Scrape multiple leads by industry from Google Maps."""
    manager = PlaywrightManager(headless=False)
    try:
        page = await manager.start_browser()
        await page.goto(BASE_URL)

        # Search for the query and location
        search_query = f"{industry} in {location}"
        await page.fill("input[name='q']", search_query)
        await page.keyboard.press("Enter")
        await page.wait_for_selector("div.ecceSd", timeout=5000)  # Wait for the scrollable container to load

        scrollable_container = page.locator("div.ecceSd").nth(1)
        previous_count = 0

        while True:
            # Scroll to the bottom of the container
            await page.evaluate(
                "(container) => container.scrollBy(0, container.scrollHeight)", 
                await scrollable_container.element_handle()
            )
            await asyncio.sleep(1)  # Wait for lazy-loaded content to load

            # Count the number of loaded business containers
            business_containers = page.locator("div.bfdHYd.Ppzolf.OFBs3e")
            current_count = await business_containers.count()

            # Break the loop if no new elements are loaded
            if current_count == previous_count:
                break
            previous_count = current_count
            
        print(f"Found {current_count} businesses for {industry} in {location}.")
        if current_count == 0:
            print("No businesses found.")
            return []
        else:
            business_list = []
                
            for i in range(current_count):
                container = business_containers.nth(i)
                try:
                    # Extract business details
                    company_name = (
                        await container.locator("div.qBF1Pd.fontHeadlineSmall").text_content()
                    ).strip() if await container.locator("div.qBF1Pd.fontHeadlineSmall").count() > 0 else "NA"

                    second_info_div = container.locator("div.W4Efsd").nth(2)
                    info_spans = await second_info_div.locator("span").all()
                    info_texts = [
                        (await span.text_content()).strip()
                        for span in info_spans
                        if (await span.text_content()).strip() and (await span.text_content()).strip() != "·"
                    ]

                    category = info_texts[0] if len(info_texts) > 0 else "NA"
                    address = info_texts[-1] if len(info_texts) > 1 else "NA"

                    rating_element = container.locator("span[aria-label*='stars']")
                    rating = (
                        (await rating_element.get_attribute("aria-label")).split(" stars")[0]
                        if await rating_element.count() > 0 else "NA"
                    )

                    phone_element = container.locator("span.UsdlK")
                    phone = (
                        (await phone_element.text_content()).strip()
                        if await phone_element.count() > 0 else "NA"
                    )

                    website_element = container.locator("a[aria-label^='Visit']")
                    website = (
                        await website_element.get_attribute("href")
                        if await website_element.count() > 0 else "NA"
                    )
                    # Normalize the URL if it starts with "/"
                    if website.startswith("/"):
                        website = f"https://www.googleadservices.com{website}"

                    # Append business details to the list
                    business_list.append({
                        "Name": company_name,
                        "Industry": category,
                        "Address": address,
                        "Rating": rating,
                        "Business_phone": phone,
                        "Website": website
                    })
                except Exception as e:
                    print(f"Error extracting data for a business: {e}")
            
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            file_path = os.path.join(OUTPUT_DIR, f"leads_{industry}_{location}.csv")
            save_to_csv(business_list, file_path)
                
    except Exception as e:
        raise RuntimeError(f"An error occurred while scraping: {e}")
        
    finally:
        await manager.stop_browser() 
        
        
if __name__ == "__main__":
    asyncio.run(scrape_lead_by_industry("private equity firms", "New York"))