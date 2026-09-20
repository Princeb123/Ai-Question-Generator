import logging
import os
from google import genai
from google.genai.errors import APIError
from dotenv import load_dotenv
from utils import PDF_PATH,SUBJECT_NAME,GRADE_LEVEL,CHAPTER_NAME,CHAPTER_NUMBER,TEXTBOOK_REF,SOURCE_TEXTBOOK_URL
from upload_file import upload_file
from extract_topics import extract_topics
from extract_concepts import extract_concepts
from run_extraction import run_extraction
from generate_visual import generate_visual
from generate_objective import generate_tbfull
from generate_subjective import generate_subjective
from generate_data import generate_table_questions
from generate_TBselected import generate_tbselected
from generate_TBreversed import generate_tbreversed
from genreate_Indirect import generate_indirect
from utils import load_topics,combine_jsons,reset_folder
from validate import validate_file

class SafeStreamHandler(logging.StreamHandler):
    def emit(self, record):
        try:
            super().emit(record)
        except OSError:
            pass


# Configure logging: writes logs with timestamps to pipeline.log and stdout
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("pipeline.log", encoding="utf-8"),
        SafeStreamHandler()
    ]
)

logging.info("Pipeline started.")

load_dotenv(dotenv_path=".env.local")

key = os.getenv("GEMINI_API_KEY")


def ensure_generated_output(path, stage, topic):
    if not path: 
        raise RuntimeError(
            f"{stage} generation failed for topic '{topic}'. No output file was created."
        )
    return path


modelChain = [
    'gemini-3.6-flash',
    'gemini-3.1-flash',
    'gemini-3.1-flash-lite',
    'gemini-3.5-flash',
    'gemini-3-flash'
]

base = f"output"

logging.info("Resetting output directories...")
reset_folder(f"{base}/tbselected")
reset_folder(f"{base}/extra")
reset_folder(f"{base}/tbreversed")
reset_folder(f"{base}/indirect")
reset_folder(f"{base}/tbfull")
reset_folder(f"{base}/final")
reset_folder("images")
reset_folder("tables")

client = genai.Client(api_key=key)

SAFE_CHAPTER_NAME = CHAPTER_NAME.replace("/", "-")

VISUAL_SUBJECTS = {
    "Science",
    "Mathematics",
    "Social Science",
    "Artificial Intelligence"
}

USE_VISUAL_PIPELINE = SUBJECT_NAME in VISUAL_SUBJECTS

logging.info(f"Uploading file: {PDF_PATH}")
uploaded_file = upload_file(
    client,
    PDF_PATH
)

if USE_VISUAL_PIPELINE:
    logging.info("Running visual pipeline topics/concepts extraction...")
    extract_topics(
        client,
        modelChain,
        uploaded_file
    )

    extract_concepts(
        client,
        uploaded_file,
        "topics.txt",
        SUBJECT_NAME
    )

    topics = load_topics("topics.txt")

else:
    logging.info("Running standard pipeline concepts extraction...")
    topics = ["Entire Chapter"]

    extract_concepts(
        client,
        uploaded_file,
        topics,
        SUBJECT_NAME       
    )

obj_rules = upload_file(
        client,
        "obj_rules.txt"
)

subj_rules = upload_file(
        client,
        "subj_rules.txt"
)

topics = load_topics("topics.txt")
# topics = ["Entire Chapter"]

with open("concepts.txt","r",encoding="utf-8") as f:
            concepts_output=f.read()

for topic in topics:

    logging.info(f"Generating tbfull & subjective for topic: {topic}")

    filename = generate_tbfull(
        client,
        modelChain,
        uploaded_file,
        concepts_output,
        obj_rules,
        topic,
        SUBJECT_NAME,
        GRADE_LEVEL,
        CHAPTER_NAME,
        CHAPTER_NUMBER,
        TEXTBOOK_REF,
        SOURCE_TEXTBOOK_URL
    )
    if filename:
        validate_file(
            filename,
            SUBJECT_NAME,
            gemini_client=client,
            model_chain=modelChain,
            source_type="TB-Full"
        )
    else:
        logging.warning(f"tbfull generation returned None for topic '{topic}', skipping validation")

    filename=generate_subjective(
        client,
        modelChain,
        uploaded_file,
        concepts_output,
        subj_rules,
        topic,
        SUBJECT_NAME,
        GRADE_LEVEL,
        CHAPTER_NAME,
        CHAPTER_NUMBER,
        TEXTBOOK_REF,
        SOURCE_TEXTBOOK_URL
    )
    if filename:
        validate_file(
            filename,
            SUBJECT_NAME,
            gemini_client=client,
            model_chain=modelChain,
            source_type="TB-Full"
        )
    else:
        logging.warning(f"subjective generation returned None for topic '{topic}', skipping validation")

    
if USE_VISUAL_PIPELINE:
    logging.info("Processing visual elements (images & tables)...")
    run_extraction(pdf_path=PDF_PATH, subject_name=SUBJECT_NAME)
    
    filename = generate_visual(
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
    if filename:
        validate_file(
            filename,
            SUBJECT_NAME,
            gemini_client=client,
            model_chain=modelChain,
            source_type="TB-Full"
        )
    
    generate_table_questions(
        client,
        modelChain,
        uploaded_file,
        "concepts.txt",
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

    if filename:
        validate_file(
            filename,
            SUBJECT_NAME,
            gemini_client=client,
            model_chain=modelChain,
            source_type="TB-Full"
        )

logging.info("Combining JSONs for tbfull...")
combine_jsons(
        input_folder="output/tbfull",
        output_file=f"output/final/{SAFE_CHAPTER_NAME}_tbfull.json",
        subject_name=SUBJECT_NAME,
        grade_level=GRADE_LEVEL,
        chapter_name=CHAPTER_NAME,
        chapter_number=CHAPTER_NUMBER,
        textbook_ref=TEXTBOOK_REF
)

logging.info("Generating tbselected & extra questions...")
generate_tbselected(
    client,
    modelChain,
    SUBJECT_NAME,
    input_folder="output/tbfull",
    output_folder_selected="output/tbselected",
    output_folder_extra="output/extra"
)

combine_jsons(
    input_folder="output/tbselected",
    output_file=f"output/final/{SAFE_CHAPTER_NAME}_tbselected.json",
    subject_name=SUBJECT_NAME,
    grade_level=GRADE_LEVEL,
    chapter_name=CHAPTER_NAME,
    chapter_number=CHAPTER_NUMBER,
    textbook_ref=TEXTBOOK_REF
)

combine_jsons(
    input_folder="output/extra",
    output_file=f"output/final/{SAFE_CHAPTER_NAME}_tbextra.json",
    subject_name=SUBJECT_NAME,
    grade_level=GRADE_LEVEL,
    chapter_name=CHAPTER_NAME,
    chapter_number=CHAPTER_NUMBER,
    textbook_ref=TEXTBOOK_REF
)

logging.info("Generating tbreversed questions...")
generate_tbreversed(
    client,
    modelChain,
    SUBJECT_NAME,
    input_folder="output/tbselected",
    output_folder="output/tbreversed",
    min_coverage_ratio=0.95,
)

combine_jsons(
    input_folder="output/tbreversed",
    output_file=f"output/final/{SAFE_CHAPTER_NAME}_tbreversed.json",
    subject_name=SUBJECT_NAME,
    grade_level=GRADE_LEVEL,
    chapter_name=CHAPTER_NAME,
    chapter_number=CHAPTER_NUMBER,
    textbook_ref=TEXTBOOK_REF
)

for topic in topics:

    logging.info(f"Generating indirect questions for topic: {topic}")

    filename = generate_indirect(
        client,
        modelChain,
        uploaded_file,
        concepts_output,
        topic,
        obj_rules,
        subj_rules,
        subject_name=SUBJECT_NAME,
        grade_level=GRADE_LEVEL,
        chapter_name=CHAPTER_NAME,
        chapter_number=CHAPTER_NUMBER,
        textbook_ref=TEXTBOOK_REF,
        source_text_url = SOURCE_TEXTBOOK_URL,
        output_folder="output/indirect")


combine_jsons(
    input_folder="output/indirect",
    output_file=f"output/final/{SAFE_CHAPTER_NAME}_indirect.json",
    subject_name=SUBJECT_NAME,
    grade_level=GRADE_LEVEL,
    chapter_name=CHAPTER_NAME,
    chapter_number=CHAPTER_NUMBER,
    textbook_ref=TEXTBOOK_REF
)

validate_file(
        f"output/final/{SAFE_CHAPTER_NAME}_indirect.json",
        SUBJECT_NAME,
        gemini_client=client,
        model_chain=modelChain,
        source_type="Indirect",
        output_path=f"output/final/{SAFE_CHAPTER_NAME}_indirect.json"
)

try:
    output_path=f"output/final/{SAFE_CHAPTER_NAME}_tbfull.json"
    os.remove(output_path)
    logging.info(f"Deleted {output_path}")
except FileNotFoundError:
    pass

combine_jsons(
    input_folder="output/final",
    output_file=f"output/final/{SAFE_CHAPTER_NAME}_merged.json",
    subject_name=SUBJECT_NAME,
    grade_level=GRADE_LEVEL,
    chapter_name=CHAPTER_NAME,
    chapter_number=CHAPTER_NUMBER,
    textbook_ref=TEXTBOOK_REF
)

logging.info("Pipeline execution completed successfully.")
 