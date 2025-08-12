import streamlit as st
import fitz  # PyMuPDF
import docx2txt
import re

# ----------- Extract text from PDF -----------
def extract_text_from_pdf(file_bytes):
    text_pages = []
    pdf_doc = fitz.open(stream=file_bytes, filetype="pdf")
    for page in pdf_doc:
        text_pages.append(page.get_text())
    return text_pages

# ----------- Extract text from DOCX -----------
def extract_text_from_docx(file_bytes):
    with open("temp.docx", "wb") as f:
        f.write(file_bytes)
    text = docx2txt.process("temp.docx")
    return text.split("\n\n")  # simulate pages

# ----------- Extract clean index entries -----------
def find_index_entries(pages):
    index_list = []
    capture = False

    for page in pages:
        lines = page.split("\n")

        for line in lines:
            clean_line = line.strip()

            # Start capturing after TOC or Index
            if re.search(r'\b(table of contents|index)\b', clean_line, re.IGNORECASE):
                capture = True
                continue

            if capture:
                # Stop capturing if revision history or references appear
                if re.search(r'\b(revision history|references)\b', clean_line, re.IGNORECASE):
                    return index_list

                # Skip empty or numeric-only lines
                if not clean_line or re.match(r'^\d+(\.\d+)*$', clean_line):
                    continue

                # Remove dotted leaders + page numbers
                clean_line = re.sub(r'\.{2,}\s*\d+$', '', clean_line).strip()

                # Remove leading numbering like "1.", "1.1.", "."
                clean_line = re.sub(r'^\.*\s*', '', clean_line)  # remove stray starting dots
                clean_line = re.sub(r'^\d+(\.\d+)*\s*\.?\s*', '', clean_line).strip()

                if re.match(r'^\d+$', clean_line):
                    continue

                if len(clean_line) > 1:
                    index_list.append(clean_line)

    return index_list


# ----------- Expected list -----------
expected_list = [
    "Introduction",
    "Purpose",
    "Scope",
    "Product perspective",
    "Product functions",
    "User characteristics",
    "Limitations",
    "Assumptions and dependencies",
    "Definitions",
    "Acronyms and abbreviations",
    "Requirements",
    "External interfaces",
    "Functions",
    "Usability requirements",
    "Performance requirements",
    "Logical database requirements",
    "Design constraints",
    "Standards compliance",
    "Software system attributes",
    "Verification",
    "Supporting information"
]

# ----------- Streamlit UI -----------
st.title("📑 Index Extractor & Comparator")

uploaded_file = st.file_uploader("Upload a PDF or Word file", type=["pdf", "docx"])

if uploaded_file:
    file_bytes = uploaded_file.read()

    # Detect and extract
    if uploaded_file.name.lower().endswith(".pdf"):
        pages = extract_text_from_pdf(file_bytes)
    elif uploaded_file.name.lower().endswith(".docx"):
        pages = extract_text_from_docx(file_bytes)
    else:
        st.error("Unsupported file format!")
        st.stop()

    # Extract index
    index_entries = find_index_entries(pages)

    if index_entries:
        st.success(f"✅ Found {len(index_entries)} index entries")
        st.write(index_entries)

        # ---- Compare with expected ----
        matches = [item for item in index_entries if item in expected_list]
        missing = [item for item in expected_list if item not in index_entries]
        extra = [item for item in index_entries if item not in expected_list]

        st.subheader("📊 Comparison Results")
        st.write(f"✅ Matches: {len(matches)} / {len(expected_list)}")
        st.write(f"🔍 Missing: {len(missing)}")
        st.write(missing)
        st.write(f"➕ Extra: {len(extra)}")
        st.write(extra)

    else:
        st.warning("⚠ No index page detected.")
