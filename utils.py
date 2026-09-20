import re

PDF_PATH = "10 ma.pdf"
SUBJECT_NAME = "Artificial Intelligence"
GRADE_LEVEL = 10
CHAPTER_NAME = "Cartisan and Coordination "
CHAPTER_NUMBER = 1
TEXTBOOK_REF = "NCERT - Textbook based"
SOURCE_TEXTBOOK_URL = "AI -Dummy URL"

def get_language_specific_instructions(subject_name):
    if subject_name.lower() == "sanskrit":
        return """
----------------------------------
SANSKRIT LANGUAGE & ENCODING RULES
----------------------------------
1. SCRIPT: All Sanskrit text must be generated natively in the Devanagari script (देवनागरी लिप्यन्तरणम्).
2. LEVEL: Strictly match CBSE Class 10 grammar, syntax, and vocabulary constraints.
3. EXPLANATIONS: Write all 'explanationAnswer' and 'explanationQuestion' values in clear English to explain the underlying Sanskrit grammatical rule applied.
4. JSON ESCAPING: Do not use backslashes or unicode escape characters for Devanagari text. Output raw UTF-8 text characters directly inside the strings."""

    return ""

def load_topics(topics_file="topics.txt"):
    topics = []

    with open(topics_file, "r", encoding="utf-8") as f:
        topics_output = f.read()

    for line in topics_output.splitlines():
        line = line.strip()

        if re.match(r'^\d+\.', line):
            line = re.sub(r'^\d+\.\s*', '', line)
            topics.append(line)

    return topics

import shutil
import os

def reset_folder(folder):
    if os.path.exists(folder):
        shutil.rmtree(folder)
    os.makedirs(folder, exist_ok=True)

import os
import json


def combine_jsons(
    input_folder,
    output_file,
    subject_name,
    grade_level,
    chapter_name,
    chapter_number,
    textbook_ref
):
    """
    Combines all JSON files in a folder into one master JSON.
    Handles nested lists inside questions arrays.
    """

    master_json = {
        "subject": subject_name,
        "grade": grade_level,
        "chapterName": chapter_name,
        "chapterNumber": chapter_number,
        "textbookRef": textbook_ref,
        "questions": []
    }

    merged_files = 0
    skipped_files = 0
    nested_fixed = 0

    if not os.path.exists(input_folder):
        raise FileNotFoundError(f"Folder not found: {input_folder}")
    
    for root, _, files in os.walk(input_folder):

        for filename in sorted(files):

            if not filename.endswith(".json"):
                continue

            filepath = os.path.join(root, filename)

            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)

                if isinstance(data, dict) and "questions" in data:
                    for item in data["questions"]:
                        if isinstance(item, list):
                            # Nested batch — flatten it in
                            master_json["questions"].extend(item)
                            nested_fixed += len(item)
                            print(f"  ⚠ Flattened nested batch of {len(item)} questions in {filename}")
                        elif isinstance(item, dict):
                            master_json["questions"].append(item)
                        else:
                            print(f"  ⚠ Skipped unknown item type {type(item)} in {filename}")

                    merged_files += 1
                    print(f"✓ Added {filename}")

                else:
                    print(f"⚠ Skipped {filename} (missing 'questions')")
                    skipped_files += 1

            except Exception as e:
                print(f"⚠ Could not read {filename}: {e}")
                skipped_files += 1

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(master_json, f, indent=2, ensure_ascii=False)

    print("\n========== Merge Summary ==========")
    print(f"Files merged   : {merged_files}")
    print(f"Files skipped  : {skipped_files}")
    print(f"Nested batches fixed : {nested_fixed} questions")
    print(f"Total questions: {len(master_json['questions'])}")
    print(f"Saved to       : {output_file}")
    print("===================================\n")

    return output_file

SUBJECT_CATEGORIES = {

    "Science": [
        "Recall",
        "Comprehension",
        "Application",
        "Analysis",
        "Evaluation",
        "Case-Study",
        "Assertion-Reason",
        "Competency-Based",
        "HOTS",
        "Source-Based",
        "Practical-Experimental",
        "Visual-Interpretation",
        "Data-Interpretation"
    ],

    "Mathematics": [
        "Recall",
        "Comprehension",
        "Application",
        "Analysis",
        "Evaluation",
        "Case-Study",
        "Assertion-Reason",
        "Competency-Based",
        "HOTS",
        "Visual-Interpretation",
        "Data-Interpretation"
    ],

    "English": [
        "Recall",
        "Comprehension",
        "Application",
        "Analysis",
        "Evaluation",
        "Case-Study",
        "Competency-Based",
        "HOTS",
        "Source-Based",
        "Writing-Skills"
    ],

    "Social Science": [
        "Recall",
        "Comprehension",
        "Application",
        "Analysis",
        "Evaluation",
        "Case-Study",
        "Assertion-Reason",
        "Competency-Based",
        "HOTS",
        "Source-Based",
        "Map-Based",
        "Visual-Interpretation",
        "Data-Interpretation"
    ],

    "Sanskrit": [
        "Recall",
        "Comprehension",
        "Application",
        "Analysis",
        "Evaluation",
        "Competency-Based",
        "HOTS",
        "Source-Based",
        "Writing-Skills"
    ],

    "Artificial Intelligence": [
        "Recall",
        "Comprehension",
        "Application",
        "Analysis",
        "Evaluation",
        "Case-Study",
        "Assertion-Reason",
        "Competency-Based",
        "HOTS",
        "Source-Based",
        "Visual-Interpretation",
        "Data-Interpretation",
        "Practical-Experimental"
    ]
}

def get_allowed_categories(subject_name):
    return SUBJECT_CATEGORIES.get(subject_name, [])

CATEGORY_BATCHES = {

    "Science": {
        "Batch_1_Foundational_Core": [
            "Recall",
            "Comprehension",
            "Application"
        ],
        "Batch_2_Advanced_Cognitive": [
            "Analysis",
            "Evaluation",
            "HOTS"
        ],
        "Batch_3_Contextual_Logic": [
            "Case-Study",
            "Assertion-Reason",
            "Competency-Based"
        ],
        "Batch_4_Applied_Data_Practical": [
            "Source-Based",
            "Practical-Experimental"
        ]
    },

    "Mathematics": {
        "Batch_1_Foundational_Core": [
            "Recall",
            "Comprehension",
            "Application"
        ],
        "Batch_2_Advanced_Cognitive": [
            "Analysis",
            "Evaluation",
            "HOTS"
        ],
        "Batch_3_Contextual_Logic": [
            "Case-Study",
            "Assertion-Reason",
            "Competency-Based"
        ],
        # "Batch_4_Applied_Data_Practical": [
        #     "Data-Interpretation",
        #     "Visual-Interpretation"
        # ]
    },

    "English": {
        "Batch_1_Foundational_Core": [
            "Recall",
            "Comprehension",
            "Application"
        ],
        "Batch_2_Advanced_Cognitive": [
            "Analysis",
            "Evaluation",
            "HOTS"
        ],
        "Batch_3_Contextual_Logic": [
            "Case-Study",
            "Competency-Based"
        ],
        "Batch_4_Language_Skills": [
            "Source-Based",
            "Writing-Skills"
        ]
    },

    "Social Science": {
        "Batch_1_Foundational_Core": [
            "Recall",
            "Comprehension",
            "Application"
        ],
        "Batch_2_Advanced_Cognitive": [
            "Analysis",
            "Evaluation",
            "HOTS"
        ],
        "Batch_3_Contextual_Logic": [
            "Case-Study",
            "Assertion-Reason",
            "Competency-Based"
        ],
        "Batch_4_Applied_Data_Practical": [
            "Source-Based",
            "Map-Based"
        ]
    },

    "Sanskrit": {
        "Batch_1_Foundational_Core": [
            "Recall",
            "Comprehension",
            "Application"
        ],
        "Batch_2_Advanced_Cognitive": [
            "Analysis",
            "Evaluation",
            "HOTS"
        ],
        "Batch_3_Contextual_Logic": [
            "Competency-Based"
        ],
        "Batch_4_Language_Skills": [
            "Source-Based",
            "Writing-Skills"
        ]
    },

    "Artificial Intelligence": {
        "Batch_1_Foundational_Core": [
            "Recall",
            "Comprehension",
            "Application"
        ],
        "Batch_2_Advanced_Cognitive": [
            "Analysis",
            "Evaluation",
            "HOTS"
        ],
        "Batch_3_Contextual_Logic": [
            "Case-Study",
            "Assertion-Reason",
            "Competency-Based"
        ],
        "Batch_4_Applied_Data_Practical": [
            "Source-Based",
            "Practical-Experimental"
        ]
    }
}

def get_category_batches(subject_name):
    if subject_name not in CATEGORY_BATCHES:
        raise ValueError(f"Unsupported subject: {subject_name}")
    return CATEGORY_BATCHES[subject_name]


def get_valid_categories(subject_name):
    categories = []
    for batch in CATEGORY_BATCHES[subject_name].values():
        categories.extend(batch)
    return categories