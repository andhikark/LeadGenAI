import os
import time
import logging
import random
import re
import zipfile
import tempfile
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException
from dotenv import load_dotenv
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
# from selenium.webdriver.common.exceptions import TimeoutException

from ..utils.proxyUtils import generate_smartproxy_url, SMARTPROXY_USER, format_proxy_for_chrome
import json
import shutil
import socket
from urllib.parse import urlparse
# Load env variables (ensure LI_AT is available)
load_dotenv()

# Configurable constants
DEBUG_PORT_START = 9222
DEBUG_PORT_END = 9280
DEBUG_FOLDER = Path("backend/linkedinScraper/debug")
CHROME_INFO_FILE = DEBUG_FOLDER / "chrome_debug_info.json"
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) …",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)…",
    "Mozilla/5.0 (X11; Linux x86_64)…",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64)…"
]
# Ensure debug folder exists
DEBUG_FOLDER.mkdir(exist_ok=True)

def is_port_available(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind(('localhost', port))
            return True
        except OSError:
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

def create_proxy_auth_extension(proxy_host, proxy_port, proxy_user, proxy_pass):
    manifest_json = """
    {
      "version": "1.0.0",
      "manifest_version": 2,
      "name": "Smartproxy Auth Extension",
      "permissions": [
        "proxy", "tabs", "unlimitedStorage", "storage", "<all_urls>", "webRequest", "webRequestBlocking"
      ],
      "background": { "scripts": ["background.js"] }
    }
    """

    background_js = f"""
    var config = {{
        mode: "fixed_servers",
        rules: {{
            singleProxy: {{
                scheme: "http",
                host: "{proxy_host}",
                port: parseInt({proxy_port})
            }},
            bypassList: ["localhost"]
        }}
    }};
    chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{}});
    chrome.webRequest.onAuthRequired.addListener(
        function(details, callback) {{
            callback({{
                authCredentials: {{
                    username: "{proxy_user}",
                    password: "{proxy_pass}"
                }}
            }});
        }},
        {{urls: ["<all_urls>"]}},
        ["blocking"]
    );
    """

    plugin_file = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
    with zipfile.ZipFile(plugin_file, 'w') as zp:
        zp.writestr("manifest.json", manifest_json)
        zp.writestr("background.js", background_js)

    return plugin_file.name

def get_chrome_driver(li_at: str, client_id: str = "default", headless=False, max_retries=3):
    """
    Launch a Chrome WebDriver with proxy, li_at injection, and stealth settings.
    Requires li_at to be passed explicitly.
    """
    if not li_at:
        raise ValueError("❌ li_at must be provided")

    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    ]

    for attempt in range(max_retries):
        port = find_available_port()
        user_data_dir = "/tmp/linkedin_profile"
        if os.path.exists(user_data_dir):
            shutil.rmtree(user_data_dir, ignore_errors=True)
        os.makedirs(user_data_dir, exist_ok=True)

        chrome_options = Options()
        chrome_options.add_argument(f"--remote-debugging-port={port}")
        chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--proxy-bypass-list=127.0.0.1;localhost")
        chrome_options.add_argument(f"--user-agent={random.choice(user_agents)}")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)

        if headless:
            chrome_options.add_argument("--headless=new")

        # Ideally passed from outside or named per batch
        proxy_url = generate_smartproxy_url(client_id)
        parsed = urlparse(proxy_url)
        proxy_user = parsed.username
        proxy_pass = parsed.password
        proxy_host = parsed.hostname
        proxy_port = parsed.port

        plugin_path = create_proxy_auth_extension(proxy_host, proxy_port, proxy_user, proxy_pass)
        chrome_options.add_argument(f"--proxy-server={format_proxy_for_chrome(proxy_url)}")


        try:
            chrome_options.binary_location = "/usr/bin/chromium"
            service = Service("/usr/bin/chromedriver")
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.implicitly_wait(10)

            driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument", {
                    "source": "Object.defineProperty(navigator, 'webdriver', {get: () => false});"
                }
            )

            driver.execute_cdp_cmd("Network.enable", {})
            driver.execute_cdp_cmd("Network.setCookie", {
                "name":     "li_at",
                "value":    li_at.strip(),
                "domain":   ".linkedin.com",
                "path":     "/",
                "secure":   True,
                "httpOnly": True,
            })

            driver.get("https://www.linkedin.com/feed")
            time.sleep(2)
            if "login" in driver.current_url.lower():
                logging.warning("⚠️ Possibly not logged in after cookie injection.")
            else:
                logging.info("✅ Logged in; starting scraping.")

            return driver

        except Exception as e:
            logging.error(f"Chrome setup failed (attempt {attempt+1}): {e}", exc_info=True)
            shutil.rmtree(user_data_dir, ignore_errors=True)
            time.sleep(random.uniform(1.5, 3.0))

    raise RuntimeError("All attempts to launch Chrome driver failed.")


if __name__ == "__main__":
    li_at = os.getenv("LI_AT")
    if not li_at:
        print("❌ LI_AT not found in environment.")
    else:
        print(f"🍪 LI_AT cookie: {li_at[:6]}...{li_at[-6:]}")

    # Generate Smartproxy URL and extract IP info
    proxy_url = generate_smartproxy_url("manual_check")
    proxy_host = re.search(r'@(.+):', proxy_url).group(1)
    proxy_port = re.search(r':(\d+)', proxy_url).group(1)

    print(f"🌐 Smartproxy IP in use: {proxy_host}:{proxy_port}")