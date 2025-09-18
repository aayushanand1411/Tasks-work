import fitz  # PyMuPDF
import os
import cairosvg  # for converting SVG -> PNG

def extract_flowcharts(pdf_path, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    doc = fitz.open(pdf_path)

    count = 0
    for page_num, page in enumerate(doc, start=1):
        # Extract vector diagrams/flowcharts
        svg = page.get_svg_image()
        if svg.strip():
            svg_path = os.path.join(output_folder, f"page{page_num}_diagram.svg")
            with open(svg_path, "w", encoding="utf-8") as f:
                f.write(svg)

            # Convert to PNG for easy viewing
            png_path = os.path.join(output_folder, f"page{page_num}_diagram.png")
            cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=png_path)

            count += 1

    print(f"✅ Extracted {count} diagrams/flowcharts into: {output_folder}")
    print("   (Both SVG and PNG versions saved)")

# Example usage
extract_flowcharts(
    r"C:\Users\aayus\Downloads\AD2_SRS_2024_080724.pdf",
    r"C:\Users\aayus\Downloads\Extracted"
)
