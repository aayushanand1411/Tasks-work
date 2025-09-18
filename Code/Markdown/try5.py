import os
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter, PdfFormatOption

# Paths
INPUT_PDF = r"C:\Users\aayus\Downloads\AD2_SRS_2024_080724.pdf"   # change this
OUTPUT_DIR = r"D:\Virtual_Environment_11\New\images"         # change this

os.makedirs(OUTPUT_DIR, exist_ok=True)

def main():
    # Configure pipeline (disable table detection to avoid TableModel error)
    pipeline_options = PdfPipelineOptions(
        generate_page_images=False,       # full page not needed
        generate_picture_images=True,     # extract images/figures
        enable_table_structure=False
    )

    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pipeline_options,
                disable_table_structure=True
            )
        }
    )

    # Convert the PDF
    conv_res = converter.convert(INPUT_PDF)

    # Collect and save images sequentially
    image_count = 1
    for element in conv_res.document.content.elements:
        if element.type.name == "Picture":  # Only images/diagrams
            img = element.render()  # get PIL Image
            img_path = os.path.join(OUTPUT_DIR, f"{image_count}.png")
            img.save(img_path)
            print(f"Saved: {img_path}")
            image_count += 1

    print(f"\n✅ Extraction complete. {image_count-1} images saved in {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
