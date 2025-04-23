import os
import random
import time
from dotenv import load_dotenv

load_dotenv()

import os
import random

def generate_proxy_url(session_id="client01"):
    """
    Generates a Decodo proxy URL using one of 10 available ports (10001–10010).
    Format: https://<username>:<password>@<gateway>:<port>
    """
    user = os.getenv("SMARTPROXY_USERNAME")  # or rename to DECODO_USERNAME
    pwd = os.getenv("SMARTPROXY_PASSWORD")   # or rename to DECODO_PASSWORD
    gateway = os.getenv("SMARTPROXY_GATEWAY", "us.decodo.com")
    
    # Randomize across 10 sticky ports: 10001–10010
    port = random.randint(10001, 10010)

    return f"https://{user}:{pwd}@{gateway}:{port}"


async def inject_li_at_cookie(page, li_at):
    await page.add_cookie(
        name="li_at",
        value=li_at,
        domain=".linkedin.com",
        path="/",
        http_only=True,
        secure=True
    )

def human_delay(min_sec=1.5, max_sec=2.5):
    time.sleep(random.uniform(min_sec, max_sec))
