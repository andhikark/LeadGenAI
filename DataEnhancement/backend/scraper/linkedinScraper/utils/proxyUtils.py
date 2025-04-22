import os
from urllib.parse import urlparse

# Load from environment or use default values
SMARTPROXY_USER    = os.getenv("SMARTPROXY_USERNAME", "spgcen825j")
SMARTPROXY_PASS    = os.getenv("SMARTPROXY_PASSWORD", "ebG_7Etrvh4Dg8zQ7w")
SMARTPROXY_GATEWAY = os.getenv("SMARTPROXY_GATEWAY", "us.smartproxy.com")
SMARTPROXY_PORT    = int(os.getenv("SMARTPROXY_PORT", 10001))

def generate_smartproxy_url(client_id: str, duration_hours: int = 1) -> str:
    """
    Build a Smartproxy HTTP URL with a sticky session.
    - client_id: unique identifier for this session (e.g. 'client01_batch1')
    - duration_hours: how many hours before Smartproxy rotates your IP
    """
    session_segment = client_id.replace(" ", "_")
    user_segment = f"user-{SMARTPROXY_USER}-sessionduration-{duration_hours}-session-{session_segment}"
    return f"http://{user_segment}:{SMARTPROXY_PASS}@{SMARTPROXY_GATEWAY}:{SMARTPROXY_PORT}"

def format_proxy_for_chrome(proxy_url: str) -> str:
    """
    Extract host:port from an auth‑style proxy URL for Chrome's --proxy-server flag.
    Example:
      input:  http://user:pass@us.smartproxy.com:10001
      output: http://us.smartproxy.com:10001
    """
    parsed = urlparse(proxy_url)
    scheme = parsed.scheme or "http"
    host   = parsed.hostname
    port   = parsed.port
    ip_display = f"{host}:{port}"
    print(f"🌐 Smartproxy IP in use: {ip_display}")
    return f"{scheme}://{host}:{port}"

def build_requests_proxies(proxy_url: str) -> dict:
    """
    If you ever mix in Python requests, use this:
      proxies = build_requests_proxies(proxy_url)
      requests.get(..., proxies=proxies)
    """
    return {
        "http":  proxy_url,
        "https": proxy_url,
    }