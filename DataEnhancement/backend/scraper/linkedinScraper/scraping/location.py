import logging
from ..utils.locationUtils import city_names_match, state_in_text
from selenium.webdriver.common.by import By

def validate_location(driver, links, city, state):
    city = city.strip().lower() if city else ""
    state = state.strip().lower() if state else ""

    for link in links[:5]:
        try:
            container = link
            for _ in range(5):
                container = container.find_element(By.XPATH, "./..")
                text = container.text.lower()
                
                # Try to split "city, state" if exists
                parts = [part.strip() for part in text.split(",")]
                city_text = parts[0] if len(parts) > 0 else ""
                state_text = parts[1] if len(parts) > 1 else text  # fallback to whole

                city_match = city_names_match(city, city_text)
                state_match = state_in_text(state, state_text)

                logging.debug(f"Comparing: input ({city}, {state}) vs snippet ({city_text}, {state_text})")

                if city_match and state_match:
                    return link, "City & state matched"
                elif city_match or state_match:
                    return link, "Partial match"
        except Exception as e:
            logging.warning(f"Error validating location: {e}")
    return links[0] if links else None, "City & state mismatch"
