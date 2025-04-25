import os
import socket
import json
import logging
import time
import random
import uuid
from pathlib import Path
import undetected_chromedriver as uc  # Import undetected-chromedriver
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException

# Configurable constants
DEBUG_PORT_START = 9222
DEBUG_PORT_END = 9230
DEBUG_FOLDER = Path("backend/linkedinScraper/debug")
CHROME_INFO_FILE = DEBUG_FOLDER / "chrome_debug_info.json"

# Ensure debug folder exists
DEBUG_FOLDER.mkdir(parents=True, exist_ok=True)

def is_port_available(port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('localhost', port))
        s.close()
        return True
    except:
        return False

def find_available_port():
    for port in range(DEBUG_PORT_START, DEBUG_PORT_END + 1):
        if is_port_available(port):
            return port
    raise RuntimeError("No available Chrome debug ports found.")

def save_chrome_info(port, user_data_dir):
    chrome_info = {
        'port': port,
        'user_data_dir': str(user_data_dir)
    }
    with open(CHROME_INFO_FILE, 'w') as f:
        json.dump(chrome_info, f)
    logging.info(f"Chrome debugging info saved to {CHROME_INFO_FILE}")

def load_chrome_info():
    if CHROME_INFO_FILE.exists():
        try:
            with open(CHROME_INFO_FILE, 'r') as f:
                chrome_info = json.load(f)
            return chrome_info
        except Exception as e:
            logging.error(f"Error loading Chrome info: {e}")
    return None

def is_chrome_running(port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = s.connect_ex(('localhost', port))
        s.close()
        return result == 0
    except:
        return False

def is_driver_active(driver):
    if driver is None:
        return False
    try:
        _ = driver.current_url
        return True
    except:
        return False

def get_chrome_driver(headless=False, max_retries=3):
    """Use undetected-chromedriver to create a Chrome instance that bypasses bot detection"""
    
    # List of realistic user agents
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36 Edg/117.0.2045.47",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
    ]
    
    # Randomly select a user agent
    random_user_agent = random.choice(user_agents)
    
    for attempt in range(max_retries):
        port = find_available_port()
        # Use persistent profile directory
        user_data_dir = os.path.abspath("linkedin_profile_1")
        
        logging.info(f"Launching undetected Chrome with profile: {user_data_dir} (Attempt {attempt + 1})")
        
        try:
            # Configure options for undetected-chromedriver
            options = uc.ChromeOptions()
            
            # Add arguments similar to standard chrome options but with undetected-chromedriver
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-notifications")
            options.add_argument("--start-maximized")
            
            # Add user data dir
            options.add_argument(f"--user-data-dir={user_data_dir}")
            
            # Set a random user agent
            options.add_argument(f"--user-agent={random_user_agent}")
            
            # Create the driver with undetected-chromedriver
            if headless:
                driver = uc.Chrome(options=options, headless=True, use_subprocess=True)
            else:
                driver = uc.Chrome(options=options, use_subprocess=True)
            
            driver.implicitly_wait(10)
            save_chrome_info(port, user_data_dir)
            
            # Add random delay to mimic human startup
            time.sleep(random.uniform(1.0, 3.0))
            
            return driver
            
        except Exception as e:
            logging.error(f"Chrome launch failed (Attempt {attempt + 1}): {e}")
            time.sleep(random.uniform(2.0, 5.0))
    
    raise RuntimeError("All attempts to launch undetected Chrome driver failed.")