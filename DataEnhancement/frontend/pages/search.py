import streamlit as st
import pandas as pd
import requests

API_BASE = "http://localhost:5000/api" 

def find_website(company):
    try:
        res = requests.get(f"{API_BASE}/find-website", params={"company": company}, timeout=10)
        if res.status_code == 200:
            return res.json().get("website")
    except Exception as e:
        return f"Error: {str(e)}"
    return "Not found"

def get_revenue(company):
    try:
        res = requests.get(f"{API_BASE}/get-revenue", params={"company": company}, timeout=10)
        if res.status_code == 200:
            return res.json().get("estimated_revenue")
    except Exception as e:
        return f"Error: {str(e)}"
    return "Not found"

# === Streamlit UI ===
st.set_page_config(page_title="Company Info Search", layout="centered")
st.title("Search Placeholder")

company = st.text_input("Enter Company Name")

if st.button("Search") and company:
    with st.spinner("Fetching data..."):
        website = find_website(company)
        revenue = get_revenue(company)

        data = {
            "Company": company,
            "Website": website,
            "Estimated Revenue": revenue
        }

        df = pd.DataFrame([data])
        st.success("Result:")
        st.write(df)

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download CSV", csv, file_name=f"{company}_info.csv", mime="text/csv")
