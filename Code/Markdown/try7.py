import pdfplumber
import fitz
import os

pdf_path = r"C:\Users\aayus\Downloads\AD2_SRS_2024_080724.pdf"
output_dir = r"processed_marker_docs"
os.makedirs(output_dir, exist_ok=True)

# Minimum width and height for drawings to be considered
MIN_WIDTH = 30   # adjust as needed
MIN_HEIGHT = 30  # adjust as needed

def get_image_coords(pdf_path):
    doc = fitz.open(pdf_path)
    print(f'Total pages: {doc.page_count}')
    
    all_drawings = {}
    
    for i in range(3, doc.page_count):
        page = doc.load_page(i)
        drawings = page.get_drawings()
        page_bboxes = []
        for d in drawings:
            if "bbox" in d:
                x0, y0, x1, y1 = d["bbox"]
                width = x1 - x0
                height = y1 - y0
                # Only keep drawings larger than minimum size
                if width >= MIN_WIDTH and height >= MIN_HEIGHT:
                    page_bboxes.append(d["bbox"])
        if page_bboxes:
            all_drawings[i] = page_bboxes
    
    doc.close()
    return all_drawings


image_coords = get_image_coords(pdf_path)

with pdfplumber.open(pdf_path) as doc:
    for page_num, bboxes in image_coords.items():
        page = doc.pages[page_num]
        for idx, bbox in enumerate(bboxes):
            x0, y0, x1, y1 = bbox
            img = page.crop((x0, y0, x1, y1)).to_image()
            img.save(f'{output_dir}/page_{page_num}_image_{idx}.png')
            print(f"Saved page {page_num}, image {idx} (size: {x1-x0}x{y1-y0})")
