import os
import io
import re
import json
import cv2
import numpy as np
from PIL import Image
from pdf2image import convert_from_path
from huggingface_hub import hf_hub_download
from doclayout_yolo import YOLOv10
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from utils import PDF_PATH
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env.local")



# -------------------------------------------------------------------
# Configuration & Initialization
# -------------------------------------------------------------------
POPPLER_PATH = r"D:\ai\poppler-26.08.0\utils"
OUTPUT_FIGURES_DIR = "images"
OUTPUT_TABLES_DIR = "tables"

# IOU threshold for treating two overlapping detections as the same physical asset.
DEDUP_IOU_THRESHOLD = 0.5

# How far to search (px, at 300 DPI) for nearby heading/title text to use as a caption.
# NOTE: unlike the NCERT script, this is NOT a Fig/Table regex gap - this document has
# no caption convention at all, so we just grab whatever heading text is closest.
HEADING_SEARCH_MAX = 220
HEADING_MARGIN_RATIO = 0.05

os.makedirs(OUTPUT_FIGURES_DIR, exist_ok=True)
os.makedirs(OUTPUT_TABLES_DIR, exist_ok=True)

print("Loading local DocLayout-YOLOv10 model...")
weights_path = hf_hub_download(
    repo_id="juliozhao/DocLayout-YOLO-DocStructBench",
    filename="doclayout_yolo_docstructbench_imgsz1024.pt"
)
layout_model = YOLOv10(weights_path)

modelChain = [
    'gemini-3.6-flash',
    'gemini-3.1-flash',
    'gemini-3.1-flash-lite',
    'gemini-3.5-flash',
    'gemini-3-flash',
]

print("Initializing Gemini Cloud OCR with failover routing...")
primary_model = ChatGoogleGenerativeAI(model=modelChain[0], temperature=0)
fallback_objects = [ChatGoogleGenerativeAI(model=m, temperature=0) for m in modelChain[1:]]
gemini_chain = primary_model.with_fallbacks(fallbacks=fallback_objects)

# -------------------------------------------------------------------
# Geometry Helpers (same as the NCERT script - unchanged, reusable on merge)
# -------------------------------------------------------------------
def expand_bbox(bbox, width, height, padding_percentage=0.03):
    xmin, ymin, xmax, ymax = bbox
    w = xmax - xmin
    h = ymax - ymin
    xmin = max(0, int(xmin - (w * padding_percentage)))
    ymin = max(0, int(ymin - (h * padding_percentage)))
    xmax = min(width, int(xmax + (w * padding_percentage)))
    ymax = min(height, int(ymax + (h * padding_percentage)))
    return [xmin, ymin, xmax, ymax]


def compute_iou(box_a, box_b):
    ax_min, ay_min, ax_max, ay_max = box_a
    bx_min, by_min, bx_max, by_max = box_b
    inter_xmin = max(ax_min, bx_min)
    inter_ymin = max(ay_min, by_min)
    inter_xmax = min(ax_max, bx_max)
    inter_ymax = min(ay_max, by_max)
    inter_w = max(0, inter_xmax - inter_xmin)
    inter_h = max(0, inter_ymax - inter_ymin)
    inter_area = inter_w * inter_h
    area_a = max(0, ax_max - ax_min) * max(0, ay_max - ay_min)
    area_b = max(0, bx_max - bx_min) * max(0, by_max - by_min)
    union = area_a + area_b - inter_area
    return 0.0 if union <= 0 else inter_area / union


def dedup_mixed_type_boxes(candidates, iou_threshold=DEDUP_IOU_THRESHOLD):
    """candidates: list of (bbox, conf, type_label). Cross-class dedup - see NCERT script notes."""
    if not candidates:
        return []
    sorted_candidates = sorted(candidates, key=lambda x: x[1], reverse=True)
    kept = []
    for bbox, conf, type_label in sorted_candidates:
        if not any(compute_iou(bbox, k[0]) > iou_threshold for k in kept):
            kept.append((bbox, conf, type_label))
    return kept


def crop_region(page_bgr, xmin, ymin, xmax, ymax, width, height):
    xmin, ymin = max(0, int(xmin)), max(0, int(ymin))
    xmax, ymax = min(width, int(xmax)), min(height, int(ymax))
    if xmax <= xmin or ymax <= ymin:
        return None
    crop = page_bgr[ymin:ymax, xmin:xmax]
    return crop if crop.size > 0 else None


def find_nearest_neighbor_edge(bbox, other_boxes, direction='below'):
    el_xmin, el_ymin, el_xmax, el_ymax = bbox
    best_edge = None
    for o_xmin, o_ymin, o_xmax, o_ymax in other_boxes:
        horizontal_overlap = max(0, min(el_xmax, o_xmax) - max(el_xmin, o_xmin))
        if horizontal_overlap <= 0:
            continue
        if direction == 'below' and o_ymin >= el_ymax:
            if best_edge is None or o_ymin < best_edge:
                best_edge = o_ymin
        elif direction == 'above' and o_ymax <= el_ymin:
            if best_edge is None or o_ymax > best_edge:
                best_edge = o_ymax
    return best_edge


# -------------------------------------------------------------------
# Gemini helpers
# -------------------------------------------------------------------
def _image_to_data_url(cropped_image_bgr):
    rgb_image = cv2.cvtColor(cropped_image_bgr, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(rgb_image)
    buffer = io.BytesIO()
    pil_img.save(buffer, format="JPEG")
    import base64
    b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/jpeg;base64,{b64}"


def extract_text_via_gemini(cropped_image_bgr):
    """Generic OCR transcription - used for nearby heading text, no content filtering."""
    try:
        data_url = _image_to_data_url(cropped_image_bgr)
        message = HumanMessage(content=[
            {"type": "text", "text": "Transcribe the exact text from this document snippet. "
                                      "Do not include any extra commentary. Return only the extracted text."},
            {"type": "image_url", "image_url": {"url": data_url}},
        ])
        response = gemini_chain.invoke([message])
        text_output = response.content if hasattr(response, 'content') else str(response)
        if isinstance(text_output, list):
            text_output = " ".join(c.get('text', '') if isinstance(c, dict) else str(c) for c in text_output)
        return text_output.strip()
    except Exception as e:
        print(f"  Gemini OCR failure: {e}")
        return ""


def is_mostly_solid_color(cropped_image_bgr, max_significant_colors=2, downscale=48,
                           quantize_step=32, min_fraction=0.03):
    """
    Cheap heuristic pre-filter: quiz-option buttons, UI boxes, and colored text
    banners (like "Supervised Learning" on a solid blue rectangle) are almost
    always just TWO significant colors - the background fill and the text color.
    Real diagrams/flowcharts/charts have several distinct fill colors, outlines,
    and a white background, so they land well above that count.

    Downscales the crop, quantizes colors into coarse buckets, and counts how many
    buckets cover at least `min_fraction` of the image. If that count is at or
    below `max_significant_colors`, this is very likely a plain button/box, not a
    diagram - skip it WITHOUT spending a Gemini call at all.

    (Empirically: simulated quiz buttons scored 2 significant colors; a simple
    3-box arrow diagram scored 4. Real textbook diagrams will generally score
    higher still due to white background + line art + multiple fills.)
    """
    if cropped_image_bgr is None or cropped_image_bgr.size == 0:
        return False
    small = cv2.resize(cropped_image_bgr, (downscale, downscale), interpolation=cv2.INTER_AREA)
    pixels = small.reshape(-1, 3)
    quantized = (pixels // quantize_step) * quantize_step
    _, counts = np.unique(quantized, axis=0, return_counts=True)
    significant = (counts / counts.sum()) >= min_fraction
    return int(significant.sum()) <= max_significant_colors


def judge_table_relevance(cropped_image_bgr, nearby_heading_text=""):
    """
    Same idea as judge_figure_relevance, but for tables. Not every bordered grid
    is worth extracting - this document's lesson-plan header table (Lesson Title /
    Approach / Summary / Learning Objectives / Learning Outcomes / Pre-requisites /
    Key-concepts) is administrative boilerplate that repeats at the start of every
    unit, not genuine subject content. Real content tables (comparisons, data
    examples, structured facts) should still always be kept.

    Returns dict: {"keep": bool, "caption": str, "reason": str}
    Fails safe: on any error/parse failure, keep=True (tables are far more likely
    to be genuine content than figures are, so the safe default here is inverted
    relative to judge_figure_relevance - we'd rather over-extract a table than
    silently drop real content on a transient API hiccup).
    """
    try:
        data_url = _image_to_data_url(cropped_image_bgr)
        context_line = f'Nearby heading text on the page: "{nearby_heading_text}"' if nearby_heading_text \
            else "No nearby heading text was detected."

        prompt = (
            "You are curating a table bank from an AI/ML training textbook so a question-writer "
            "can generate exam questions from meaningful tables later.\n\n"
            "Look at the attached table image and decide:\n"
            "1. is_content_table: true if this is a genuine subject-matter table - a comparison table "
            "(e.g. Supervised vs Unsupervised Learning), a data example table, a structured list of facts, "
            "or any table a student could be tested on. false if this is a LESSON-METADATA / administrative "
            "table containing lesson-plan header fields such as 'Lesson Title', 'Approach', 'Summary', "
            "'Learning Objectives', 'Learning Outcomes', 'Pre-requisites', 'Key-concepts' - this kind of "
            "boilerplate header table appears at the start of every unit and carries no testable subject content.\n"
            "2. caption: if is_content_table is true, a short 5-12 word descriptive caption/title for the "
            "table grounded in what it actually shows. Empty string if false.\n"
            "3. reason: one brief sentence explaining the decision.\n\n"
            f"{context_line}\n\n"
            "Respond with ONLY a raw JSON object, no markdown fences, no extra text, in exactly this shape:\n"
            '{"is_content_table": true, "caption": "...", "reason": "..."}'
        )

        message = HumanMessage(content=[
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": data_url}},
        ])
        response = gemini_chain.invoke([message])
        text_output = response.content if hasattr(response, 'content') else str(response)
        if isinstance(text_output, list):
            text_output = " ".join(c.get('text', '') if isinstance(c, dict) else str(c) for c in text_output)

        cleaned = re.sub(r'^```(?:json)?', '', text_output.strip()).strip()
        cleaned = re.sub(r'```$', '', cleaned).strip()
        parsed = json.loads(cleaned)
        return {
            "keep": bool(parsed.get("is_content_table", True)),
            "caption": (parsed.get("caption") or "").strip(),
            "reason": (parsed.get("reason") or "").strip(),
        }
    except Exception as e:
        print(f"  Table relevance-check failure (fails safe to KEEP): {e}")
        return {"keep": True, "caption": "", "reason": f"judge_failed_defaulted_keep: {e}"}


def judge_figure_relevance(cropped_image_bgr, nearby_heading_text=""):
    """
    Sends the cropped FIGURE to Gemini vision and asks it to decide whether the
    image carries real educational/conceptual content (diagrams, flowcharts, block
    diagrams, screenshots of relevant tools, labeled process illustrations) worth
    extracting for question generation, versus purely decorative content (stock
    photos, generic clip-art, cartoon icons with no informational payload).

    Returns dict: {"keep": bool, "caption": str, "reason": str}
    Fails safe: on any error/parse failure, keep=False (skip) rather than risk
    flooding the output folder with unjudged images.
    """
    try:
        data_url = _image_to_data_url(cropped_image_bgr)
        context_line = f'Nearby heading text on the page (may or may not relate to this exact image): "{nearby_heading_text}"' \
            if nearby_heading_text else "No nearby heading text was detected."

        prompt = (
            "You are curating an image bank from an AI/ML training textbook so a question-writer "
            "can generate exam questions from meaningful figures later.\n\n"
            "Look at the attached image and decide:\n"
            "1. is_diagram_or_chart: true if this is a conceptual diagram, flowchart, block diagram, "
            "graph, comparison chart, labeled process illustration, or a screenshot of relevant software/output "
            "that conveys information a student could be tested on. false if it is decorative clip art, a generic "
            "stock photo, a small icon, a cartoon illustration used purely for visual appeal, OR a plain colored "
            "rectangular UI button/box containing only a short phrase (e.g. a multiple-choice quiz option button "
            "like 'Supervised Learning' or 'Classification' on a solid color background, an answer-choice button, "
            "or any other interactive-looking UI element) - these are NOT diagrams even though they are boxed and "
            "colored, since they carry no diagram content, just a label.\n"
            "2. caption: if is_diagram_or_chart is true, a short 5-12 word descriptive caption/title for the "
            "image grounded in what it actually shows. Empty string if false.\n"
            "3. reason: one brief sentence explaining the decision.\n\n"
            f"{context_line}\n\n"
            "Respond with ONLY a raw JSON object, no markdown fences, no extra text, in exactly this shape:\n"
            '{"is_diagram_or_chart": true, "caption": "...", "reason": "..."}'
        )

        message = HumanMessage(content=[
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": data_url}},
        ])
        response = gemini_chain.invoke([message])
        text_output = response.content if hasattr(response, 'content') else str(response)
        if isinstance(text_output, list):
            text_output = " ".join(c.get('text', '') if isinstance(c, dict) else str(c) for c in text_output)

        cleaned = text_output.strip()
        cleaned = re.sub(r'^```(?:json)?', '', cleaned).strip()
        cleaned = re.sub(r'```$', '', cleaned).strip()

        parsed = json.loads(cleaned)
        return {
            "keep": bool(parsed.get("is_diagram_or_chart", False)),
            "caption": (parsed.get("caption") or "").strip(),
            "reason": (parsed.get("reason") or "").strip(),
        }
    except Exception as e:
        print(f"  Relevance-check failure (fails safe to SKIP): {e}")
        return {"keep": False, "caption": "", "reason": f"judge_failed: {e}"}


def find_nearby_heading(bbox, other_element_boxes, page_bgr, width, height,
                         max_search=HEADING_SEARCH_MAX, margin_ratio=HEADING_MARGIN_RATIO):
    """
    Generic (non-Fig/Table-pattern) heading finder: OCRs whatever text sits directly
    above the element (bold section headings in this document sit ABOVE, not below,
    e.g. "Object Classification", "Block Representation - Machine Learning (ML)"),
    bounded by the nearest neighboring figure/table edge so it never bleeds into a
    different image's own heading. Falls back to searching below if nothing found above.
    No content filtering - whatever text is there becomes the candidate title, trimmed
    to the first line since these headings are always short.
    """
    el_xmin, el_ymin, el_xmax, el_ymax = bbox
    el_w = el_xmax - el_xmin
    margin = el_w * margin_ratio

    def grab(direction):
        if direction == 'above':
            edge = find_nearest_neighbor_edge(bbox, other_element_boxes, 'above')
            top = max(edge, el_ymin - max_search) if edge is not None else max(0, el_ymin - max_search)
            crop = crop_region(page_bgr, el_xmin - margin, top, el_xmax + margin, el_ymin, width, height)
        else:
            edge = find_nearest_neighbor_edge(bbox, other_element_boxes, 'below')
            bottom = min(edge, el_ymax + max_search) if edge is not None else min(height, el_ymax + max_search)
            crop = crop_region(page_bgr, el_xmin - margin, el_ymax, el_xmax + margin, bottom, width, height)
        if crop is None:
            return ""
        text = extract_text_via_gemini(crop)
        # Headings in this doc are short - keep just the first line to avoid grabbing
        # a whole paragraph if the crop overshoots into body text.
        return text.split("\n")[0].strip()[:120] if text else ""

    heading = grab('above')
    if not heading:
        heading = grab('below')
    return heading


# -------------------------------------------------------------------
# Main Pipeline Execution (callable, for use by a dispatcher/orchestrator)
# -------------------------------------------------------------------
def run(pdf_path=PDF_PATH, poppler_path=POPPLER_PATH,
        output_figures_dir=OUTPUT_FIGURES_DIR, output_tables_dir=OUTPUT_TABLES_DIR):
    os.makedirs(output_figures_dir, exist_ok=True)
    os.makedirs(output_tables_dir, exist_ok=True)

    print("Rendering PDF pages at 300 DPI...")
    pages = convert_from_path(pdf_path, dpi=300, poppler_path=poppler_path)
    print(f"Loaded {len(pages)} pages. Starting detection extraction...")

    figure_counter = 1
    table_counter = 1

    for page_idx, page_image in enumerate(pages):
        page_num = page_idx + 1
        width, height = page_image.size
        print(f"\nProcessing Page {page_num}/{len(pages)}...")

        page_np = np.array(page_image)
        page_bgr = cv2.cvtColor(page_np, cv2.COLOR_RGB2BGR)
        results = layout_model(page_bgr, verbose=False, conf=0.25)[0]

        raw_candidates = []
        for box in results.boxes:
            cls_id = int(box.cls[0])
            label = results.names[cls_id].lower()
            coords = box.xyxy[0].tolist()
            conf = float(box.conf[0]) if hasattr(box, 'conf') else 1.0
            box_w, box_h = coords[2] - coords[0], coords[3] - coords[1]
            box_area = box_w * box_h

            if 'table' in label:
                if box_h > 60 and box_w > 60:
                    raw_candidates.append((coords, conf, 'table'))
            elif any(x in label for x in ['figure', 'picture', 'diagram']):
                if box_h > 70 and box_w > 70 and box_area > 9000:
                    raw_candidates.append((coords, conf, 'figure'))

        deduped = dedup_mixed_type_boxes(raw_candidates)
        tables = [b for b, c, t in deduped if t == 'table']
        figures = [b for b, c, t in deduped if t == 'figure']

        all_elements = [('table', b) for b in tables] + [('figure', b) for b in figures]
        element_boxes = [b for _, b in all_elements]

        for e_idx, (predicted_type, bbox) in enumerate(all_elements):
            other_boxes = [b for i, b in enumerate(element_boxes) if i != e_idx]
            heading_text = find_nearby_heading(bbox, other_boxes, page_bgr, width, height)

            expanded_bbox = expand_bbox(bbox, width, height, padding_percentage=0.03)
            ex_xmin, ex_ymin, ex_xmax, ex_ymax = expanded_bbox
            cropped_asset = page_bgr[ex_ymin:ex_ymax, ex_xmin:ex_xmax]
            if cropped_asset.size == 0:
                continue

            if predicted_type == 'table':
                verdict = judge_table_relevance(cropped_asset, heading_text)
                if not verdict["keep"]:
                    print(f"-> Skipped table on Page {page_num} (lesson-metadata/administrative, not content): {verdict['reason'][:80]}")
                    continue

                caption_text = verdict["caption"] or heading_text or f"Table (untitled, page {page_num})"
                tbl_path = os.path.join(output_tables_dir, f"table_{table_counter}.jpg")
                txt_path = os.path.join(output_tables_dir, f"table_{table_counter}_caption.txt")
                cv2.imwrite(tbl_path, cropped_asset)
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(caption_text)
                print(f"-> Saved Table {table_counter}: {caption_text[:60]}  (reason: {verdict['reason'][:60]})")
                table_counter += 1

            else:  # figure - gated by cheap heuristic first, then AI relevance judgment
                if is_mostly_solid_color(cropped_asset):
                    print(f"-> Skipped figure on Page {page_num} (solid-color heuristic - likely a UI button/box, no Gemini call spent)")
                    continue

                verdict = judge_figure_relevance(cropped_asset, heading_text)
                if not verdict["keep"]:
                    print(f"-> Skipped figure on Page {page_num} (decorative/no content): {verdict['reason'][:80]}")
                    continue

                caption_text = verdict["caption"] or heading_text or f"Figure (untitled, page {page_num})"
                img_path = os.path.join(output_figures_dir, f"figure_{figure_counter}.jpg")
                txt_path = os.path.join(output_figures_dir, f"figure_{figure_counter}_caption.txt")
                cv2.imwrite(img_path, cropped_asset)
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(caption_text)
                print(f"-> Saved Figure {figure_counter}: {caption_text[:60]}  (reason: {verdict['reason'][:60]})")
                figure_counter += 1

    print("\nProcessing Complete! AI-judged relevance filtering successfully executed.")
    return {"figures_saved": figure_counter - 1, "tables_saved": table_counter - 1}


if __name__ == "__main__":
    run()