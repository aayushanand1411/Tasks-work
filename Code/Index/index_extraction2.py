import fitz  # PyMuPDF
import docx2txt
import re
import tkinter as tk
from tkinter import filedialog

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

# --- File Picker UI ---
root = tk.Tk()
root.withdraw()  # hide main window
file_path = filedialog.askopenfilename(
    title="Select a PDF or Word file",
    filetypes=[("PDF files", "*.pdf"), ("Word files", "*.docx")]
)

if not file_path:
    print("❌ No file selected.")
    exit()

# Process file
if file_path.lower().endswith(".pdf"):
    pages = extract_text_from_pdf(file_path)
elif file_path.lower().endswith(".docx"):
    pages = extract_text_from_docx(file_path)
else:
    print("❌ Unsupported file format!")
    exit()

# Extract index entries
index_entries = find_index_entries(pages)

# Print results
if index_entries:
    print(f"✅ Found {len(index_entries)} index entries:\n")
    for i, entry in enumerate(index_entries, start=1):
        print(f"{i}. {entry}")
else:
    print("⚠ No index page detected.")
