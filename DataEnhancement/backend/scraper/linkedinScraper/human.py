import time
import random

def human_delay(base=0.5, jitter=0.5):
    time.sleep(base + random.uniform(0, jitter))

# def human_scroll(driver, steps=3, max_offset=800):
#     for _ in range(steps):
#         offset = random.randint(200, max_offset)
#         driver.execute_script(f"window.scrollBy(0, {offset});")
#         human_delay(0.3, 0.7)

def human_type(element, text, typo_chance=0.02):
    for char in text:
        element.send_keys(char)
        if random.random() < typo_chance:
            element.send_keys(random.choice("abcdefghijklmnopqrstuvwxyz"))
            time.sleep(random.uniform(0.1, 0.3))
            element.send_keys("\b")
        time.sleep(random.uniform(0.05, 0.12))

# def human_click(driver, element):
#     actions = ActionChains(driver)
#     actions.move_to_element(element).pause(random.uniform(0.1, 0.4)).click().perform()

def randomize_viewport(driver):
    width = random.randint(1024, 1440)
    height = random.randint(768, 900)
    driver.set_window_size(width, height)
