
import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="📤 Upload CSV & Normalize", layout="wide")
st.title("📤 Upload & Normalize Lead Data")
st.markdown("""
Welcome! This tool allows you to upload a CSV file and normalize its structure 
to match our standard format, and enrich it with Apollo data.
""")

# Initialize session state for normalized_df
if "normalized_df" not in st.session_state:
    st.session_state.normalized_df = None

STANDARD_COLUMNS = [
    'Company', 'City', 'State', 'First Name', 'Last Name', 'Email', 'Title', 'Website',
    'LinkedIn URL', 'Industry ', 'Revenue', 'Product/Service Category',
    'Business Type (B2B, B2B2C) ', 'Employees', 'Rev Source', 'Year Founded',
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

        st.markdown("### 🛠 Step 2: Map Your Columns")
        st.write("We detected the following columns in your file:")
        st.dataframe(df.head(), use_container_width=True)

        auto_mapping = {col: col for col in STANDARD_COLUMNS if col in df.columns}
        column_mapping = {}

        st.markdown("#### 🔗 Map your CSV columns to our standard format:")

        for target in STANDARD_COLUMNS:
            st.markdown(f"<div style='margin-bottom: -0.5rem; margin-top: 1rem; font-weight: 600;'>{target}</div>", unsafe_allow_html=True)
            col1, col2 = st.columns([1, 2])
            with col1:
                st.text("From your file")
            with col2:
                default = auto_mapping.get(target, "-- None --")
                selected = st.selectbox(" ", ["-- None --"] + list(df.columns), index=(["-- None --"] + list(df.columns)).index(default) if default != "-- None --" else 0, key=target, label_visibility="collapsed")
            column_mapping[target] = selected if selected != "-- None --" else None

        if st.button("🔄 Normalize CSV"):
            normalized_df = pd.DataFrame()

            for col in STANDARD_COLUMNS:
                if column_mapping[col] and column_mapping[col] in df.columns:
                    normalized_df[col] = df[column_mapping[col]]
                else:
                    normalized_df[col] = ""

            extra_columns = [col for col in df.columns if col not in column_mapping.values()]
            for col in extra_columns:
                normalized_df[col] = df[col]

            st.session_state.normalized_df = normalized_df

            st.markdown("### ✅ Normalized Data Preview")
            st.dataframe(normalized_df.head(), use_container_width=True)

            csv_download = normalized_df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download Normalized CSV", data=csv_download, file_name="normalized_leads.csv", mime="text/csv")

    except Exception as e:
        st.error(f"❌ Failed to process file: {e}")
else:
    st.info("⬆️ Upload a CSV file to begin.")

# Apollo Enhancement Section (visible after normalization)
if st.session_state.normalized_df is not None:
    if st.button("🚀 Enhance with Apollo Data"):
        st.markdown("⏳ Please wait while we enrich company data...")
        progress_bar = st.progress(0)
        status_text = st.empty()

        enhanced_df = st.session_state.normalized_df.copy()
        domains = enhanced_df["Company"].dropna().unique().tolist()

        # Fix: ensure string dtype for enriched columns
        columns_to_fix = ["Revenue", "Year Founded", "Website", "LinkedIn URL", "Company"]
        for col in columns_to_fix:
            if col in enhanced_df.columns:
                enhanced_df[col] = enhanced_df[col].astype(str)

        try:
            response = requests.post(
                "http://localhost:5000/api/apollo-info",
                json=[{"domain": d} for d in domains],
                timeout=60
            )

            if response.status_code == 200:
                enrichment_results = response.json()
                enrichment_lookup = {item["domain"]: item for item in enrichment_results if "domain" in item}

                for i, (idx, row) in enumerate(enhanced_df.iterrows()):
                    domain = row["Company"]
                    enriched = enrichment_lookup.get(domain, {})

                    if enriched:
                        if not row["Revenue"] or str(row["Revenue"]).strip() == "":
                            enhanced_df.at[idx, "Revenue"] = enriched.get("annual_revenue_printed", "")

                        if not row["Year Founded"] or str(row["Year Founded"]).strip() == "":
                            enhanced_df.at[idx, "Year Founded"] = enriched.get("founded_year", "")

                        if not row["Website"] or str(row["Website"]).strip() == "":
                            enhanced_df.at[idx, "Website"] = enriched.get("website_url", "")

                        if not row["LinkedIn URL"] or str(row["LinkedIn URL"]).strip() == "":
                            enhanced_df.at[idx, "LinkedIn URL"] = enriched.get("linkedin_url", "")

                        if not row["Company"] or str(row["Company"]).strip() == "":
                            enhanced_df.at[idx, "Company"] = enriched.get("name", domain)

                    progress = int((i + 1) / len(enhanced_df) * 100)
                    progress_bar.progress(progress)
                    status_text.text(f"Enhancing row {i + 1} of {len(enhanced_df)}...")

                st.success("✅ Enrichment complete!")
                st.markdown("### ✅ Apollo Enriched Data Preview")
                st.dataframe(enhanced_df.head(), use_container_width=True)

                enriched_csv = enhanced_df.to_csv(index=False).encode("utf-8")
                st.download_button("📥 Download Enriched CSV", enriched_csv, file_name="apollo_enriched_leads.csv", mime="text/csv")

            else:
                st.error(f"❌ Apollo API returned {response.status_code}: {response.text}")

        except Exception as e:
            st.error(f"❌ Failed to enrich data: {e}")
