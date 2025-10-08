#!/usr/bin/env python3
"""
Improved and more robust version of the PDF -> descriptive mapped sections pipeline.

Main improvements:
- clearer structure and type annotations
- lazy loading of SentenceTransformer with a safe fallback
- corrected fuzzy/semantic thresholds (fuzzy: 0-100 scale)
- safer, validated PDF cropping
- robust markdown image placeholder and markdown-image replacement
- better heading extraction and content splitting logic
- improved error handling and logging
- consistent return types and small CLI wrapper
- docling availability-check (so the script fails gracefully if docling isn't installed)

Notes:
- This file expects the same external libraries you used previously (docling, ollama, sentence-transformers,
  rapidfuzz, pymupdf). If docling is not available the pipeline will raise a clear error.
- You can configure certain values via environment variables: OLLAMA_HOST, OLLAMA_MODEL, IMAGE_RESOLUTION_SCALE,
  SENTENCE_TRANSFORMER_MODEL_PATH.

"""
from __future__ import annotations

import argparse
import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import fitz
import numpy as np
import ollama
from rapidfuzz import fuzz
from sentence_transformers import SentenceTransformer, util

# Try importing docling components (optional at runtime)
try:
    from docling_core.types.doc import PictureItem
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions, EasyOcrOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption
    DOC_LING_AVAILABLE = True
except Exception:
    PictureItem = None  # type: ignore
    InputFormat = None  # type: ignore
    PdfPipelineOptions = None  # type: ignore
    EasyOcrOptions = None  # type: ignore
    DocumentConverter = None  # type: ignore
    PdfFormatOption = None  # type: ignore
    DOC_LING_AVAILABLE = False


# ----------------------
# Logging
# ----------------------
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ----------------------
# Configuration and defaults
# ----------------------
MODEL_NAME = os.environ.get("OLLAMA_MODEL", "gemma3:4b")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
IMAGE_RESOLUTION_SCALE = float(os.environ.get("IMAGE_RESOLUTION_SCALE", "2.0"))
SENTENCE_TRANSFORMER_MODEL_PATH = os.environ.get(
    "SENTENCE_TRANSFORMER_MODEL_PATH", "/home/dlpda/Aayush/sep22/model"
)


# ----------------------
# Lazy-loaded sentence transformer
# ----------------------
_sentence_model: Optional[SentenceTransformer] = None


def get_sentence_model(path: Optional[str] = None) -> SentenceTransformer:
    """Lazy load the sentence transformer. Falls back to 'all-MiniLM-L6-v2' if the configured path fails.

    Keeps the heavy initialization out of module import time.
    """
    global _sentence_model
    if _sentence_model is not None:
        return _sentence_model

    model_path = path or SENTENCE_TRANSFORMER_MODEL_PATH
    try:
        logger.info("Loading sentence-transformer from: %s", model_path)
        _sentence_model = SentenceTransformer(model_path)
    except Exception as e:
        logger.warning(
            "Failed to load model from %s: %s. Falling back to 'all-MiniLM-L6-v2'.", model_path, e
        )
        _sentence_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _sentence_model


# ----------------------
# Utility helpers
# ----------------------

def _normalize_text_for_fuzzy(s: str) -> str:
    s = s.lower()
    # strip non-alphanumeric (keep spaces)
    s = re.sub(r"[^0-9a-z\s]", "", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


# ----------------------
# PDF cropping
# ----------------------

def crop_pdf_headers_footers(
    input_pdf_path: str, output_dir: Optional[str] = None, top_percent: float = 0.08, bottom_percent: float = 0.1
) -> Path:
    """Crop top and bottom margins of each page and write a new PDF named 'cropped_<original>'.

    Args:
        input_pdf_path: path to source pdf
        output_dir: directory to store the cropped PDF; defaults to same folder as input
        top_percent: fraction of page height to crop from top (0.0-0.5)
        bottom_percent: fraction of page height to crop from bottom (0.0-0.5)

    Returns:
        Path to the cropped PDF.
    """
    input_pdf = Path(input_pdf_path)
    if not input_pdf.exists():
        raise FileNotFoundError(f"PDF not found: {input_pdf}")

    if not (0 <= top_percent < 0.5 and 0 <= bottom_percent < 0.5):
        raise ValueError("top_percent and bottom_percent must be between 0 and 0.5")

    output_dir = Path(output_dir) if output_dir else input_pdf.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"cropped_{input_pdf.name}"

    doc = fitz.open(str(input_pdf))
    try:
        for page in doc:
            rect = page.rect
            new_rect = fitz.Rect(
                rect.x0,
                rect.y0 + rect.height * top_percent,
                rect.x1,
                rect.y1 - rect.height * bottom_percent,
            )
            page.set_cropbox(new_rect)

        doc.save(str(output_path))
        logger.info("Saved cropped PDF to %s", output_path)
    finally:
        doc.close()

    return output_path


# ----------------------
# Markdown + Image extraction
# ----------------------

def md_extract(pdf_path: str, output_dir: Path) -> Path:
    """Use docling to convert the (cropped) PDF to markdown and extract images.

    Returns path to the generated markdown file.
    """
    if not DOC_LING_AVAILABLE:
        raise RuntimeError("docling dependencies are missing. Install docling_core and related packages to use md_extract.")

    start = time.time()
    pdf_path = Path(pdf_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    pipeline_options = PdfPipelineOptions(
        images_scale=IMAGE_RESOLUTION_SCALE,
        generate_page_images=True,
        generate_picture_images=True,
        ocr_options=EasyOcrOptions(),
    )
    converter = DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
    )

    try:
        conv_res = converter.convert(pdf_path)
    except Exception as e:
        logger.exception("DocumentConverter.convert failed: %s", e)
        raise

    doc_filename = conv_res.input.file.stem
    pic_count = 0

    # extract images (PictureItem)
    for element, _meta in conv_res.document.iterate_items():
        try:
            if PictureItem is not None and isinstance(element, PictureItem):
                pic_count += 1
                out_file = output_dir / f"{pic_count}.png"
                try:
                    img = element.get_image(conv_res.document)
                    # img should be a PIL image-like object with .save
                    img.save(out_file, "PNG")
                except Exception as e:
                    logger.warning("Failed to save image %s: %s", out_file, e)
        except Exception:
            # be defensive; iterate_items can yield unexpected types
            logger.debug("Skipping non-picture element or unexpected element type.")

    md_file = output_dir / f"{doc_filename}.md"
    try:
        conv_res.document.save_as_markdown(md_file)
    except Exception as e:
        logger.exception("Failed to save markdown: %s", e)
        raise

    logger.info("[md_extract] Exported %d images → %s (%.2fs)", pic_count, md_file, time.time() - start)
    return md_file


# ----------------------
# Image description generation (via ollama)
# ----------------------

def process_images(image_folder: Path, output_file: Path, model_name: str = MODEL_NAME, host: str = OLLAMA_HOST) -> Path:
    """Generate textual descriptions for images in the target folder using ollama.

    Writes a JSON list of {"image": filename, "description": text} to output_file.
    Returns output_file (Path).
    """
    start = time.time()
    image_folder = Path(image_folder)
    image_files = sorted([f for f in os.listdir(image_folder) if f.lower().endswith((".png", ".jpg", ".jpeg"))])
    client = ollama.Client(host)

    if not image_files:
        logger.warning("[process_images] No images found in %s", image_folder)
        return output_file

    descriptions = []
    for image_file in image_files:
        image_path = str(image_folder / image_file)
        prompt = (
            "You are an assistant that writes clear, objective, and useful descriptions of images. "
            "Describe the image in 50-150 words with meaningful detail — objects, layout, colors, and apparent purpose. "
            "Do not make unverifiable claims (e.g. personal identities or private data). Keep the description factual and concise."
        )

        # try a few times on transient failure
        last_err = None
        for attempt in range(3):
            try:
                response = client.generate(model_name, prompt, images=[image_path], stream=False)
                # ollama responses may have different formats; be defensive
                description = ""
                if isinstance(response, dict):
                    description = response.get("response") or response.get("text") or ""
                elif hasattr(response, "get"):
                    description = response.get("response", "")
                else:
                    # fallback to str()
                    description = str(response)

                description = (description or "").strip()
                if not description:
                    raise ValueError("empty description")

                descriptions.append({"image": image_file, "description": description})
                logger.info("[process_images] Processed %s", image_file)
                last_err = None
                break
            except Exception as e:
                last_err = e
                logger.warning("[process_images] attempt %d for %s failed: %s", attempt + 1, image_file, e)
                time.sleep(0.5 * (attempt + 1))

        if last_err is not None:
            logger.error("[process_images] Failed to generate description for %s after retries: %s", image_file, last_err)

    if descriptions:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(json.dumps(descriptions, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("[process_images] Saved %d descriptions → %s (%.2fs)", len(descriptions), output_file, time.time() - start)
    else:
        logger.warning("[process_images] No descriptions produced.")

    return output_file


# ----------------------
# Replace image placeholders in markdown with generated descriptions
# ----------------------

def get_description_map_from_json(json_file: Path) -> Dict[str, str]:
    if not json_file.exists():
        raise FileNotFoundError(json_file)
    data = json.loads(json_file.read_text(encoding="utf-8"))
    return {item["image"]: item["description"] for item in data}


def replace_images_in_md(md_input_path: Path, md_output_path: Path, json_file: Path) -> Tuple[Path, str]:
    """Replace both <!-- image --> placeholders and markdown image tags with textual descriptions.

    Returns tuple (output_path, final_text)
    """
    start = time.time()
    desc_map = get_description_map_from_json(json_file)

    text = md_input_path.read_text(encoding="utf-8")

    # 1) replace placeholder occurrences sequentially (assumes placeholders correspond to 1.png, 2.png, ...)
    counter = 1

    def _placeholder_repl(_m: re.Match) -> str:
        nonlocal counter
        img_name = f"{counter}.png"
        counter += 1
        return (desc_map.get(img_name, _m.group(0))) + "\n\n" if desc_map.get(img_name) else _m.group(0)

    text = re.sub(r"<!--\s*image\s*-->", _placeholder_repl, text)

    # 2) replace explicit markdown image tags - keep behavior conservative (replace tag with description if available)
    def _md_img_repl(m: re.Match) -> str:
        path_inside = m.group(1).strip()
        filename = Path(path_inside).name
        desc = desc_map.get(filename)
        if desc:
            return desc + "\n\n"
        return m.group(0)

    text = re.sub(r"!\[.*?\]\(([^)]+)\)", _md_img_repl, text)

    md_output_path.parent.mkdir(parents=True, exist_ok=True)
    md_output_path.write_text(text, encoding="utf-8")

    logger.info("[replace_images_in_md] Updated markdown → %s (%.2fs)", md_output_path, time.time() - start)
    return md_output_path, text


# ----------------------
# Headings and content extraction
# ----------------------

def heading_extraction(path: Path) -> List[str]:
    """Extract top-level headings that begin with '## <number>' and return the full heading lines in order.

    Matches examples:
      ## 1 Introduction
      ## 2. Acronyms
      ## 3) Reference Documents
    """
    headings: List[str] = []
    pattern = re.compile(r"^##\s*(\d+)[\.)]?\s*(.*)$")

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            m = pattern.match(line)
            if m:
                # keep the original formatting of heading line
                headings.append(line.rstrip("\n"))
    logger.info("[heading_extraction] Found %d headings in %s", len(headings), path)
    return headings


def content_extraction(path: Path, headings: List[str]) -> Dict[str, str]:
    """Split the markdown file into sections keyed by the heading lines (as provided by heading_extraction).

    Also returns a 'Cover Page' entry containing the content before the first matched heading (up to 50 lines).
    """
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    sections: Dict[str, str] = {}
    cover_lines: List[str] = []

    i_head = 0
    current_heading: Optional[str] = None
    buffer: List[str] = []

    for line in lines:
        if i_head < len(headings) and line.strip() == headings[i_head].strip():
            # start of a new heading
            if current_heading is not None:
                sections[current_heading] = "".join(buffer)
            current_heading = headings[i_head]
            buffer = [line]
            i_head += 1
        elif current_heading is not None:
            buffer.append(line)
        else:
            cover_lines.append(line)

    # add last collected section
    if current_heading is not None:
        sections[current_heading] = "".join(buffer)

    # Cover Page: first 50 lines or all if shorter
    sections["Cover Page"] = "".join(cover_lines[:50]) if cover_lines else ""

    logger.info("[content_extraction] Extracted %d sections + Cover Page from %s", len(sections) - 1, path)
    return sections


# ----------------------
# Semantic + fuzzy mapping
# ----------------------

def map_sections_to_target(
    sections_dict: Dict[str, str],
    target_dict: Dict[str, str],
    semantic_threshold: float = 0.6,
    fuzzy_threshold: float = 60.0,
) -> Dict[str, Dict[str, Optional[object]]]:
    """Map sections to target keys using sentence embeddings (cosine similarity) and fuzzy matching.

    Returns a mapping from target_key -> {content, semantic_score, fuzzy_score}
    """
    model = get_sentence_model()
    target_keys = list(target_dict.keys())

    # initialize mapped structure
    mapped: Dict[str, Dict[str, Optional[object]]] = {
        k: {"content": "", "semantic_score": None, "fuzzy_score": None} for k in target_keys
    }

    # compute target embeddings once
    target_embeddings = model.encode(target_keys, convert_to_tensor=True, show_progress_bar=False)

    for section_key, section_content in sections_dict.items():
        # prefer using the heading text without the leading '##' for embedding
        cleaned_heading = re.sub(r"^##\s*", "", section_key).strip()
        if not cleaned_heading:
            continue

        section_emb = model.encode(cleaned_heading, convert_to_tensor=True)
        cos_scores = util.cos_sim(section_emb, target_embeddings)[0].cpu().numpy()

        best_idx = int(np.argmax(cos_scores))
        best_sem_score = float(cos_scores[best_idx])
        best_sem_key = target_keys[best_idx]

        # fuzzy matching (0-100)
        norm_section = _normalize_text_for_fuzzy(cleaned_heading)
        fuzzy_scores = [fuzz.ratio(norm_section, _normalize_text_for_fuzzy(k)) for k in target_keys]
        best_fuzzy_idx = int(np.argmax(fuzzy_scores))
        best_fuzzy_score = float(fuzzy_scores[best_fuzzy_idx])
        best_fuzzy_key = target_keys[best_fuzzy_idx]

        chosen_key = None
        chosen_sem = None
        chosen_fuzzy = None

        if best_sem_score >= semantic_threshold:
            chosen_key = best_sem_key
            chosen_sem = round(best_sem_score, 3)
            chosen_fuzzy = int(best_fuzzy_score)
        elif best_fuzzy_score >= fuzzy_threshold:
            chosen_key = best_fuzzy_key
            chosen_sem = round(best_sem_score, 3)
            chosen_fuzzy = int(best_fuzzy_score)

        if chosen_key:
            # append if content already exists (helps when multiple sections map to the same key)
            existing = mapped[chosen_key]["content"]
            if existing:
                mapped[chosen_key]["content"] = existing + "\n" + section_content
            else:
                mapped[chosen_key]["content"] = section_content
            mapped[chosen_key]["semantic_score"] = chosen_sem
            mapped[chosen_key]["fuzzy_score"] = chosen_fuzzy

            logger.debug(
                "Mapped section '%s' -> '%s' (sem=%.3f, fuzzy=%s)",
                cleaned_heading,
                chosen_key,
                chosen_sem if chosen_sem is not None else -1,
                chosen_fuzzy,
            )
        else:
            # If not mapped, append to '17 SomethingElse' if present, else create 'SomethingElse'
            fallback_key = next((k for k in target_keys if "somethingelse" in k.replace(" ", "").lower()), None)
            if fallback_key:
                mapped[fallback_key]["content"] += "\n" + section_content if mapped[fallback_key]["content"] else section_content
                mapped[fallback_key]["semantic_score"] = mapped[fallback_key].get("semantic_score") or None
                mapped[fallback_key]["fuzzy_score"] = mapped[fallback_key].get("fuzzy_score") or None
            else:
                logger.info("Section '%s' left unmapped (sem=%.3f, fuzzy=%.1f)", cleaned_heading, best_sem_score, best_fuzzy_score)

    return mapped


# ----------------------
# Main pipeline wrappers
# ----------------------

def pdf_to_descriptive_mapped_sections(pdf_path: str, output_dir: str) -> Dict[str, object]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Step 0: crop headers/footers
    cropped_pdf = crop_pdf_headers_footers(pdf_path, output_dir)

    # Step 1: markdown + images
    md_file = md_extract(str(cropped_pdf), output_dir)

    # Step 2: image descriptions
    json_file = output_dir / "image_descriptions.json"
    process_images(output_dir, json_file)

    # Step 3: replace placeholders
    md_with_desc = output_dir / f"{md_file.stem}_with_desc.md"
    output_path, final_text = replace_images_in_md(md_file, md_with_desc, json_file)

    # Step 4: headings & sections
    headings = heading_extraction(md_with_desc)
    sections = content_extraction(md_with_desc, headings)

    # Step 5: target keys
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
        "17 SomethingElse": "",
    }

    # Step 6: mapping
    mapped_sections = map_sections_to_target(sections, target_dict)

    logger.info("Extraction and mapping complete. Markdown: %s; Descriptions: %s; Mapped keys: %d", md_file, json_file, len(mapped_sections))

    return {
        "original_md": str(md_file),
        "image_descriptions_json": str(json_file),
        "md_with_descriptions": final_text,
        "mapped_sections": mapped_sections,
    }


def pdf_to_descriptive_mapped_sections2(md_path: str, output_dir: Optional[str] = None) -> Dict[str, object]:
    """Process an existing markdown file (with descriptions already) and map sections to the target keys.

    Useful when you already have a markdown and don't want to run docling/ollama.
    """
    md_path = Path(md_path)
    if not md_path.exists():
        raise FileNotFoundError(md_path)

    output_dir = Path(output_dir) if output_dir else md_path.parent

    headings = heading_extraction(md_path)
    sections = content_extraction(md_path, headings)

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
        "17 SomethingElse": "",
    }

    mapped_sections = map_sections_to_target(sections, target_dict)

    logger.info("Mapped sections from markdown: %s. Keys mapped: %d", md_path, len([k for k, v in mapped_sections.items() if v.get("content")]))

    return {
        "md_path": str(md_path),
        "mapped_sections": mapped_sections,
    }


# ----------------------
# CLI
# ----------------------

def _build_cli() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="PDF -> descriptive mapped sections pipeline")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--pdf", help="input PDF to process (this will run crop -> docling -> ollama)")
    g.add_argument("--md", help="existing markdown file already containing image descriptions")
    p.add_argument("--out", default="./out", help="output directory")
    return p


def main() -> None:
    parser = _build_cli()
    args = parser.parse_args()

    if args.pdf:
        res = pdf_to_descriptive_mapped_sections(args.pdf, args.out)
        # save mapped sections as JSON sample
        Path(args.out).joinpath("mapped_sections.json").write_text(json.dumps(res["mapped_sections"], ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("Saved mapped_sections.json to %s", args.out)
    else:
        res = pdf_to_descriptive_mapped_sections2(args.md, args.out)
        Path(args.out).joinpath("mapped_sections_from_md.json").write_text(json.dumps(res["mapped_sections"], ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("Saved mapped_sections_from_md.json to %s", args.out)


if __name__ == "__main__":
    main()
