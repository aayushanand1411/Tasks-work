from docling.document_converter import DocumentConverter, InputFormat
from docling.pipeline_options import PdfPipelineOptions, PdfFormatOption

# Example constant for image scaling
IMAGE_RESOLUTION_SCALE = 2.0  

# Define pipeline options
pipeline_options = PdfPipelineOptions(
    images_scale=IMAGE_RESOLUTION_SCALE,
    generate_page_images=True,
    generate_picture_images=True,
    enable_table_structure=False
)

# Initialize converter with format options
converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(
            pipeline_options=pipeline_options
        )
    }
)

# Convert example
doc = converter.convert(r"C:\Users\aayus\Downloads\AD2_SRS_2024_080724.pdf")
markdown_text = doc.document.export_to_markdown()

with open("example.md", "w", encoding="utf-8") as f:
    f.write(markdown_text)
