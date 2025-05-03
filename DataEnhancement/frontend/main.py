import streamlit as st

st.set_page_config(page_title="Company Intelligence Tool", layout="wide")

# ✅ Simple login check
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("🚫 Please log in first.")
    st.stop()

st.sidebar.title("🔍 Navigation")
st.sidebar.markdown("Choose a feature to use:")

# ✅ Optional navigation (remove auto-switch)
if st.sidebar.button("📤 Upload CSV"):
    st.switch_page("pages/upload.py")
