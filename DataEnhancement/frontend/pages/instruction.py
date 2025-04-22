import streamlit as st

st.set_page_config(page_title="🔐 How to Get li_at Cookie", layout="centered")
st.title("🔐 How to Get Your li_at Cookie from LinkedIn")

st.markdown("""
### 📝 Step-by-Step Instructions
1. **Login to LinkedIn** in your browser (preferably Chrome).
2. **Right-click** anywhere on the page and select **Inspect**, or press `Ctrl+Shift+I` (or `Cmd+Option+I` on Mac) to open **Developer Tools**.
3. Go to the **Application** tab (you may need to click `>>` to find it).
4. In the left sidebar under **Storage**, expand **Cookies** and click on `https://www.linkedin.com`.
5. In the cookie list, look for an entry named **`li_at`**.
6. 🔍 **Can’t find it?** Use the search bar in DevTools and type `li_at` to locate it faster.
7. **Copy the Value** of the `li_at` cookie.
8. **Paste** this value into the **LinkedIn Session (li_at)** input box in the app UI.

---

### ⚠️ Important Notes
- Your `li_at` is your **LinkedIn session token** — **keep it private**.
- If the browser tab where you’re logged into LinkedIn gets closed or the session expires, your `li_at` may no longer work.
- In that case, simply log in again and **repeat the steps above** to get a new token.
""")
