import os

# Load from environment or use default values
SMARTPROXY_USER = os.getenv("SMARTPROXY_USERNAME", "spvy76kscp")
SMARTPROXY_PASS = os.getenv("SMARTPROXY_PASSWORD", "bCE_1m7qkO0D1lzdjf")
SMARTPROXY_GATEWAY = os.getenv("SMARTPROXY_GATEWAY", "us.smartproxy.com")
SMARTPROXY_PORT = int(os.getenv("SMARTPROXY_PORT", 10001))

def generate_smartproxy_url(batch_index=None, client_id=None, duration=1):
    session_id = client_id if client_id is not None else f"batch-{batch_index}"
    username = f"user-{SMARTPROXY_USER}-sessionduration-{duration}-session-{session_id}"
    return f"http://{username}:{SMARTPROXY_PASS}@{SMARTPROXY_GATEWAY}:{SMARTPROXY_PORT}"

def format_proxy_for_chrome(proxy_url):
    """
    Extract and format proxy string for --proxy-server flag in Chrome.
    Returns: http://ip:port
    """
    proxy_no_auth = proxy_url.split("@")[-1]
    return f"http://{proxy_no_auth}"