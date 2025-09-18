import pdfplumber
import fitz
import os

pdf_path = r"C:\Users\aayus\Downloads\AD2_SRS_2024_080724.pdf"
output_dir = r"processed_marker_docs"
os.makedirs(output_dir, exist_ok=True)

def get_image_coords(pdf_path):
    doc = fitz.open(pdf_path)
    print(f'Total pages: {doc.page_count}')
    
    all_drawings = {}
    
    for i in range(3, doc.page_count):
        page = doc.load_page(i)
        # Get all drawings on the page
        drawings = page.get_drawings()
        page_bboxes = []
        for d in drawings:
            if "bbox" in d:  # only keep drawings with bounding box
                page_bboxes.append(d["bbox"])
        if page_bboxes:
            all_drawings[i] = page_bboxes
    
    doc.close()
    return all_drawings


# Get all drawings with bounding boxes
image_coords = get_image_coords(pdf_path)

# Open PDF with pdfplumber to crop
with pdfplumber.open(pdf_path) as doc:
    for page_num, bboxes in image_coords.items():
        page = doc.pages[page_num]
        for idx, bbox in enumerate(bboxes):
            # pdfplumber expects (x0, top, x1, bottom)
            x0, y0, x1, y1 = bbox
            img = page.crop((x0, y0, x1, y1)).to_image()
            img.save(f'{output_dir}/page_{page_num}_image_{idx}.png')
            print(f"Saved page {page_num}, image {idx}")
