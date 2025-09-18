import logging
import time
from pathlib import Path
from docling_core.types.doc import ImageRefMode, PictureItem, TableItem
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption


# Config
INPUT_PDF = Path(r"C:\Users\aayus\Downloads\AD2_SRS_2024_080724.pdf")
OUTPUT_DIR = Path(r'C:\Users\aayus\OneDrive\Desktop\xyz')
IMAGE_RESOLUTION_SCALE = 2.0

def main():
    logging.basicConfig(level=logging.INFO)

    # Set PDF processing options
    pipeline_options = PdfPipelineOptions(
        images_scale=IMAGE_RESOLUTION_SCALE,
        generate_page_images=True,
        generate_picture_images=True,
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
    start_time = time.time()
    conv_res = converter.convert(INPUT_PDF)
    doc_filename = conv_res.input.file.stem
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # # Save each page as image
    # for page in conv_res.document.pages.values():
    #     page_image = OUTPUT_DIR / f"{doc_filename}-page-{page.page_no}.png"
    #     page.image.pil_image.save(page_image, format="PNG")

    # Save tables and pictures
    table_count, pic_count = 0, 0
    for element, _ in conv_res.document.iterate_items():
        if isinstance(element, TableItem):
            table_count += 1
            filename = OUTPUT_DIR / f"{doc_filename}-table-{table_count}.png"
            element.get_image(conv_res.document).save(filename, "PNG")
        elif isinstance(element, PictureItem):
            pic_count += 1
            filename = OUTPUT_DIR / f"{doc_filename}-picture-{pic_count}.png"
            element.get_image(conv_res.document).save(filename, "PNG")

    # Save Markdown with image references
    md_file = OUTPUT_DIR / f"{doc_filename}-with-image-refs.md"
    conv_res.document.save_as_markdown(md_file, image_mode=ImageRefMode.REFERENCED)

    logging.info(f"Done: Exported {table_count} tables, {pic_count} pictures, and all pages in {time.time()-start_time:.2f}s")

if __name__ == "__main__":
    main()
