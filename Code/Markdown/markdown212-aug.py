import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import fitz  # PyMuPDF
import docx2txt
import markdownify
import ollama
import os
import threading

# ===== Extraction Functions =====
def pdf_to_text(file_path):
    text = ""
    with fitz.open(file_path) as pdf:
        for page in pdf:
            text += page.get_text()
    return text

def docx_to_text(file_path):
    return docx2txt.process(file_path)

def text_to_markdown(text):
    return markdownify.markdownify(text, heading_style="ATX")

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

# ===== Processing Function =====
def process_file():
    file_path = filedialog.askopenfilename(
        title="Select a PDF or Word file",
        filetypes=[("Documents", "*.pdf *.docx")]
    )
    if not file_path:
        return

    progress_bar["value"] = 0
    status_label.config(text="Extracting text...")
    root.update_idletasks()

    def worker():
        try:
            # Step 1: Extract text
            if file_path.lower().endswith(".pdf"):
                extracted_text = pdf_to_text(file_path)
            elif file_path.lower().endswith(".docx"):
                extracted_text = docx_to_text(file_path)
            else:
                messagebox.showerror("Error", "Unsupported file type.")
                return
            progress_bar["value"] = 30
            status_label.config(text="Converting to Markdown...")
            root.update_idletasks()

            # Step 2: Convert to Markdown
            initial_md = text_to_markdown(extracted_text)

            progress_bar["value"] = 60
            status_label.config(text="Refining with LLM...")
            root.update_idletasks()

            # Step 3: Refine with LLM
            refined_md = refine_with_llm(initial_md)

            progress_bar["value"] = 100
            status_label.config(text="Done!")
            root.update_idletasks()

            # Step 4: Preview in text area
            preview_box.delete("1.0", tk.END)
            preview_box.insert(tk.END, refined_md)

            # Store output path & content
            global last_output_path, last_refined_md
            last_output_path = os.path.splitext(file_path)[0] + "_refined.md"
            last_refined_md = refined_md

        except Exception as e:
            messagebox.showerror("Error", str(e))

    threading.Thread(target=worker).start()

# ===== Save Function =====
def save_markdown():
    if last_refined_md.strip():
        with open(last_output_path, "w", encoding="utf-8") as f:
            f.write(last_refined_md)
        messagebox.showinfo("Saved", f"Refined Markdown saved to:\n{last_output_path}")
    else:
        messagebox.showerror("Error", "No refined Markdown to save.")

# ===== GUI Setup =====
root = tk.Tk()
root.title("PDF/Word → Refined Markdown")
root.geometry("800x600")

# Upload button
upload_btn = tk.Button(root, text="Upload Document", command=process_file, font=("Arial", 12), bg="lightblue")
upload_btn.pack(pady=10)

# Progress bar
progress_bar = ttk.Progressbar(root, length=400, mode="determinate")
progress_bar.pack(pady=5)

# Status label
status_label = tk.Label(root, text="Idle", font=("Arial", 10))
status_label.pack()

# Preview area
preview_label = tk.Label(root, text="Refined Markdown Preview:", font=("Arial", 12, "bold"))
preview_label.pack(pady=5)

preview_box = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=90, height=20, font=("Consolas", 10))
preview_box.pack(padx=10, pady=5)

# Save button
save_btn = tk.Button(root, text="Save Markdown", command=save_markdown, font=("Arial", 12), bg="lightgreen")
save_btn.pack(pady=10)

# Storage variables
last_output_path = ""
last_refined_md = ""

root.mainloop()
