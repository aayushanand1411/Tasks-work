import fitz  # PyMuPDF
import os

def extract_images_and_diagrams(pdf_path, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    doc = fitz.open(pdf_path)

    img_count = 0
    for page_num, page in enumerate(doc, start=1):
        # --- Extract raster images ---
        for img_index, img in enumerate(page.get_images(full=True), start=1):
            xref = img[0]
            base_image = doc.extract_image(xref)
            img_bytes = base_image["image"]
            img_ext = base_image["ext"]
            img_path = os.path.join(output_folder, f"page{page_num}_img{img_index}.{img_ext}")
            with open(img_path, "wb") as f:
                f.write(img_bytes)
            img_count += 1

        # --- Extract vector diagrams / flowcharts as SVG ---
        svg = page.get_svg_image()
        if svg.strip():
            svg_path = os.path.join(output_folder, f"page{page_num}_diagram.svg")
            with open(svg_path, "w", encoding="utf-8") as f:
                f.write(svg)
            img_count += 1

    print(f"Extracted {img_count} images/diagrams into {output_folder}")

# Example usage
extract_images_and_diagrams(
    r"C:\Users\aayus\Downloads\AD2_SRS_2024_080724.pdf",
    r"C:\Users\aayus\Downloads\Extracted"
)
