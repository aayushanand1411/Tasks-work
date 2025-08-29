import streamlit as st
from docling.document_converter import DocumentConverter
import re

# Sections we want
TARGET_SECTIONS = [
    "Introduction",
    "Product Description",
    "Assumptions",
    "Hardware Requirements",
    "States and Mode of Software",
    "Detailed Software",
    "Timing Requirements"
]

def pdf_to_markdown(pdf_bytes):
    """Convert PDF (bytes) to Markdown using Docling"""
    converter = DocumentConverter()
    result = converter.convert(pdf_bytes)
    return result.document.export_to_markdown()

def extract_sections(markdown_text):
    """Extract only target sections into a dictionary"""
    sections_dict = {}

    # Regex to capture headings (# ...) and their content until the next heading
    pattern = r"^#\s*(.+?)\n([\s\S]*?)(?=\n#|\Z)"  
    matches = re.findall(pattern, markdown_text, flags=re.MULTILINE)

    for heading, content in matches:
        heading_clean = heading.strip()
        if heading_clean in TARGET_SECTIONS:
            sections_dict[heading_clean] = content.strip()

    # Ensure all target sections are in dict (even if missing from doc)
    for sec in TARGET_SECTIONS:
        sections_dict.setdefault(sec, "")

    return sections_dict

# ---------------- STREAMLIT APP ----------------
st.title("📑 SRS Section Extractor")

uploaded_file = st.file_uploader("Upload your SRS PDF", type=["pdf"])

if uploaded_file is not None:
    st.success("✅ File uploaded successfully")

    # Convert PDF -> Markdown
    with st.spinner("Converting PDF to Markdown..."):
        markdown_text = pdf_to_markdown(uploaded_file)

    # Extract sections
    srs_dict = extract_sections(markdown_text)

    st.subheader("Select Section to View")
    options = ["Show All"] + TARGET_SECTIONS
    section_choice = st.selectbox("Choose a section:", options)

    if section_choice == "Show All":
        for sec, content in srs_dict.items():
            st.markdown(f"### {sec}")
            if content:
                st.write(content)
            else:
                st.warning("⚠️ Section found but no content available.")
    else:
        st.markdown(f"### {section_choice}")
        if srs_dict[section_choice]:
            st.write(srs_dict[section_choice])
        else:
            st.warning("⚠️ Section found but no content available.")
