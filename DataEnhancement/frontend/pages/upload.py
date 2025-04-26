
import streamlit as st
from streamlit_cookies_controller import CookieController
import pandas as pd
import requests
import jwt
import time
from config import BACKEND_URL


JWT_SECRET = "fallback_secret_change_me_in_production"
JWT_ALGORITHM = "HS256"

cookies = CookieController()
token = cookies.get("auth_token")

if token and "logged_in" not in st.session_state:
    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        st.session_state.token = token
        st.session_state.logged_in = True
        st.session_state.username = decoded.get("username")
    except jwt.ExpiredSignatureError:
        cookies.delete("auth_token")
        st.warning("Session expired.")
        st.stop()
    except jwt.InvalidTokenError:
        cookies.delete("auth_token")
        st.warning("Invalid session.")
        st.stop()

if not st.session_state.get("logged_in"):
    st.warning("Please log in first.")
    st.stop()

def auth_headers():
    token = st.session_state.get("token")
    if not token:
        st.error("Missing token. Please log in again.")
        st.stop()
    return {"Authorization": f"Bearer {token}"}

def normalize_name(name):
    return name.strip().lower().replace(" ", "").replace("-", "").replace(".", "") if name else ""

def split_name(full_name):
    parts = full_name.strip().split()
    if len(parts) == 0:
        return "", ""
    elif len(parts) == 1:
        return parts[0], ""
    else:
        return parts[0], " ".join(parts[1:])

st.set_page_config(page_title="📤 Upload CSV & Normalize", layout="wide")
st.title("📤 Upload & Normalize Lead Data")
st.markdown("""
Welcome! This tool allows you to upload a CSV file and normalize its structure 
to match our standard format, and enrich it with Apollo, LinkedIn, and Growjo data.
""")

if "normalized_df" not in st.session_state:
    st.session_state.normalized_df = None
if "confirmed_selection_df" not in st.session_state:
    st.session_state.confirmed_selection_df = None

STANDARD_COLUMNS = [
    'Company', 'City', 'State', 'First Name', 'Last Name', 'Email', 'Title', 'Website',
    'LinkedIn URL', 'Industry ', 'Revenue', 'Product/Service Category',
    'Business Type (B2B, B2B2C) ', 'Associated Members', 'Employees count', 'Rev Source', 'Year Founded',
    "Owner's LinkedIn", 'Owner Age', 'Phone Number', 'Additional Notes', 'Score',
    'Email customization #1', 'Subject Line #1', 'Email Customization #2', 'Subject Line #2',
    'LinkedIn Customization #1', 'LinkedIn Customization #2', 'Reasoning for r//y/g'
]

st.markdown("### 📎 Step 1: Upload Your CSV")
uploaded_file = st.file_uploader("Choose a CSV file to upload", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        st.success("✅ File uploaded successfully!")

        st.markdown("### ✅ Step 2: Select Rows to Enhance")
        df['Select Row'] = False
        edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic", key="editable_df", disabled=df.columns[:-1].tolist())
        selected_df = pd.DataFrame(edited_df)
        rows_to_enhance = selected_df[selected_df['Select Row'] == True].drop(columns=['Select Row'])
        selected_count = len(rows_to_enhance)
        st.markdown(f"**🧮 Selected Rows: `{selected_count}` / 10**")

        if selected_count > 10:
            st.error("❌ You can only select up to 10 rows for enhancement.")
            st.button("✅ Confirm Selected Rows", disabled=True)
        else:
            if st.button("✅ Confirm Selected Rows"):
                if selected_count > 0:
                    st.session_state.confirmed_selection_df = rows_to_enhance.copy()
                    st.success(f"{selected_count} rows confirmed for normalization and enrichment.")
                else:
                    st.session_state.confirmed_selection_df = df.copy()
                    st.info("No rows selected. Defaulting to all rows.")

    except Exception as e:
        st.error(f"❌ Failed to process file: {e}")

if st.session_state.confirmed_selection_df is not None:
    data_for_mapping = st.session_state.confirmed_selection_df.copy()

    st.markdown("### 🛠 Step 3: Map Your Columns")
    auto_mapping = {col: col for col in STANDARD_COLUMNS if col in data_for_mapping.columns}
    column_mapping = {}

    st.markdown("#### 🔗 Map your CSV columns to our standard format:")
    for target in STANDARD_COLUMNS:
        st.markdown(f"<div style='margin-bottom: -0.5rem; margin-top: 1rem; font-weight: 600;'>{target}</div>", unsafe_allow_html=True)
        col1, col2 = st.columns([1, 2])
        with col1:
            st.text("From your file")
        with col2:
            default = auto_mapping.get(target, "-- None --")
            selected = st.selectbox(" ", ["-- None --"] + list(data_for_mapping.columns), index=(["-- None --"] + list(data_for_mapping.columns)).index(default) if default != "-- None --" else 0, key=target, label_visibility="collapsed")
        column_mapping[target] = selected if selected != "-- None --" else None

    if st.button("🔄 Normalize CSV"):
        normalized_df = pd.DataFrame()
        for col in STANDARD_COLUMNS:
            if column_mapping[col] and column_mapping[col] in data_for_mapping.columns:
                normalized_df[col] = data_for_mapping[column_mapping[col]]
            else:
                normalized_df[col] = ""

        mapped_input_columns = set(column_mapping.values())
        extra_columns = [col for col in data_for_mapping.columns if col not in mapped_input_columns and col != "Select Row"]
        for col in extra_columns:
            normalized_df[col] = data_for_mapping[col]

        st.session_state.normalized_df = normalized_df.copy()
        st.markdown("### ✅ Normalized Data Preview")
        st.dataframe(normalized_df.head(), use_container_width=True)

        st.download_button("📥 Download Normalized CSV", data=normalized_df.to_csv(index=False).encode("utf-8"), file_name="normalized_leads.csv", mime="text/csv")

if st.session_state.normalized_df is not None and st.session_state.confirmed_selection_df is not None:
    if st.button("🚀 Enrich Data"):
        st.markdown("⏳ Please wait while we enrich company data...")
        start_time = time.time()
        progress_bar = st.progress(0)
        status_text = st.empty()

        base_df = st.session_state.normalized_df.copy()
        confirmed_df = st.session_state.confirmed_selection_df.copy()
        enhanced_df = base_df.copy()

        mask = base_df["Company"].isin(confirmed_df["Company"])
        rows_to_update = enhanced_df[mask].copy()

        apollo_domains = rows_to_update["Website"].dropna().unique().tolist()
        apollo_domains = [w.replace("http://", "").replace("https://", "").replace("www.", "").strip().lower() for w in apollo_domains]

        apollo_response = requests.post(
            f"{BACKEND_URL}/api/apollo-scrape-batch",
            json={"domains": apollo_domains}
        )
        apollo_lookup = {r["domain"]: r for r in apollo_response.json() if "domain" in r}

        # Prepare list for batch call
        growjo_request = [{"company": row["Company"]} for idx, row in rows_to_update.iterrows()]

        # Send batch request
        growjo_response = requests.post(
            f"{BACKEND_URL}/api/scrape-growjo-batch",
            json=growjo_request,
            headers=auth_headers()
        )
        growjo_results = {item["company"].lower(): item for item in growjo_response.json() if "company" in item}


        for i, (idx, row) in enumerate(rows_to_update.iterrows()):
            domain_appolo = row["Website"].replace("http://", "").replace("https://", "").replace("www.", "").strip().lower()
            domain = row["Company"]
            apollo = apollo_lookup.get(domain_appolo, {})
            growjo = growjo_results.get(domain.lower(), {})


            if not row["Revenue"].strip():
                revenue = apollo.get('annual_revenue_printed', '')
                if revenue:
                    rows_to_update.at[idx, "Revenue"] = f"${revenue}"
                    rows_to_update.at[idx, "Rev Source"] = "Apollo"
                else:
                    rows_to_update.at[idx, "Revenue"] = ""
                    rows_to_update.at[idx, "Rev Source"] = ""

            if not row["Year Founded"].strip():
                rows_to_update.at[idx, "Year Founded"] = apollo.get("founded_year", "")
            if not row["Website"].strip():
                rows_to_update.at[idx, "Website"] = apollo.get("website_url", "")
            if not row["LinkedIn URL"].strip():
                rows_to_update.at[idx, "LinkedIn URL"] = apollo.get("linkedin_url", "") 
            if not row["Industry "].strip():
                rows_to_update.at[idx, "Industry "] = ""
            if not row["Associated Members"].strip():
                rows_to_update.at[idx, "Associated Members"] = ""
            if not row["Employees count"].strip():
                rows_to_update.at[idx, "Employees count"] = apollo.get("employee_count", "")
            if not row["Product/Service Category"].strip():
                rows_to_update.at[idx, "Product/Service Category"] = apollo.get("keywords", "")

            if not row["Email"].strip() and growjo.get("decider_email"):
                rows_to_update.at[idx, "Email"] = growjo.get("decider_email", "")
            if not row["Phone Number"].strip() and growjo.get("decider_phone"):
                rows_to_update.at[idx, "Phone Number"] = growjo.get("decider_phone", "")
            if not row["Owner's LinkedIn"].strip() and growjo.get("decider_linkedin"):
                rows_to_update.at[idx, "Owner's LinkedIn"] = growjo.get("decider_linkedin", "")
            if not row["Title"].strip() and growjo.get("decider_title"):
                rows_to_update.at[idx, "Title"] = growjo.get("decider_title", "")
            if not row["Industry "].strip() and growjo.get("industry"):
                rows_to_update.at[idx, "Industry "] = growjo.get("industry", "")

            decider_name = growjo.get("decider_name", "")
            first_name, last_name = split_name(decider_name)

            if not row["First Name"].strip():
                rows_to_update.at[idx, "First Name"] = first_name
            if not row["Last Name"].strip():
                rows_to_update.at[idx, "Last Name"] = last_name

            progress_bar.progress((i + 1) / len(rows_to_update))
            status_text.text(f"Enhanced {i + 1} of {len(rows_to_update)} rows")

        enhanced_df.update(rows_to_update)

        end_time = time.time()
        elapsed_time = end_time - start_time

        minutes = elapsed_time / 60
        st.success(f"✅ Enrichment complete in {minutes:.2f} minutes!")
        st.dataframe(enhanced_df.head(), use_container_width=True)
        csv = enhanced_df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download Enhanced CSV", csv, file_name="apollo_linkedin_growjo_enriched.csv", mime="text/csv")
