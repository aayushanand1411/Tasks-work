import tkinter as tk
from tkinter import filedialog, messagebox
import fitz  # PyMuPDF
import docx2txt
import markdownify
import ollama
import os

# Function to convert PDF to text
def pdf_to_text(file_path):
    text = ""
    with fitz.open(file_path) as pdf:
        for page in pdf:
            text += page.get_text()
    return text

# Function to convert DOCX to text
def docx_to_text(file_path):
    return docx2txt.process(file_path)

# Function to convert plain text to markdown
def text_to_markdown(text):
    # Here we could use markdownify for HTML, 
    # but assuming text is already plain, we format it.
    return markdownify.markdownify(text, heading_style="ATX")

# Function to refine markdown using local LLM
def refine_with_llm(markdown_content):
    prompt = f"""You are a markdown formatting assistant. 
The following content is in markdown but may be imperfect.
Reformat it into clean, consistent, professional markdown:

{markdown_content}
"""
    response = ollama.chat(model="llama3", messages=[
        {"role": "user", "content": prompt}
    ])
    return response['message']['content']

# Main processing function
def process_file():
    file_path = filedialog.askopenfilename(
        title="Select a PDF or Word file",
        filetypes=[("Documents", "*.pdf *.docx")]
    )
    if not file_path:
        return

    try:
        # Step 1: Extract text
        if file_path.lower().endswith(".pdf"):
            extracted_text = pdf_to_text(file_path)
        elif file_path.lower().endswith(".docx"):
            extracted_text = docx_to_text(file_path)
        else:
            messagebox.showerror("Error", "Unsupported file type.")
            return

        # Step 2: Convert to Markdown
        initial_md = text_to_markdown(extracted_text)

        # Step 3: Refine with LLM
        refined_md = refine_with_llm(initial_md)

        # Step 4: Save output
        output_path = os.path.splitext(file_path)[0] + "_refined.md"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(refined_md)

        messagebox.showinfo("Success", f"Refined Markdown saved to:\n{output_path}")

    except Exception as e:
        messagebox.showerror("Error", str(e))

# GUI setup
root = tk.Tk()
root.title("PDF/Word to Markdown with LLM")
root.geometry("400x200")

label = tk.Label(root, text="Convert PDF/Word to refined Markdown", font=("Arial", 14))
label.pack(pady=20)

upload_btn = tk.Button(root, text="Upload Document", command=process_file, font=("Arial", 12), bg="lightblue")
upload_btn.pack(pady=10)

root.mainloop()
