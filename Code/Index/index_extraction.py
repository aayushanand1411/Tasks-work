import streamlit as st
import fitz  # PyMuPDF
import docx2txt
import re

# --- Extract text from PDF ---
def extract_text_from_pdf(file_bytes):
    text_pages = []
    pdf_doc = fitz.open(stream=file_bytes, filetype="pdf")
    for page in pdf_doc:
        text_pages.append(page.get_text())
    return text_pages

# --- Extract text from DOCX ---
def extract_text_from_docx(file_bytes):
    with open("temp.docx", "wb") as f:
        f.write(file_bytes)
    text = docx2txt.process("temp.docx")
    return text.split("\n\n")  # treat each section as a "page"

# --- Extract clean index entries ---
def find_index_entries(pages):
    index_list = []
    capture = False

    for page in pages:
        lines = page.split("\n")

        for line in lines:
            clean_line = line.strip()

            # Start capturing after TOC or Index heading
            if re.search(r'\b(table of contents|index)\b', clean_line, re.IGNORECASE):
                capture = True
                continue  # skip the heading itself

            if capture:
                # Stop capturing if revision history or references appear
                if re.search(r'\b(revision history|references)\b', clean_line, re.IGNORECASE):
                    return index_list

                # Skip empty or numeric-only lines
                if not clean_line or re.match(r'^\d+(\.\d+)*$', clean_line):
                    continue

                # Remove dotted leaders and page numbers at the end
                clean_line = re.sub(r'\.{2,}\s*\d+$', '', clean_line).strip()

                # Skip if still just a number
                if re.match(r'^\d+$', clean_line):
                    continue

                # Add if it's a meaningful title
                if len(clean_line) > 1:
                    index_list.append(clean_line)

    return index_list

# --- Streamlit UI ---
st.title("📑 Index Extractor App")

uploaded_file = st.file_uploader("Upload a PDF or Word file", type=["pdf", "docx"])

if uploaded_file:
    file_bytes = uploaded_file.read()

    if uploaded_file.name.lower().endswith(".pdf"):
        pages = extract_text_from_pdf(file_bytes)
    elif uploaded_file.name.lower().endswith(".docx"):
        pages = extract_text_from_docx(file_bytes)
    else:
        st.error("Unsupported file format!")
        st.stop()

    index_entries = find_index_entries(pages)

    if index_entries:
        st.success(f"✅ Found {len(index_entries)} index entries")
        st.write(index_entries)
    else:
        st.warning("⚠ No index page detected.")
