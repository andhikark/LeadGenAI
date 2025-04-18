import pandas as pd
import json
import logging
import re
from pathlib import Path

# Define debug folder using pathlib
DEBUG_FOLDER = Path.cwd() / "debug"
DEBUG_FOLDER.mkdir(exist_ok=True)

INDUSTRY_MAPPINGS_FILE = DEBUG_FOLDER / 'industry_mappings.json'

def read_csv(file_path):
    """Read a CSV file into a DataFrame."""
    try:
        df = pd.read_csv(file_path)
        logging.info(f"Successfully read CSV file: {file_path}")
        return df
    except Exception as e:
        logging.error(f"Error reading CSV file {file_path}: {e}")
        raise

def save_screenshot(driver, filename):
    """Save a screenshot to the debug folder."""
    filepath = DEBUG_FOLDER / filename
    driver.save_screenshot(str(filepath))
    logging.info(f"Screenshot saved to {filepath}")
    return filepath

def save_page_source(driver, filename):
    """Save the current page source to the debug folder."""
    filepath = DEBUG_FOLDER / filename
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    logging.info(f"Page source saved to {filepath}")
    return filepath

def load_industry_mappings():
    """Load industry code-to-name mappings from JSON file or return default."""
    default_mappings = {
        "132": "Environmental Health & Safety Training",
        "124": "Health, Wellness & Fitness",
        "96": "Management Consulting",
        "4": "Computer Software",
        "105": "E-Learning",
        "43": "Financial Services",
        "118": "Information Technology & Services",
        "27": "Retail",
        "33": "Sports"
    }
    
    try:
        if INDUSTRY_MAPPINGS_FILE.exists():
            logging.info(f"Loading industry mappings from {INDUSTRY_MAPPINGS_FILE}")
            with open(INDUSTRY_MAPPINGS_FILE, 'r') as f:
                mappings = json.load(f)
            logging.info(f"Loaded {len(mappings)} industry mappings")
            return mappings
        else:
            logging.info("Industry mappings file not found. Using default mappings.")
            return default_mappings
    except Exception as e:
        logging.warning(f"Error loading industry mappings: {e}")
        logging.info("Using default industry mappings instead")
        return default_mappings

def save_industry_mappings(mappings: dict):
    """Save industry code-to-name mappings to JSON file."""
    try:
        with open(INDUSTRY_MAPPINGS_FILE, 'w') as f:
            json.dump(mappings, f, indent=2, sort_keys=True)
        logging.info(f"Saved {len(mappings)} industry mappings to {INDUSTRY_MAPPINGS_FILE}")
    except Exception as e:
        logging.warning(f"Error saving industry mappings: {e}")

def extract_industry_mappings_from_page(page_source: str, existing_mappings: dict) -> int:
    """
    Extract new industry mappings from HTML and update the provided dictionary.

    Returns:
        int: Number of new mappings added.
    """
    pattern = r'"name":"([^"]+)","entityUrn":"urn:li:fsd_industry:(\d+)"'
    matches = re.findall(pattern, page_source)
    new_count = 0

    for name, code in matches:
        if code not in existing_mappings or existing_mappings[code] != name:
            existing_mappings[code] = name
            new_count += 1
            logging.info(f"Added/updated industry mapping: {code} -> {name}")
    
    if new_count > 0:
        save_industry_mappings(existing_mappings)
        logging.info(f"Added {new_count} new industry mappings from page")

    return new_count
