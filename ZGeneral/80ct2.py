import streamlit as st
import pandas as pd
import json
import os
import time
from pathlib import Path
from rapidfuzz import fuzz
from pdf_to_descriptive_mapped_sections_improved import pdf_to_descriptive_mapped_sections

# ===============================
# STREAMLIT APP FOR PDF → MAPPED SECTIONS
# ===============================

st.set_page_config(page_title="PDF → Descriptive Sections", layout="wide")
st.title("📄 PDF to Descriptive Mapped Sections Analyzer")

# Sidebar for Uploads and Configuration
st.sidebar.header("Upload PDF")
uploaded_pdf = st.sidebar.file_uploader("Upload a PDF document", type=["pdf"])

output_dir = Path("logs")
output_dir.mkdir(exist_ok=True)

# Session state to keep track of progress
if "generated_result" not in st.session_state:
    st.session_state.generated_result = None

if uploaded_pdf:
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    pdf_folder = output_dir / timestamp
    pdf_folder.mkdir(parents=True, exist_ok=True)

    pdf_path = pdf_folder / uploaded_pdf.name
    with open(pdf_path, "wb") as f:
        f.write(uploaded_pdf.read())

    st.sidebar.success(f"✅ Uploaded {uploaded_pdf.name}")

    if st.sidebar.button("Generate Result"):
        with st.spinner("Processing PDF... this may take a few minutes depending on content size"):
            result = pdf_to_descriptive_mapped_sections(str(pdf_path), str(pdf_folder))
            st.session_state.generated_result = result
            st.success("✅ Processing complete!")

# Display results if available
if st.session_state.generated_result:
    result = st.session_state.generated_result
    mapped_sections = result.get("mapped_sections", {})

    st.subheader("📘 Extracted Sections and Mapping Results")

    data = []
    for key, val in mapped_sections.items():
        if val:
            data.append({
                "Section": key,
                "Semantic Score": val.get("semantic_score", "N/A"),
                "Fuzzy Score": val.get("fuzzy_score", "N/A"),
                "Content Snippet": val.get("content", "").strip()[:200] + "..."
            })
        else:
            data.append({
                "Section": key,
                "Semantic Score": "-",
                "Fuzzy Score": "-",
                "Content Snippet": "[No Match Found]"
            })

    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)

    # Section search functionality
    st.markdown("---")
    st.subheader("🔍 Search for a Section")
    search_query = st.text_input("Enter a section name or keyword")

    if search_query:
        found_match = False
        for sec_name, sec_data in mapped_sections.items():
            if sec_data and fuzz.WRatio(search_query, sec_name) > 75:
                found_match = True
                st.markdown(f"### 🧩 Matched Section: {sec_name}")
                st.markdown(f"**Semantic Score:** {sec_data.get('semantic_score', 'N/A')}  |  **Fuzzy Score:** {sec_data.get('fuzzy_score', 'N/A')}")
                st.text_area("Section Content", sec_data.get("content", "No content found."), height=300)
        if not found_match:
            st.warning("No matching section found.")

    # Option to download mapped data
    st.markdown("---")
    json_download = json.dumps(mapped_sections, indent=4, ensure_ascii=False)
    st.download_button(
        label="💾 Download Mapped Sections (JSON)",
        data=json_download,
        file_name=f"mapped_sections_{time.strftime('%Y%m%d-%H%M%S')}.json",
        mime="application/json"
    )
else:
    st.info("👆 Upload a PDF file in the sidebar to begin.")
