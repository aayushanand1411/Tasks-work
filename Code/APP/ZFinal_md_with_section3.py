import os
import re
import json
import time
import logging
from pathlib import Path

import ollama
from docling_core.types.doc import ImageRefMode, PictureItem
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, EasyOcrOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

from sentence_transformers import SentenceTransformer, util
from rapidfuzz import fuzz
import numpy as np
import fitz


# ===============================
# CONFIG
# ===============================
MODEL_NAME = "gemma3:4b"
IMAGE_RESOLUTION_SCALE = 2.0

SENTENCE_TRANSFORMER_MODEL_PATH = "/home/aayush/Downloads/model"

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# =========
# pdf pre processing

def crop_pdf_headers_footers(input_pdf_path, output_dir, top_percent=0.08, bottom_percent=0.1):
    if output_dir is None:
        output_dir = os.path.dirname(input_pdf_path)
    os.makedirs(output_dir, exist_ok=True)

    input_filename = os.path.basename(input_pdf_path)
    output_pdf_path = os.path.join(output_dir, f"cropped_{input_filename}")

    doc = fitz.open(input_pdf_path)

    for page in doc:
        rect = page.rect
        new_rect = fitz.Rect(
            rect.x0,
            rect.y0 + rect.height * top_percent,
            rect.x1,
            rect.y1 - rect.height * bottom_percent
        )
        page.set_cropbox(new_rect)

    doc.save(output_pdf_path)
    doc.close()

    return output_pdf_path
# ===============================
# PDF TO MARKDOWN & IMAGES EXTRACTION
# ===============================
def md_extract(pdf_path: str, output_dir: Path) -> Path:
    start = time.time()
    pdf_path = Path(pdf_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    pipeline_options = PdfPipelineOptions(
        images_scale=IMAGE_RESOLUTION_SCALE,
        generate_page_images=True,
        generate_picture_images=True,
        ocr_options=EasyOcrOptions()
    )
    converter = DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
    )

    conv_res = converter.convert(pdf_path)
    doc_filename = conv_res.input.file.stem
    pic_count = 0

    for element, _ in conv_res.document.iterate_items():
        if isinstance(element, PictureItem):
            pic_count += 1
            filename = output_dir / f"{pic_count}.png"
            try:
                element.get_image(conv_res.document).save(filename, "PNG")
            except Exception as e:
                logging.warning(f"Failed to extract image: {e}")

    md_file = output_dir / f"{doc_filename}.md"
    conv_res.document.save_as_markdown(md_file)

    logging.info(f"[md_extract] Exported {pic_count} images → {md_file} ({time.time()-start:.2f}s)")
    return md_file


# ===============================
# GENERATE IMAGE DESCRIPTIONS
# ===============================
def process_images(image_folder: Path, output_file: Path) -> Path:
    start = time.time()
    image_descriptions = []
    client = ollama.Client("http://localhost:11434")

    image_files = sorted([f for f in os.listdir(image_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
    if not image_files:
        logging.warning(f"[process_images] No images found in {image_folder}")
        return output_file

    for image_file in image_files:
        image_path = str(image_folder / image_file)
        prompt = "Describe this image in 50-150 words with meaningful detail."

        try:
            response = client.generate(MODEL_NAME, prompt, images=[image_path], stream=False)
            description = response.get("response", "").strip()
            if not description:
                raise ValueError("Empty description returned")

            image_descriptions.append({"image": image_file, "description": description})
            logging.info(f"[process_images] Processed {image_file}")

        except Exception as e:
            logging.error(f"Error processing {image_file}: {e}")

    if image_descriptions:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(image_descriptions, f, indent=4, ensure_ascii=False)
        logging.info(f"[process_images] Saved {len(image_descriptions)} descriptions → {output_file} "
                     f"({time.time()-start:.2f}s)")
    else:
        logging.warning("[process_images] No valid descriptions generated")

    return output_file


# ===============================
# REPLACE IMAGE PLACEHOLDERS WITH DESCRIPTIONS
# ===============================
def get_description(image_name: str, data: list) -> str | None:
    for item in data:
        if item["image"] == image_name:
            return item["description"]
    return None


def replace_images_in_md(md_input_path: Path, md_output_path: Path, json_file: Path) -> Path:
    start = time.time()

    if not json_file.exists():
        logging.warning(f"[replace_images_in_md] JSON file not found: {json_file}")
        return md_input_path

    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    output_lines = []
    image_counter = 1

    with open(md_input_path, "r", encoding="utf-8") as md_file:
        for line in md_file:
            if "<!-- image -->" in line:
                image_name = f"{image_counter}.png"
                description = get_description(image_name, data)
                if description:
                    output_lines.append(description + "\n\n")
                    image_counter += 1
                else:
                    logging.warning(f"No description found for {image_name}, keeping placeholder")
                    output_lines.append(line)
            else:
                output_lines.append(line)

    with open(md_output_path, "w", encoding="utf-8") as out_file:
        out_file.writelines(output_lines)

    final_text = ' '.join(output_lines)
    logging.info(f"[replace_images_in_md] Updated markdown → {md_output_path} ({time.time()-start:.2f}s)")
    return md_output_path, final_text


# ===============================
# EXTRACT HEADINGS AND SECTIONS FROM MARKDOWN
# ===============================
def heading_extraction(path):
    heading = []
    with open(path, "r", encoding="utf-8") as f:
        i = 1
        pattern1 = re.compile(rf"^## {i} ")
        pattern2 = re.compile(rf"^## {i}\. ")
        pattern3 = re.compile(rf"^## {i}\) ")
        for line in f:
            if pattern1.match(line) or pattern2.match(line) or pattern3.match(line):
                heading.append(line)
                i += 1
                pattern1 = re.compile(rf"^## {i} ")
                pattern2 = re.compile(rf"^## {i}\. ")
                pattern3 = re.compile(rf"^## {i}\) ")
    return heading


def content_extraction(path, heading):
    section = {}
    with open(path, "r", encoding="utf-8") as f:
        section_content = ""
        counter = False
        i = 0
        for line in f:
            if line == heading[i]:
                if counter:
                    section[heading[i]] = section_content
                section_content = line
                counter = True
            elif counter:
                # Check if next heading reached
                if i + 1 < len(heading) and line == heading[i+1]:
                    section[heading[i]] = section_content
                    section_content = line
                    i += 1
                else:
                    # section_content.append(line)
                    section_content = section_content + line
        # Add last section
        if counter and i < len(heading):
            section[heading[i]] = section_content
    with open(path, "r", encoding="utf-8") as f:
        section_content = ""
        i = 0
        for line in f:
            if i < 50:
                section_content = section_content + line
                i = i + 1
            else:
                section['Cover Page'] = section_content
                break
    return section
# print("".join(value.get("content", [])))

# ===============================
# SEMANTIC + FUZZY MAPPING OF SECTIONS TO TARGET KEYS
# ===============================
model = SentenceTransformer(SENTENCE_TRANSFORMER_MODEL_PATH)

def normalize(text):
    text = text.lower()
    text = re.sub(r'[^a-z\s]', '', text)
    return text.strip()

def map_sections_to_target(sections_dict, target_dict, semantic_threshold=0.5, fuzzy_threshold=0.5):
    target_keys = list(target_dict.keys())
    target_embeddings = model.encode(target_keys, convert_to_tensor=True)

    for section_key, section_content in sections_dict.items():
        section_emb = model.encode(section_key, convert_to_tensor=True)
        cos_scores = util.cos_sim(section_emb, target_embeddings)[0].cpu().numpy()

        best_idx = np.argmax(cos_scores)
        best_sem_score = cos_scores[best_idx]
        best_sem_key = target_keys[best_idx]

        norm_section = normalize(section_key)
        fuzzy_scores = [fuzz.ratio(norm_section, normalize(k)) for k in target_keys]
        best_fuzzy_idx = np.argmax(fuzzy_scores)
        best_fuzzy_score = fuzzy_scores[best_fuzzy_idx]
        best_fuzzy_key = target_keys[best_fuzzy_idx]

        if best_sem_score >= semantic_threshold:
            target_dict[best_sem_key] = {
                "content": section_content,
                "semantic_score": round(float(best_sem_score), 3),
                "fuzzy_score": best_fuzzy_score
            }
        elif best_fuzzy_score >= fuzzy_threshold:
            target_dict[best_fuzzy_key] = {
                "content": section_content,
                "semantic_score": round(float(best_sem_score), 3),
                "fuzzy_score": best_fuzzy_score
            }
        # else leave as is

    return target_dict


# ===============================
# MAIN PIPELINE
# ===============================
def pdf_to_descriptive_mapped_sections(pdf_path: str, output_dir: str):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    #step:0 pre-processing
    cropped_pdf = crop_pdf_headers_footers(pdf_path,output_dir)

    # Step 1: Extract markdown + images
    md_file = md_extract(cropped_pdf, output_dir)

    # Step 2: Generate descriptions for extracted images
    json_file = output_dir / "image_descriptions.json"
    process_images(output_dir, json_file)

    # Step 3: Replace image placeholders with descriptions
    md_with_desc = output_dir / (md_file.stem + "_with_desc.md")
    output_path, final_text = replace_images_in_md(md_file, md_with_desc, json_file)

    # Step 4: Extract headings & content from markdown with descriptions
    headings = heading_extraction(md_with_desc)
    sections = content_extraction(md_with_desc, headings)

    # Step 5: Define target dictionary keys
    target_dict = {
        "Cover Page": "",
        "1 Introduction": "",
        "2 Acronyms": "",
        "3 Reference Documents": "",
        "4 Product Description": "",
        "5 Assumptions": "",
        "6 Hardware Requirements": "",
        "7 States and Mode of Software": "",
        "8 Detailed Software Requirement": "",
        "9 Timing Requirements": "",
        "10 Loadable Data Requirements": "",
        "11 Internal and External Interface Requirement": "",
        "12 Safety & Security Requirements": "",
        "13 Software Testing Requirements": "",
        "14 General Constraints": "",
        "15 Traceability Matrix": "",
        "16 Overview": "",
        "17 SomethingElse": ""
    }

    # Step 6: Map sections to target keys
    mapped_sections = map_sections_to_target(sections, target_dict)
    # with open(f"{output_dir}/saved_mapped_dict.json", "w") as g:
    #     json.dump(mapped_sections, g)

    # Logging output info
    logging.info(f"Extracted Markdown: {md_file}")
    logging.info(f"Image Descriptions JSON: {json_file}")
    logging.info(f"Markdown with Descriptions: {md_with_desc}")

    print("\n=== MAPPED SECTIONS ===")
    for key, value in mapped_sections.items():
        print(f"\n=== Target Key: {key} ===")
        if value:
            print(f"Semantic Score: {value.get('semantic_score', 'N/A')}, Fuzzy Score: {value.get('fuzzy_score', 'N/A')}")
            # print(value.get("content", []))
        else:
            print("[NO MATCH FOUND]")

    return {
        "original_md": md_file,
        "image_descriptions_json": json_file,
        "md_with_descriptions": final_text,
        "mapped_sections": mapped_sections
    }


def pdf_to_descriptive_mapped_sections2(md_path: str):
    # Step 4: Extract headings & content from markdown with descriptions
    headings = heading_extraction(md_path)
    sections = content_extraction(md_path, headings)
    print(f'\n sections extracted from md file are {sections.keys()} \n')

    # Step 5: Define target dictionary keys
    target_dict = {
        "Cover Page": "",
        "1 Introduction": "",
        "2 Acronyms": "",
        "3 Reference Documents": "",
        "4 Product Description": "",
        "5 Assumptions": "",
        "6 Hardware Requirements": "",
        "7 States and Mode of Software": "",
        "8 Detailed Software Requirement": "",
        "9 Timing Requirements": "",
        "10 Loadable Data Requirements": "",
        "11 Internal and External Interface Requirement": "",
        "12 Safety & Security Requirements": "",
        "13 Software Testing Requirements": "",
        "14 General Constraints": "",
        "15 Traceability Matrix": "",
        "16 Overview": "",
        "17 SomethingElse": ""
    }

    # Step 6: Map sections to target keys
    mapped_sections = map_sections_to_target(sections, target_dict)

    print("\n=== MAPPED SECTIONS ===")
    for key, value in mapped_sections.items():
        print(f"\n=== Target Key: {key} ===")
        if value:
            print(f"Semantic Score: {value.get('semantic_score', 'N/A')}, Fuzzy Score: {value.get('fuzzy_score', 'N/A')}")
            # print(value.get("content", []))
        else:
            print("[NO MATCH FOUND]")

    return ""



# if __name__ == "__main__":
#     result = pdf_to_descriptive_mapped_sections(
#         pdf_path="/home/dlpda/SRS_DOCS/6407_VSH_CC_SRS_25_10_2023.pdf",
#         output_dir="/home/dlpda/Aayush/sep22/out_folder"
#     )

if __name__ == "__main__":
    result = pdf_to_descriptive_mapped_sections2(
        md_path="/home/dlpda/Aayush/pycharm/29sep/logs/2025-10-07-15:59:07/cropped_6407_VSH_CC_SRS_25_10_2023_with_desc.md"
    )
