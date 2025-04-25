import time
import random
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

def human_like_typing(element, text):
    """Types text into an element with human-like timing variations"""
    for char in text:
        # Random delay before typing each character (varies more than previous implementation)
        time.sleep(random.uniform(0.05, 0.25))
        element.send_keys(char)
    
    # Add a pause after complete typing
    time.sleep(random.uniform(0.3, 0.7))

def random_scrolling(driver):
    """Performs random scrolling behavior to mimic human browsing"""
    scroll_amount = random.randint(100, 300)
    scroll_direction = random.choice([1, -1])  # 1 for down, -1 for up
    scroll_steps = random.randint(2, 5)
    
    for _ in range(scroll_steps):
        driver.execute_script(f"window.scrollBy(0, {scroll_amount * scroll_direction})")
        time.sleep(random.uniform(0.2, 1.0))

def random_mouse_movement(driver, element=None):
    """Simulates random mouse movements"""
    actions = ActionChains(driver)
    
    if element:
        # Move to target element with randomness
        actions.move_to_element_with_offset(
            element, 
            random.randint(-10, 10), 
            random.randint(-10, 10)
        )
    else:
        # Move randomly on the page
        viewport_width = driver.execute_script("return window.innerWidth")
        viewport_height = driver.execute_script("return window.innerHeight")
        
        x = random.randint(10, viewport_width - 10)
        y = random.randint(10, viewport_height - 10)
        
        actions.move_by_offset(x, y)
    
    actions.perform()
    time.sleep(random.uniform(0.1, 0.5))

def login_to_linkedin(driver, username, password):
    logging.info("🔐 Starting login process...")

    # Go to login page directly
    driver.get('https://www.linkedin.com/login')
    
    # Wait a bit with randomized time
    time.sleep(random.uniform(2.0, 4.0))
    
    # Perform some random mouse movements before login
    random_mouse_movement(driver)
    
    try:
        # Find the input fields
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'username'))
        )
        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'password'))
        )
        
        # First move to the username field
        random_mouse_movement(driver, username_field)
        
        # Click on the field
        username_field.click()
        time.sleep(random.uniform(0.3, 0.8))
        
        # Clear the fields with natural behavior
        username_field.clear()
        time.sleep(random.uniform(0.2, 0.5))
        
        # Type username with human-like timing
        human_like_typing(username_field, username)
        
        # Perform some realistic tab navigation
        if random.choice([True, False]):
            username_field.send_keys(Keys.TAB)
            time.sleep(random.uniform(0.3, 0.7))
        else:
            # Or click on password field
            random_mouse_movement(driver, password_field)
            password_field.click()
        
        time.sleep(random.uniform(0.3, 0.8))
        
        # Clear password field
        password_field.clear()
        time.sleep(random.uniform(0.2, 0.5))
        
        # Type password with human-like timing
        human_like_typing(password_field, password)
        
        # Find and click login button with human-like behavior
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@type="submit"]'))
        )
        
        # Move to login button
        random_mouse_movement(driver, login_button)
        time.sleep(random.uniform(0.5, 1.2))
        
        # Click the button
        login_button.click()
        
        # Wait for login to complete with randomized timing
        time.sleep(random.uniform(3.0, 5.0))

    except TimeoutException:
        logging.warning("⚠️ Login form not found. Aborting login.")
        return False

    # --- Checkpoint/Captcha Detection ---
    for _ in range(3):
        page_source = driver.page_source.lower()
        current_url = driver.current_url

        if any(x in current_url for x in ["checkpoint", "login"]) or \
           any(x in page_source for x in ["captcha", "verify your identity", "security verification"]):
            screenshot_path = f"output/login_checkpoint_{int(time.time())}.png"
            driver.save_screenshot(screenshot_path)
            logging.warning(f"⚠️ CAPTCHA or checkpoint detected. Screenshot saved: {screenshot_path}")
            print(f"\n⚠️ Manual login required. Please complete it in the browser.")
            input("⏸️ Press [ENTER] when you're logged in and see your feed...")

            if any(x in driver.current_url for x in ["feed", "mynetwork", "/in/"]):
                logging.info("✅ Manual login successful.")
                return True
            else:
                logging.warning("❌ Still not logged in.")
                time.sleep(2)
        else:
            # Perform random scrolling to mimic a human looking at the page
            random_scrolling(driver)
            break

    if any(x in driver.current_url for x in ["feed", "mynetwork", "/in/"]):
        logging.info("✅ Logged in programmatically.")
        
        # Simulate human behavior by scrolling a bit on the feed
        random_scrolling(driver)
        
        return True

    logging.error("❌ Login failed.")
    return False