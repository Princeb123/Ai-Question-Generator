"""
run_extraction.py

Single entry point for the figure/table extraction pipeline. Picks which
underlying pipeline to run based on subject_name:

  - subject_name == "Artificial Intelligence" (case-insensitive, a few common
    spellings accepted) -> pipeline_ai_relevance.py
    (no Fig/Table caption convention in these docs; figures/tables are
    filtered by asking Gemini whether they carry real content)

  - anything else -> pipeline_ncert.py
    (standard NCERT-style Fig X / Table X caption matching pipeline)

IMPORTANT: each pipeline module loads its own DocLayout-YOLO model and Gemini
client chain at import time. To avoid loading BOTH model sets when you only
need one, this dispatcher imports the chosen module LAZILY, inside the
matching branch - not at the top of the file.

Usage:
    python run_extraction.py --pdf "AI-B-2.pdf" --subject "Artificial Intelligence"
    python run_extraction.py --pdf "3-Sci.pdf" --subject "Science"

Or from other code:
    from run_extraction import run_extraction
    run_extraction(pdf_path="AI-B-2.pdf", subject_name="Artificial Intelligence")
"""

import argparse

# Subject-name variants that should route to the AI-relevance pipeline.
# Add more synonyms here as you encounter them across different course catalogs.
AI_SUBJECT_ALIASES = {
    "artificial intelligence",
    "ai",
    "artificial intelligence (ai)",
}

DEFAULT_POPPLER_PATH = (
    r"C:/Users/bhart/AppData/Local/Microsoft/WinGet/Packages/"
    r"oschwartz10612.Poppler_Microsoft.Winget.Source_8wekyb3d8bbwe/"
    r"poppler-25.07.0/Library/bin"
)
DEFAULT_FIGURES_DIR = "images"
DEFAULT_TABLES_DIR = "tables"


def _is_ai_subject(subject_name: str) -> bool:
    return subject_name.strip().lower() in AI_SUBJECT_ALIASES


def run_extraction(pdf_path, subject_name,
                    poppler_path=DEFAULT_POPPLER_PATH,
                    output_figures_dir=DEFAULT_FIGURES_DIR,
                    output_tables_dir=DEFAULT_TABLES_DIR):
    """
    Routes to the correct extraction pipeline based on subject_name and runs it.
    Returns whatever dict the underlying pipeline's run() returns
    (e.g. {"figures_saved": N, "tables_saved": M}).
    """
    if _is_ai_subject(subject_name):
        print(f"[Dispatcher] subject_name='{subject_name}' -> AI-relevance pipeline "
              f"(no Fig/Table caption pattern in these docs; Gemini judges relevance)")
        import extract_imgs_ai as pipeline
    else:
        print(f"[Dispatcher] subject_name='{subject_name}' -> standard NCERT Fig/Table "
              f"caption-matching pipeline")
        import extract_imgs as pipeline

    return pipeline.run(
        pdf_path=pdf_path,
        poppler_path=poppler_path,
        output_figures_dir=output_figures_dir,
        output_tables_dir=output_tables_dir,
    )


def main():
    parser = argparse.ArgumentParser(description="Extract figures/tables from a textbook PDF.")
    parser.add_argument("--pdf", required=True, help="Path to the source PDF.")
    parser.add_argument("--subject", required=True, help="Subject name, e.g. 'Artificial Intelligence' or 'Science'.")
    parser.add_argument("--poppler", default=DEFAULT_POPPLER_PATH, help="Path to poppler bin directory.")
    parser.add_argument("--figures-dir", default=DEFAULT_FIGURES_DIR, help="Output directory for figures.")
    parser.add_argument("--tables-dir", default=DEFAULT_TABLES_DIR, help="Output directory for tables.")
    args = parser.parse_args()

    run_extraction(
        pdf_path=args.pdf,
        subject_name=args.subject,
        poppler_path=args.poppler,
        output_figures_dir=args.figures_dir,
        output_tables_dir=args.tables_dir,
    )


if __name__ == "__main__":
    main()