# nter file upload → to let user select SRS PDF.
#
# Docling DocumentConverter → convert PDF → Markdown.
#
# Markdown parsing → extract only the sections you care about (Introduction, Product Description, etc.).
#
# Store in dictionary → { "Introduction": "...", "Product Description": "...", ... }.
#
# Ask user → print that section.

import tkinter as tk
from tkinter import filedialog
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


# def upload_file():
#     root = tk.Tk()
#     root.withdraw()  # hide main tkinter window
#     file_path = filedialog.askopenfilename(
#         title="Select SRS PDF File",
#         filetypes=[("PDF files", "*.pdf")]
#     )
#     return

#
# file_path="D:\Virtual_Environment_11\Mark_Content_Extraction\29aug.py"


def pdf_to_markdown(pdf_path):
    """Convert PDF to Markdown using Docling"""
    converter = DocumentConverter()
    result = converter.convert(pdf_path)
    return result.document.export_to_markdown()


def extract_sections(markdown_text):
    """Extract only target sections into a dictionary"""
    sections_dict = {}

    # Regex to capture headings (## or #) and their content
    pattern = r"^#\s*(.+?)\n([\s\S]*?)(?=\n#|\Z)"
    matches = re.findall(pattern, markdown_text, flags=re.MULTILINE)

    for heading, content in matches:
        heading_clean = heading.strip()
        if heading_clean in TARGET_SECTIONS:
            sections_dict[heading_clean] = content.strip()

    return sections_dict


def main():
    print("Please upload your SRS PDF file...")
    pdf_path = r"C:\Users\aayus\Downloads\ReqView-Example_Software_Requirements_Specification_SRS_Document.pdf"
    if not pdf_path:
        print("No file selected. Exiting.")
        return

    print("Converting PDF to Markdown...")
    markdown_text = pdf_to_markdown(pdf_path)

    print("Extracting required sections...")
    srs_dict = extract_sections(markdown_text)

    # Ask user for a section
    print("\nAvailable Sections:")
    for key in srs_dict.keys():
        print("-", key)

    section_choice = input("\nEnter the section you want to view: ").strip()

    if section_choice in srs_dict:
        print(f"\n--- {section_choice} ---\n")
        print(srs_dict[section_choice])
    else:
        print("Section not found in the document.")


if __name__ == "__main__":
    main()
