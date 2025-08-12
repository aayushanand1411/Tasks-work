import fitz  # PyMuPDF
import docx2txt
import re
import tkinter as tk
from tkinter import filedialog

# --- Reference list ---
reference_list = [
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

# --- Extract text from PDF ---
def extract_text_from_pdf(file_path):
    text_pages = []
    pdf_doc = fitz.open(file_path)
    for page in pdf_doc:
        text_pages.append(page.get_text())
    return text_pages

# --- Extract text from DOCX ---
def extract_text_from_docx(file_path):
    text = docx2txt.process(file_path)
    return text.split("\n\n")

# --- Extract clean index entries ---
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
                # Stop capturing when these appear
                if re.search(r'\b(revision history|references)\b', clean_line, re.IGNORECASE):
                    return index_list

                if not clean_line or re.match(r'^\d+(\.\d+)*$', clean_line):
                    continue

                # Remove dotted leaders and page numbers
                clean_line = re.sub(r'\.{2,}\s*\d+$', '', clean_line).strip()

                # Remove stray starting dots
                clean_line = re.sub(r'^\.*\s*', '', clean_line)

                # Remove numbering like 1., 1.1., etc.
                clean_line = re.sub(r'^\d+(\.\d+)*\s*\.?\s*', '', clean_line).strip()

                if len(clean_line) > 1:
                    index_list.append(clean_line)
    return index_list

# --- Compare with reference list ---
def compare_lists(extracted, reference):
    extracted_set = set(map(str.lower, extracted))
    reference_set = set(map(str.lower, reference))

    matched_lower = extracted_set & reference_set
    extra_lower = extracted_set - reference_set
    missing_lower = reference_set - extracted_set

    matched = [item for item in extracted if item.lower() in matched_lower]
    extras = [item for item in extracted if item.lower() in extra_lower]
    missing = [item for item in reference if item.lower() in missing_lower]

    return matched, extras, missing

# --- File Picker ---
root = tk.Tk()
root.withdraw()
file_path = filedialog.askopenfilename(
    title="Select a PDF or Word file",
    filetypes=[("PDF files", "*.pdf"), ("Word files", "*.docx")]
)

if not file_path:
    print("❌ No file selected.")
    exit()

# Extract pages
if file_path.lower().endswith(".pdf"):
    pages = extract_text_from_pdf(file_path)
elif file_path.lower().endswith(".docx"):
    pages = extract_text_from_docx(file_path)
else:
    print("❌ Unsupported file format.")
    exit()

# Compare
extracted = find_index_entries(pages)
matched, extras, missing = compare_lists(extracted, reference_list)

# --- Output ---
print("\n📑 Extracted Index Entries:")
for e in extracted:
    print(f"- {e}")

print("\n✅ Matched Items:")
for m in matched:
    print(f"- {m}")
print(f"Total Matched: {len(matched)} / {len(reference_list)}")

print("\n⚠ Extra in Extracted (Not in Reference):")
for ex in extras:
    print(f"- {ex}")

print("\n❌ Missing from Extracted (Needed):")
for miss in missing:
    print(f"- {miss}")
