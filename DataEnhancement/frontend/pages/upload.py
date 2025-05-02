
import streamlit as st
import pandas as pd
import requests
import time
import os
from dotenv import load_dotenv
from config import BACKEND_URL

# ✅ Simple login check using session state only
if not st.session_state.get("logged_in"):
    st.warning("🚫 Please log in first.")
    st.stop()

# ✅ Dummy auth headers (if backend still expects headers)
def auth_headers():
    return {}  # You can return {"Authorization": "dummy"} if needed by backend

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

def normalize_website(website):
    if pd.isna(website) or not isinstance(website, str):
        return ""
    return website.replace("http://", "").replace("https://", "").replace("www.", "").strip().lower()

def revenue_to_number(revenue_str):
    """Convert revenue like '500K', '2M', '$1.2B' to a numeric float."""
    if not isinstance(revenue_str, str) or revenue_str.strip() == "":
        return 0
    revenue_str = revenue_str.replace("$", "").replace(",", "").strip().upper()
    try:
        if revenue_str.endswith("B"):
            return float(revenue_str[:-1]) * 1_000_000_000
        elif revenue_str.endswith("M"):
            return float(revenue_str[:-1]) * 1_000_000
        elif revenue_str.endswith("K"):
            return float(revenue_str[:-1]) * 1_000
        else:
            return float(revenue_str)
    except ValueError:
        return 0


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
        st.markdown(f"**🧮 Selected Rows: `{selected_count}` / 100**")

        if selected_count > 100:
            st.error("❌ You can only select up to 100 rows for enhancement.")
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
        enhanced_df = base_df.copy()

        rows_to_update = base_df[base_df["Company"].notnull()].copy()

        # Step 1: GROWJO first
        growjo_request = [{"company": row["Company"]} for _, row in rows_to_update.iterrows()]
        growjo_response = requests.post(
            f"{BACKEND_URL}/api/scrape-growjo-batch",
            json=growjo_request,
            headers=auth_headers()
        )
        growjo_results = {item["company"].lower(): item for item in growjo_response.json() if "company" in item}

        # Step 2: Prepare Apollo fallback if revenue missing
        domains_for_apollo = []
        domains_for_person = []

        for _, row in rows_to_update.iterrows():
            company = row["Company"].lower()
            growjo = growjo_results.get(company, {})
            if not growjo.get("revenue"):
                website = normalize_website(growjo.get("website") or row.get("Website", ""))
                if website:
                    domains_for_apollo.append(website)
            if not growjo.get("decider_email") and not growjo.get("decider_name"):
                website = normalize_website(growjo.get("website") or row.get("Website", ""))
                if website:
                    domains_for_person.append(website)

        domains_for_apollo = list(set(domains_for_apollo))
        domains_for_person = list(set(domains_for_person))

        # Step 3: Call Apollo for missing revenue
        if domains_for_apollo:
            apollo_response = requests.post(
                f"{BACKEND_URL}/api/apollo-scrape-batch",
                json={"domains": domains_for_apollo}
            )
            apollo_lookup = {r["domain"]: r for r in apollo_response.json() if "domain" in r}
        else:
            apollo_lookup = {}

        # Step 4: Call Apollo People for missing decision makers
        if domains_for_person:
            apollo_person_response = requests.post(
                f"{BACKEND_URL}/api/find-best-person-batch",
                json={"domains": domains_for_person},
                headers=auth_headers()
            )
            apollo_person_lookup = {r["domain"]: r for r in apollo_person_response.json() if "domain" in r}
        else:
            apollo_person_lookup = {}

        # Step 5: Merge results
        for i, (idx, row) in enumerate(rows_to_update.iterrows()):
            company = row["Company"]
            company_lower = company.lower()
            growjo = growjo_results.get(company_lower, {})
            domain_apollo = normalize_website(growjo.get("website") or row.get("Website", ""))
            apollo = apollo_lookup.get(domain_apollo, {})
            apollo_person = apollo_person_lookup.get(domain_apollo, {})

            def fill(col, val1, val2):
                if not row[col].strip():
                    rows_to_update.at[idx, col] = val1 or val2 or ""

            fill("Revenue", growjo.get("revenue"), apollo.get("revenue"))
            rows_to_update.at[idx, "Rev Source"] = "Growjo" if growjo.get("revenue") else "Apollo"

            fill("Year Founded", growjo.get("founded"), apollo.get("founded_year"))  # still from original apollo
            fill("Website", growjo.get("website"), apollo.get("company_website"))
            fill("LinkedIn URL", growjo.get("decider_linkedin"), apollo_person.get("linkedin_url"))
            fill("Industry ", growjo.get("industry"), apollo.get("industry"))
            fill("Associated Members", growjo.get("associated_members"), "")  # no apollo fallback for this
            fill("Employees count", growjo.get("employees"), apollo.get("employee_count"))
            fill("Product/Service Category", growjo.get("category"), apollo.get("interests"))

            fill("Email", growjo.get("decider_email"), apollo_person.get("email") or apollo.get("decider_email"))
            fill("Phone Number", growjo.get("decider_phone"), apollo_person.get("phone_number") or apollo.get("decider_phone"))
            fill("Owner's LinkedIn", growjo.get("decider_linkedin"), apollo_person.get("linkedin_url") or apollo.get("decider_linkedin"))
            fill("Title", growjo.get("decider_title"), apollo_person.get("title") or apollo.get("decider_title"))

            # Combine Growjo and Apollo (Apollo Person only has first/last)
            decider_name = growjo.get("decider_name", "") or apollo.get("decider_name", "")
            first_name, last_name = split_name(decider_name)
            fill("First Name", first_name, apollo_person.get("first_name"))
            fill("Last Name", last_name, apollo_person.get("last_name"))

            progress_bar.progress((i + 1) / len(rows_to_update))
            status_text.text(f"Enhanced {i + 1} of {len(rows_to_update)} rows")

        enhanced_df.update(rows_to_update)

        elapsed_time = time.time() - start_time
        st.success(f"✅ Enrichment complete in {elapsed_time / 60:.2f} minutes!")
        st.dataframe(enhanced_df.head(), use_container_width=True)
        st.session_state.enriched_df = enhanced_df.copy()
        st.session_state.enrichment_done = True

        csv = enhanced_df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download Enhanced CSV", csv, file_name="enriched_leads.csv", mime="text/csv")


# Step 4: Filter Enhanced Data — OUTSIDE of the button block
    if st.session_state.get("enrichment_done") and "enriched_df" in st.session_state:
        st.markdown("### 🧹 Step 4: Filter Enhanced Data")

        enhanced_df = st.session_state.enriched_df.copy()

        filter_col1, filter_col2 = st.columns(2)
        with filter_col1:
            min_revenue = st.text_input("Minimum Revenue (e.g., 500K, 1M, 2B)", value="", key="min_revenue_input")
        with filter_col2:
            min_employees = st.number_input("Minimum Employees", value=0, step=1, key="min_employees_input")

        # Apply filtering
        enhanced_df["Revenue Numeric"] = enhanced_df["Revenue"].apply(revenue_to_number)
        enhanced_df["Employees Numeric"] = pd.to_numeric(enhanced_df["Employees count"], errors="coerce").fillna(0)

        filtered_df = enhanced_df.copy()

        if min_revenue:
            min_revenue_num = revenue_to_number(min_revenue)
            filtered_df = filtered_df[filtered_df["Revenue Numeric"] >= min_revenue_num]

        if min_employees > 0:
            filtered_df = filtered_df[filtered_df["Employees Numeric"] >= min_employees]

        # Show filtered result
        st.dataframe(filtered_df.drop(columns=["Revenue Numeric", "Employees Numeric"]).head(), use_container_width=True)

        if st.button("✅ Confirm Filtered Data"):
            st.session_state.filtered_df = filtered_df.drop(columns=["Revenue Numeric", "Employees Numeric"]).copy()
            st.success("✅ Filtered data confirmed! Proceed to select final rows.")



# Final Step: Select rows to download
if "filtered_df" in st.session_state:
    st.markdown("### 🖱️ Step 5: Select Final Rows to Download")

    filtered_data_with_select = st.session_state.filtered_df.copy()
    filtered_data_with_select["Select Row"] = False

    edited_final_df = st.data_editor(
        filtered_data_with_select,
        use_container_width=True,
        num_rows="dynamic",
        key="final_selection_editor",
        disabled=filtered_data_with_select.columns[:-1].tolist()
    )

    selected_final_df = edited_final_df[edited_final_df["Select Row"] == True].drop(columns=["Select Row"])

    st.markdown(f"**🧮 Selected Final Rows: `{len(selected_final_df)}`**")

    if len(selected_final_df) > 0:
        csv_final = selected_final_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Download Final Selected CSV",
            csv_final,
            file_name="final_selected_leads.csv",
            mime="text/csv"
        )
    else:
        st.info("Please select at least one row to enable download.")
