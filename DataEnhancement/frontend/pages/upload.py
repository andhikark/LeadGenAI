import streamlit as st
import pandas as pd
import os
import io

st.set_page_config(page_title="📤 Upload CSV & Normalize", layout="wide")
st.title("📤 Upload & Normalize Lead Data")
st.markdown("""
Welcome! This tool allows you to upload a CSV file and normalize its structure 
to match our standard format for further processing.
""")

# --- Standard column structure
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

        # --- Auto-mapping logic
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

            # Fill standard columns
            for col in STANDARD_COLUMNS:
                if column_mapping[col] and column_mapping[col] in df.columns:
                    normalized_df[col] = df[column_mapping[col]]
                else:
                    normalized_df[col] = ""

            # Include extra (non-standard) columns
            extra_columns = [col for col in df.columns if col not in column_mapping.values()]
            for col in extra_columns:
                normalized_df[col] = df[col]

            st.markdown("---")
            st.markdown("### ✅ Normalized Data Preview")
            st.dataframe(normalized_df.head(), use_container_width=True)

            csv_download = normalized_df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download Normalized CSV", data=csv_download, file_name="normalized_leads.csv", mime="text/csv")

    except Exception as e:
        st.error(f"❌ Failed to process file: {e}")
else:
    st.info("⬆️ Upload a CSV file to begin.")
