"""
resume_visual.py

Standalone resume script — runs ONLY the visual (images) and data (tables)
question-generation steps against files you've placed manually into the
`images/` and `tables/` folders.

Does NOT call reset_folder() on images/tables, and does NOT call
run_extraction() — so your manually placed files are left untouched.

Usage:
    python resume_visual.py
"""

import os
import logging
from google import genai
from dotenv import load_dotenv

from utils import PDF_PATH, SUBJECT_NAME, GRADE_LEVEL, CHAPTER_NAME, CHAPTER_NUMBER, TEXTBOOK_REF
from upload_file import upload_file
from generate_visual import generate_visual
from generate_data import generate_table_questions
from validate import validate_file

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("pipeline.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logging.info("Resume (visual + tables) started.")

load_dotenv(dotenv_path=".env.local")
key = os.getenv("GEMINI_API_KEY")

modelChain = [
    'gemini-3.6-flash',
    'gemini-3.1-flash',
    'gemini-3.1-flash-lite',
    'gemini-3.5-flash',
    'gemini-3-flash'
]

client = genai.Client(api_key=key)

# Re-upload everything — yesterday's Gemini file handles have likely expired.
logging.info(f"Re-uploading PDF: {PDF_PATH}")
uploaded_file = upload_file(client, PDF_PATH)

obj_rules = upload_file(client, "obj_rules.txt")
subj_rules = upload_file(client, "subj_rules.txt")

with open("concepts.txt", "r", encoding="utf-8") as f:
    concepts_output = f.read()

# ── Images / Visual-Interpretation ──────────────────────────────
logging.info("Generating visual questions from images/ folder...")
visual_filename = generate_visual(
    client,
    modelChain,
    "images",
    obj_rules,
    subj_rules,
    SUBJECT_NAME,
    GRADE_LEVEL,
    CHAPTER_NAME,
    CHAPTER_NUMBER,
    TEXTBOOK_REF,
    output_folder="output/tbfull"
)

if visual_filename:
    logging.info(f"Visual questions written to {visual_filename}, validating...")
    validate_file(
        visual_filename,
        SUBJECT_NAME,
        gemini_client=client,
        model_chain=modelChain,
        source_type="TB-Full"
    )
else:
    logging.warning("generate_visual returned None — no images found or all models failed.")

# ── Tables / Data-Interpretation ────────────────────────────────
logging.info("Generating data questions from tables/ folder...")
table_filename = generate_table_questions(
    client,
    modelChain,
    uploaded_file,
    concepts_output,
    "tables",
    obj_rules,
    subj_rules,
    SUBJECT_NAME,
    GRADE_LEVEL,
    CHAPTER_NAME,
    CHAPTER_NUMBER,
    TEXTBOOK_REF,
    output_folder="output/tbfull"
)

if table_filename:
    logging.info(f"Data questions written to {table_filename}, validating...")
    validate_file(
        table_filename,
        SUBJECT_NAME,
        gemini_client=client,
        model_chain=modelChain,
        source_type="TB-Full"
    )
else:
    logging.warning("generate_table_questions returned None — no tables found or all models failed.")

logging.info("Resume (visual + tables) run completed.")

# NOTE: this only writes new files into output/tbfull. It does NOT re-run
# combine_jsons or touch output/final/..._merged.json. Once you're happy
# with the new visual_mcqs_*.json / data_mcqs_*.json files, either:
#   1) re-run combine_jsons over output/tbfull + regenerate tbselected/
#      tbreversed downstream from it, or
#   2) manually splice the new questions into your existing
#      output/final/..._merged.json "questions" array.
