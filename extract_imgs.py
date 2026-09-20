import os
import io
import re
import cv2
import numpy as np
from PIL import Image
from pdf2image import convert_from_path
from huggingface_hub import hf_hub_download
from doclayout_yolo import YOLOv10
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
from utils import PDF_PATH

# Load API keys
load_dotenv()

# -------------------------------------------------------------------
# Configuration & Initialization
# -------------------------------------------------------------------

POPPLER_PATH = r"D:\ai\poppler-26.08.0\utils"
OUTPUT_FIGURES_DIR = "images"
OUTPUT_TABLES_DIR = "tables"


FIGURE_CAPTION_PATTERN = re.compile(r'\bfig(?:ure)?\.?\s*\d', re.IGNORECASE)
TABLE_CAPTION_PATTERN = re.compile(r'\btable\.?\s*\d', re.IGNORECASE)

# Max acceptable IOU between two detected boxes of the same class before we treat
# them as duplicate detections of the same physical asset.
DEDUP_IOU_THRESHOLD = 0.5

# Max acceptable vertical gap (in px, at 300 DPI) between an asset and its caption.
MAX_CAPTION_GAP = 250

os.makedirs(OUTPUT_FIGURES_DIR, exist_ok=True)
os.makedirs(OUTPUT_TABLES_DIR, exist_ok=True)

# 1. Fetch and Load DocLayout-YOLOv10
print("Loading local DocLayout-YOLOv10 model...")
weights_path = hf_hub_download(
    repo_id="juliozhao/DocLayout-YOLO-DocStructBench",
    filename="doclayout_yolo_docstructbench_imgsz1024.pt"
)
layout_model = YOLOv10(weights_path)

# model pipeline definition
modelChain = [
    'gemini-3.6-flash',
    'gemini-3.1-flash',
    'gemini-3.1-flash-lite',
    'gemini-3.5-flash',
    'gemini-3-flash'
]

# 2. Build the structural LangChain Fallback Queue
print("Initializing Gemini Cloud OCR with failover routing...")

primary_model = ChatGoogleGenerativeAI(model=modelChain[0], temperature=0)

fallback_objects = [
    ChatGoogleGenerativeAI(model=model_name, temperature=0)
    for model_name in modelChain[1:]
]

gemini_ocr_chain = primary_model.with_fallbacks(fallbacks=fallback_objects)

# -------------------------------------------------------------------
# Geometry Helpers
# -------------------------------------------------------------------
def expand_bbox(bbox, width, height, padding_percentage=0.03):
    """Expands bounding box by a given percentage buffer safely."""
    xmin, ymin, xmax, ymax = bbox
    w = xmax - xmin
    h = ymax - ymin

    xmin = max(0, int(xmin - (w * padding_percentage)))
    ymin = max(0, int(ymin - (h * padding_percentage)))
    xmax = min(width, int(xmax + (w * padding_percentage)))
    ymax = min(height, int(ymax + (h * padding_percentage)))

    return [xmin, ymin, xmax, ymax]


def compute_iou(box_a, box_b):
    """Standard IOU between two [xmin, ymin, xmax, ymax] boxes."""
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

    if union <= 0:
        return 0.0
    return inter_area / union


def dedup_mixed_type_boxes(candidates, iou_threshold=DEDUP_IOU_THRESHOLD):
    """
    De-duplicates overlapping detections of the same physical asset ACROSS
    table/figure classes together, not per-class - YOLO sometimes fires two boxes
    for the SAME physical asset with two DIFFERENT class labels (e.g. one 'table'
    box + one 'figure' box on the same table). candidates: list of
    (bbox, conf, type_label). Keeps highest-confidence box in each overlapping
    cluster, regardless of its predicted type.
    """
    if not candidates:
        return []
    sorted_candidates = sorted(candidates, key=lambda x: x[1], reverse=True)
    kept = []
    for bbox, conf, type_label in sorted_candidates:
        is_duplicate = False
        for kept_bbox, _, _ in kept:
            if compute_iou(bbox, kept_bbox) > iou_threshold:
                is_duplicate = True
                break
        if not is_duplicate:
            kept.append((bbox, conf, type_label))
    return kept


def dedup_boxes(boxes_with_conf, iou_threshold=DEDUP_IOU_THRESHOLD):
    """
    Removes duplicate detections of the same physical asset.
    boxes_with_conf: list of (bbox, confidence)
    Keeps the highest-confidence box among any cluster of overlapping boxes.
    """
    if not boxes_with_conf:
        return []

    # Sort by confidence descending so we keep the best box first
    sorted_boxes = sorted(boxes_with_conf, key=lambda x: x[1], reverse=True)
    kept = []

    for bbox, conf in sorted_boxes:
        is_duplicate = False
        for kept_bbox, _ in kept:
            if compute_iou(bbox, kept_bbox) > iou_threshold:
                is_duplicate = True
                break
        if not is_duplicate:
            kept.append((bbox, conf))

    return [b for b, _ in kept]


def vertical_gap_score(element_bbox, caption_bbox):
    """
    Computes a matching score (lower = better) between an element and a caption
    based on edge-to-edge vertical gap, with a horizontal-alignment penalty.
    Returns float('inf') if the pair should never be matched.
    """
    el_xmin, el_ymin, el_xmax, el_ymax = element_bbox
    c_xmin, c_ymin, c_xmax, c_ymax = caption_bbox

    el_cx = (el_xmin + el_xmax) / 2
    c_cx = (c_xmin + c_xmax) / 2

    horizontal_overlap = max(0, min(el_xmax, c_xmax) - max(el_xmin, c_xmin))

    if c_ymin >= el_ymax:
        vertical_gap = c_ymin - el_ymax          # caption below element
    elif el_ymin >= c_ymax:
        vertical_gap = el_ymin - c_ymax          # caption above element
    else:
        vertical_gap = 0                         # overlapping vertically

    if horizontal_overlap == 0:
        horizontal_distance = abs(el_cx - c_cx)
        score = vertical_gap + (horizontal_distance * 0.5)
    else:
        score = vertical_gap

    return score


def is_caption_below(element_bbox, caption_bbox):
    """Direction classification by CENTER position (robust to slight bbox overlap)."""
    el_ymin, el_ymax = element_bbox[1], element_bbox[3]
    c_ymin, c_ymax = caption_bbox[1], caption_bbox[3]
    el_cy = (el_ymin + el_ymax) / 2
    c_cy = (c_ymin + c_ymax) / 2
    return c_cy >= el_cy


def get_preferred_caption_direction(predicted_type):
    """
    NCERT convention differs by asset type:
      - Figures: caption is almost always BELOW the image.
      - Tables: caption/title is often ABOVE the table.
    This is only used to PRIORITIZE search order, not to reject matches outright -
    the non-preferred direction is still tried as a fallback in Pass 2.
    """
    return 'above' if predicted_type == 'table' else 'below'


def assign_captions_globally(elements, element_types, captions, max_gap=MAX_CAPTION_GAP):
    """
    Performs a GLOBAL one-to-one greedy assignment between elements and captions
    on a page, instead of each element picking its nearest caption independently.
    This prevents two nearby elements from fighting over / duplicating the same caption.

    IMPORTANT: pure pixel-distance ranking is NOT reliable here, because an
    element's own caption can sometimes be pixel-wise FARTHER than an unrelated
    caption sitting on the "wrong" side (e.g. the previous figure's caption, if
    that figure's lower margin happens to be tight). So each element's PREFERRED
    direction (below for figures, above for tables - see get_preferred_caption_direction)
    is made a hard priority over raw distance:

      Pass 1: only consider (element, caption) pairs where the caption sits on the
              element's PREFERRED side. Assign these first, closest-first.
      Pass 2: for whatever elements/captions are still unmatched, allow the
              opposite side as a fallback, closest-first.

    elements: list of bbox (any mix of images/tables)
    element_types: list of 'figure'/'table' YOLO-predicted hints, same length/order
                    as elements (used only to bias search priority, never to
                    reject a match outright - final type is still decided later
                    from the caption TEXT itself).
    captions: list of bbox

    Returns: dict {element_index: caption_index}
    """
    preferred_candidates = []
    fallback_candidates = []

    for e_idx, e_box in enumerate(elements):
        preferred_dir = get_preferred_caption_direction(element_types[e_idx])
        for c_idx, c_box in enumerate(captions):
            score = vertical_gap_score(e_box, c_box)
            if score > max_gap:
                continue
            actual_dir = 'below' if is_caption_below(e_box, c_box) else 'above'
            if actual_dir == preferred_dir:
                preferred_candidates.append((score, e_idx, c_idx))
            else:
                fallback_candidates.append((score, e_idx, c_idx))

    preferred_candidates.sort(key=lambda x: x[0])
    fallback_candidates.sort(key=lambda x: x[0])

    assigned_element = {}
    used_captions = set()

    # Pass 1: each element's preferred side gets first claim, closest-first
    for score, e_idx, c_idx in preferred_candidates:
        if e_idx in assigned_element or c_idx in used_captions:
            continue
        assigned_element[e_idx] = c_idx
        used_captions.add(c_idx)

    # Pass 2: only elements/captions still unmatched may pair up via the opposite side
    for score, e_idx, c_idx in fallback_candidates:
        if e_idx in assigned_element or c_idx in used_captions:
            continue
        assigned_element[e_idx] = c_idx
        used_captions.add(c_idx)

    return assigned_element


# -------------------------------------------------------------------
# OCR Helper
# -------------------------------------------------------------------
def extract_text_via_gemini(cropped_image_bgr):
    """Sends the cropped caption image snippet to Gemini with fallback failover protection."""
    try:
        import base64
        rgb_image = cv2.cvtColor(cropped_image_bgr, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb_image)

        buffer = io.BytesIO()
        pil_img.save(buffer, format="JPEG")
        image_bytes = buffer.getvalue()

        base64_encoded = base64.b64encode(image_bytes).decode("utf-8")
        data_url = f"data:image/jpeg;base64,{base64_encoded}"

        message = HumanMessage(
            content=[
                {"type": "text", "text": "Transcribe the exact text from this document snippet. Do not include any extra commentary or introductory phrases. Return only the extracted text."},
                {"type": "image_url", "image_url": {"url": data_url}}
            ]
        )

        response = gemini_ocr_chain.invoke([message])

        if hasattr(response, 'content'):
            text_output = response.content
        else:
            text_output = str(response)

        if isinstance(text_output, list):
            text_output = " ".join(
                [chunk.get('text', '') if isinstance(chunk, dict) else str(chunk) for chunk in text_output]
            )

        return text_output.strip()

    except Exception as e:
        print(f" Gemini OCR Failure Across All Fallbacks: {e}")
        return "OCR Failed"


def pad_bbox_fixed(bbox, width, height, pad_px=12):
    """
    Pads a bbox by a FIXED pixel amount (not percentage) on all sides, clamped to
    page bounds. Used for detected caption boxes: DocLayout-YOLO sometimes draws
    the caption box a few pixels too tight, clipping the first or last word (e.g.
    'Table 9.1 ...' losing the word 'Table' itself). A small fixed pad is more
    reliable here than a percentage pad, since caption boxes are often very short.
    """
    xmin, ymin, xmax, ymax = bbox
    return [
        max(0, int(xmin - pad_px)),
        max(0, int(ymin - pad_px)),
        min(width, int(xmax + pad_px)),
        min(height, int(ymax + pad_px)),
    ]


def crop_region(page_bgr, xmin, ymin, xmax, ymax, width, height):
    """Safely crops a region from the page, clamping to page bounds."""
    xmin = max(0, int(xmin))
    ymin = max(0, int(ymin))
    xmax = min(width, int(xmax))
    ymax = min(height, int(ymax))
    if xmax <= xmin or ymax <= ymin:
        return None
    crop = page_bgr[ymin:ymax, xmin:xmax]
    if crop.size == 0:
        return None
    return crop


# Ceiling on how far below/above an element to search when no caption box was
# detected by YOLO at all AND there's no neighboring element to bound the search.
FALLBACK_MAX_SEARCH = 400
FALLBACK_MARGIN_RATIO = 0.05


def find_nearest_neighbor_edge(bbox, other_boxes, direction='below'):
    """
    Finds the edge of the nearest OTHER element (figure or table) that sits
    directly below/above this one in roughly the same horizontal column.
    Used to bound the fallback caption search so it stops exactly at the start
    of the next figure/table instead of guessing a fixed height.
    """
    el_xmin, el_ymin, el_xmax, el_ymax = bbox
    best_edge = None

    for o_xmin, o_ymin, o_xmax, o_ymax in other_boxes:
        horizontal_overlap = max(0, min(el_xmax, o_xmax) - max(el_xmin, o_xmin))
        if horizontal_overlap <= 0:
            continue  # not in the same column, ignore

        if direction == 'below' and o_ymin >= el_ymax:
            if best_edge is None or o_ymin < best_edge:
                best_edge = o_ymin
        elif direction == 'above' and o_ymax <= el_ymin:
            if best_edge is None or o_ymax > best_edge:
                best_edge = o_ymax

    return best_edge


def try_fallback_caption_ocr(bbox, predicted_type, other_element_boxes, page_bgr, width, height,
                              max_search=FALLBACK_MAX_SEARCH,
                              margin_ratio=FALLBACK_MARGIN_RATIO):
    """
    Last-resort caption recovery for when DocLayout-YOLO simply never emitted a
    caption box near this element (a common miss on non-standard book layouts,
    like short bold 'Fig. 2.6' style captions), OR when a caption sits tightly
    sandwiched between two stacked images/tables.

    Instead of guessing a fixed crop height (which can either overshoot into the
    next figure's artwork, confusing the OCR, or undershoot and miss the caption),
    this bounds the crop by the nearest neighboring element's own edge. That way
    the fallback crop only ever contains the exact whitespace strip between two
    elements - never bleeding into the next figure/table's visual content.

    Search order matches NCERT convention: images are searched below-then-above,
    tables are searched above-then-below (get_preferred_caption_direction).

    It only ever "wins" if the OCR'd text still passes the Fig/Table regex, so it
    can't accidentally pull in unrelated body text.
    """
    el_xmin, el_ymin, el_xmax, el_ymax = bbox
    el_w = el_xmax - el_xmin
    margin = el_w * margin_ratio

    def try_below():
        next_below_edge = find_nearest_neighbor_edge(bbox, other_element_boxes, 'below')
        below_limit = min(next_below_edge, el_ymax + max_search) if next_below_edge is not None \
            else min(height, el_ymax + max_search)
        crop = crop_region(page_bgr, el_xmin - margin, el_ymax, el_xmax + margin, below_limit, width, height)
        if crop is not None:
            text = extract_text_via_gemini(crop)
            # Element is ABOVE this crop -> nearest caption fragment is the FIRST match
            typ, trimmed = extract_best_caption(text, prefer='first')
            if typ is not None:
                return trimmed
        return None

    def try_above():
        next_above_edge = find_nearest_neighbor_edge(bbox, other_element_boxes, 'above')
        above_limit = max(next_above_edge, el_ymin - max_search) if next_above_edge is not None \
            else max(0, el_ymin - max_search)
        crop = crop_region(page_bgr, el_xmin - margin, above_limit, el_xmax + margin, el_ymin, width, height)
        if crop is not None:
            text = extract_text_via_gemini(crop)
            # Element is BELOW this crop -> nearest caption fragment is the LAST match
            typ, trimmed = extract_best_caption(text, prefer='last')
            if typ is not None:
                return trimmed
        return None

    preferred_dir = get_preferred_caption_direction(predicted_type)
    first, second = (try_above, try_below) if preferred_dir == 'above' else (try_below, try_above)

    result = first()
    if result is not None:
        return result
    return second()


def find_caption_matches(text):
    """Returns every Fig/Table match in text as (start_index, type), sorted by position."""
    matches = []
    for m in FIGURE_CAPTION_PATTERN.finditer(text):
        matches.append((m.start(), 'figure'))
    for m in TABLE_CAPTION_PATTERN.finditer(text):
        matches.append((m.start(), 'table'))
    matches.sort(key=lambda x: x[0])
    return matches


def extract_best_caption(text, prefer='first'):
    """
    An OCR'd crop can occasionally contain TWO concatenated captions - e.g. a
    fallback crop bounded only by figure/table edges can still cross through an
    adjacent (already-claimed) caption belonging to a DIFFERENT element. Since
    captions are read top-to-bottom, the fragment nearest the target element is
    always at a predictable end of the text:
      - prefer='first': element is ABOVE the crop (below-search) -> nearest
        fragment is the FIRST match (top of crop = closest to the element).
      - prefer='last':  element is BELOW the crop (above-search) -> nearest
        fragment is the LAST match (bottom of crop = closest to the element).

    Returns (type, trimmed_caption_text) for the nearest match, or (None, None).
    """
    if not text or text == "OCR Failed":
        return None, None

    matches = find_caption_matches(text)
    if not matches:
        return None, None

    if prefer == 'last':
        start_idx, typ = matches[-1]
        end_idx = len(text)
    else:
        start_idx, typ = matches[0]
        end_idx = matches[1][0] if len(matches) > 1 else len(text)

    trimmed = text[start_idx:end_idx].strip()
    return typ, trimmed


def classify_caption(caption_text):
    """
    Decides whether a caption belongs to a FIGURE or a TABLE purely from its text,
    NOT from the YOLO-predicted label. This guarantees no cross-contamination
    between the figures/ and tables/ folders even if YOLO mislabels a box.

    Returns 'figure', 'table', or None (reject).
    """
    typ, _ = extract_best_caption(caption_text, prefer='first')
    return typ


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

        raw_candidates, raw_captions = [], []

        for box in results.boxes:
            cls_id = int(box.cls[0])
            label = results.names[cls_id].lower()
            coords = box.xyxy[0].tolist()  # [xmin, ymin, xmax, ymax]
            conf = float(box.conf[0]) if hasattr(box, 'conf') else 1.0

            box_w = coords[2] - coords[0]
            box_h = coords[3] - coords[1]
            box_area = box_w * box_h

            if 'caption' in label:
                raw_captions.append((coords, conf))
            elif 'table' in label:
                if box_h > 60 and box_w > 60:
                    raw_candidates.append((coords, conf, 'table'))
            elif any(x in label for x in ['figure', 'picture', 'diagram']):
                if box_h > 120 and box_w > 120 and box_area > 20000:
                    raw_candidates.append((coords, conf, 'figure'))

        # ---- De-duplicate overlapping detections of the same physical asset ----
        # IMPORTANT: this must happen ACROSS table/figure classes together, not per-class.
        deduped_candidates = dedup_mixed_type_boxes(raw_candidates)
        raw_tables = [b for b, c, t in deduped_candidates if t == 'table']
        raw_figures = [b for b, c, t in deduped_candidates if t == 'figure']

        # Also dedup caption boxes themselves in case the same caption text region
        # got detected twice
        captions = dedup_boxes(raw_captions, iou_threshold=DEDUP_IOU_THRESHOLD)

        # ---- Drop tables/figures that are really just captions misclassified ----
        def strip_caption_false_positives(boxes, captions):
            cleaned = []
            for box in boxes:
                is_false_positive = False
                for c_box in captions:
                    x_left = max(box[0], c_box[0])
                    y_top = max(box[1], c_box[1])
                    x_right = min(box[2], c_box[2])
                    y_bottom = min(box[3], c_box[3])
                    if x_right > x_left and y_bottom > y_top:
                        intersection_area = (x_right - x_left) * (y_bottom - y_top)
                        box_area = (box[2] - box[0]) * (box[3] - box[1])
                        if box_area > 0 and (intersection_area / box_area) > 0.85:
                            is_false_positive = True
                            break
                if not is_false_positive:
                    cleaned.append(box)
            return cleaned

        tables = strip_caption_false_positives(raw_tables, captions)
        images = strip_caption_false_positives(raw_figures, captions)

        # ---- Combine into one element pool for GLOBAL caption assignment ----
        all_elements = [('table', b) for b in tables] + [('figure', b) for b in images]
        element_boxes = [b for _, b in all_elements]
        element_types = [t for t, _ in all_elements]

        assignment = assign_captions_globally(element_boxes, element_types, captions, max_gap=MAX_CAPTION_GAP)

        for e_idx, (predicted_type, bbox) in enumerate(all_elements):
            c_idx = assignment.get(e_idx)
            caption_text = None
            used_fallback = False

            if c_idx is not None:
                caption_bbox = captions[c_idx]
                padded_caption_bbox = pad_bbox_fixed(caption_bbox, width, height, pad_px=12)
                c_xmin, c_ymin, c_xmax, c_ymax = padded_caption_bbox
                cropped_caption_img = page_bgr[c_ymin:c_ymax, c_xmin:c_xmax]

                if cropped_caption_img.size > 0:
                    raw_text = extract_text_via_gemini(cropped_caption_img)
                    _typ, trimmed = extract_best_caption(raw_text, prefer='first')
                    caption_text = trimmed if trimmed is not None else raw_text

            # If the layout model gave us no caption box at all, OR the caption box it
            # did give us didn't actually contain valid Fig/Table text, fall back to a
            # direct OCR crop below/above the element itself before giving up. This crop
            # is bounded by the nearest neighboring figure/table's own edge, so a caption
            # sandwiched tightly between two stacked images gets captured precisely without
            # bleeding into the next figure's artwork.
            if caption_text is None or classify_caption(caption_text) is None:
                other_element_boxes = [b for i, b in enumerate(element_boxes) if i != e_idx]
                fallback_text = try_fallback_caption_ocr(bbox, predicted_type, other_element_boxes, page_bgr, width, height)
                if fallback_text is not None:
                    caption_text = fallback_text
                    used_fallback = True

            # Decide final type strictly from caption content
            final_type = classify_caption(caption_text) if caption_text else None

            if final_type is None:
                preview = (caption_text or "")[:40]
                print(f"-> Skipped {predicted_type} on Page {page_num}: "
                      f"no valid Fig/Table caption found (last OCR: '{preview}').")
                continue

            # Crop the asset itself
            expanded_bbox = expand_bbox(bbox, width, height, padding_percentage=0.03)
            ex_xmin, ex_ymin, ex_xmax, ex_ymax = expanded_bbox
            cropped_asset = page_bgr[ex_ymin:ex_ymax, ex_xmin:ex_xmax]
            if cropped_asset.size == 0:
                continue

            if final_type == 'figure':
                img_path = os.path.join(output_figures_dir, f"figure_{figure_counter}.jpg")
                txt_path = os.path.join(output_figures_dir, f"figure_{figure_counter}_caption.txt")
                cv2.imwrite(img_path, cropped_asset)
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(caption_text)
                tag = " [fallback OCR]" if used_fallback else ""
                print(f"-> Saved Figure {figure_counter} (YOLO said '{predicted_type}'){tag}: {caption_text[:50]}...")
                figure_counter += 1

            elif final_type == 'table':
                tbl_path = os.path.join(output_tables_dir, f"table_{table_counter}.jpg")
                txt_path = os.path.join(output_tables_dir, f"table_{table_counter}_caption.txt")
                cv2.imwrite(tbl_path, cropped_asset)
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(caption_text)
                tag = " [fallback OCR]" if used_fallback else ""
                print(f"-> Saved Table {table_counter} (YOLO said '{predicted_type}'){tag}: {caption_text[:50]}...")
                table_counter += 1

    print("\nProcessing Complete! Clean local layout with cloud OCR successfully executed.")
    return {"figures_saved": figure_counter - 1, "tables_saved": table_counter - 1}


if __name__ == "__main__":
    run()