import streamlit as st
import requests
import jwt
from streamlit_cookies_controller import CookieController
from config import BACKEND_URL

st.set_page_config(page_title="🔐 Login", layout="centered")
JWT_ALGORITHM = "HS256"

cookies = CookieController()
token = cookies.get("auth_token")

if token and "logged_in" not in st.session_state:
    try:
        # Decode token without verifying signature
        decoded = jwt.decode(token, options={"verify_signature": False})
        st.session_state.logged_in = True
        st.session_state.token = token
        st.session_state.username = decoded.get("username")
    except Exception:
        cookies.delete("auth_token")
        st.warning("Invalid or expired session. Please log in again.")

def login_form():
    st.markdown("""
        <style>
            .login-card {
                background-color: #f9f9f9;
                padding: 2rem;
                border-radius: 1rem;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
                max-width: 400px;
                margin: 4rem auto;
            }
            .login-title {
                text-align: center;
                font-size: 1.8rem;
                font-weight: bold;
                margin-bottom: 1rem;
            }
            .login-info {
                font-size: 0.9rem;
                color: #888;
                text-align: center;
                margin-bottom: 1.5rem;
            }
        </style>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.markdown('<div class="login-title">🔐 Welcome Back</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-info">Please log in to continue</div>', unsafe_allow_html=True)

        username = st.text_input("👤 Username")
        password = st.text_input("🔒 Password", type="password")
        login_btn = st.button("🚀 Login")

        st.markdown('</div>', unsafe_allow_html=True)

        if login_btn:
            if not username or not password:
                st.warning("Please enter both username and password.")
                return

            try:
                res = requests.post(f"{BACKEND_URL}/api/login", json={
                    "username": username,
                    "password": password
                })

                if res.status_code == 200:
                    token = res.json().get("token")
                    decoded = jwt.decode(token, options={"verify_signature": False})

                    st.session_state.logged_in = True
                    st.session_state.token = token
                    st.session_state.username = decoded.get("username")

                    cookies.set("auth_token", token)
                    st.session_state.just_logged_in = True
                    st.rerun()
                else:
                    st.error(f"❌ {res.json().get('error', 'Login failed.')}")
            except Exception as e:
                st.error(f"⚠️ Failed to connect to backend: {e}")

if st.session_state.get("just_logged_in"):
    st.session_state.pop("just_logged_in")
    st.success(f"✅ Logged in as **{st.session_state.username}**")

elif not st.session_state.get("logged_in"):
    login_form()
else:
    st.success(f"✅ You are logged in as **{st.session_state.username}**")
    if st.button("🔓 Logout"):
        st.session_state.clear()
        cookies.remove("auth_token")
        st.rerun()
