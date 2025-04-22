import requests
import time
import threading
from backend.scraper.linkedinScraper.utils.proxyUtils import generate_smartproxy_url

NUM_CLIENTS = 3  # Simulate 3 parallel clients per minute

seen_ips = set()
lock = threading.Lock()

def request_with_proxy(client_id):
    proxy_url = generate_smartproxy_url(client_id)  # uses sessionduration-1 and unique session
    proxy_auth_stripped = proxy_url.split("?")[0]

    proxies = {
        "http": proxy_auth_stripped,
        "https": proxy_auth_stripped
    }

    print(f"🧵 Client-{client_id} using proxy: {proxy_auth_stripped}")

    try:
        response = requests.get("https://api.ipify.org?format=json", proxies=proxies, timeout=10)
        response.raise_for_status()

        ip_data = response.json()
        ip = ip_data.get("ip", "⚠️ No IP returned")

        print(f"✅ Client-{client_id} got IP: {ip}")
        with lock:
            seen_ips.add(ip)

    except requests.exceptions.ProxyError as e:
        print(f"❌ Client-{client_id} Proxy error: {e}")
    except requests.exceptions.ConnectTimeout:
        print(f"❌ Client-{client_id} Timeout – Proxy may be down or blocked.")
    except Exception as e:
        print(f"❌ Client-{client_id} General error: {e}")

def test_proxy_rotation_parallel():
    print("🧪 Testing Smartproxy IP rotation with parallel clients (1-minute sessions)...\n")

    for minute in range(1, 6):  # Test over 5 minutes
        print(f"\n🕒 Minute {minute}: Spawning {NUM_CLIENTS} client threads...\n")
        threads = []

        for i in range(NUM_CLIENTS):
            # Ensure unique session ID across all minutes
            client_id = (minute - 1) * NUM_CLIENTS + i + 1
            t = threading.Thread(target=request_with_proxy, args=(client_id,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        if minute < 5:
            print("⏳ Waiting 60 seconds before next batch...\n")
            time.sleep(60)

    print(f"\n🔁 Total unique IPs: {len(seen_ips)}")
    print(f"🧠 IPs seen: {seen_ips}")

if __name__ == "__main__":
    test_proxy_rotation_parallel()
