import os
import re
import json
import time
from google.genai.errors import APIError
from utils import get_language_specific_instructions
from validate import validate_file


def generate_tbselected(
    client,
    modelChain,
    subject_name,
    input_folder="output/tbfull",
    output_folder_selected="output/tbselected",
    output_folder_extra="output/extra",
    target_ratio=0.50,   # TARGET: keep 40-60% of input questions
):
    """
    Generates TB-Selected JSONs topic-wise.

    Reads every JSON from input_folder,
    sends it to Gemini,
    saves selected questions with the SAME filename.

    """

    os.makedirs(output_folder_selected, exist_ok=True)
    os.makedirs(output_folder_extra, exist_ok=True)
    # Both TB-Selected and TB-Extra files go into the same output/final folder

    json_files = sorted([
        f for f in os.listdir(input_folder)
        if f.endswith(".json")
    ])

    generated_files = []

    for json_file in json_files:

        print("\n==========================================")
        print(f"Processing: {json_file}")
        print("==========================================")

        input_path = os.path.join(input_folder, json_file)

        with open(input_path, "r", encoding="utf-8") as f:
            topic_data = json.load(f)

        all_questions = topic_data.get("questions", [])
        total_input = len(all_questions)

        # CHANGE 1: Compute explicit target count from ratio
        target_min = max(1, int(total_input * 0.40))
        target_max = max(1, int(total_input * 0.60))
        target_ideal = max(1, int(total_input * target_ratio))

        print(f"Input: {total_input} questions | Target: {target_min}-{target_max} (ideal ~{target_ideal})")

        questions_json = json.dumps(
            all_questions,
            indent=2,
            ensure_ascii=False
        )

        topic = topic_data.get("topic", "")
        subject = topic_data.get("subject", "")
        grade = topic_data.get("grade", "")
        chapter_name = topic_data.get("chapterName", "")
        chapter_number = topic_data.get("chapterNumber", "")
        textbook_ref = topic_data.get("textbookRef", "")

        language_instructions = get_language_specific_instructions(subject_name)

        selection_prompt = rf"""
You are an expert CBSE assessment reviewer and question paper designer.

{language_instructions}

Your task is to select the BEST UNIQUE questions from the provided bank.

DO NOT generate new questions.
DO NOT rewrite questions.
DO NOT modify wording.
DO NOT change IDs.
DO NOT change explanations.

Simply REMOVE questions that are redundant, low-quality, or duplicates.

--------------------------------------------------
TARGET COUNT (MANDATORY)
--------------------------------------------------

The input bank has {total_input} questions.

You MUST select between {target_min} and {target_max} questions.
Ideal target: approximately {target_ideal} questions.

This is a hard requirement. Do NOT keep more than {target_max} questions.
Do NOT return fewer than {target_min} questions.

--------------------------------------------------
DUPLICATE REMOVAL RULES (STRICT)
--------------------------------------------------

Two questions ARE duplicates and you must keep only ONE if they:

1. Test the same concept AND the same cognitive level (e.g. both ask
   what the near point of the eye is — even if worded differently).

2. Differ only in: numbers, examples, option order, sentence structure,
   or surface phrasing — but have the same correct answer and the
   same learning objective.

3. Are the same question with different difficulty labels but identical
   content.

When removing a duplicate, keep the one with:
- better/longer distractors
- more detailed explanation
- clearer question stem
- higher cognitive level (prefer Application over Recall for same concept)

--------------------------------------------------
CATEGORY BALANCE RULES
--------------------------------------------------

Category dominance rule:
No single category should exceed 30% of the final selected questions.
If Recall has 60 questions and the total is 133, you must trim Recall
to at most {max(1, int(target_ideal * 0.30))} questions in the output.

--------------------------------------------------
COVERAGE RULES
--------------------------------------------------

Ensure every major concept in the topic has at least one question.
Do NOT allow one concept to have 10 questions while another has 0.
Prioritise concept breadth over concept depth.

--------------------------------------------------
QUESTION TYPE BALANCE
--------------------------------------------------

Maintain a balanced mix whenever available:
mcq, multi, truefalse, fillblanks, matchfollowing, subjective

Do NOT remove an entire question type.

--------------------------------------------------
SOURCE TYPE UPDATE (MANDATORY)
--------------------------------------------------

For EVERY retained question replace:
    "sourceType": "TB-Full"
with:
    "sourceType": "TB-Selected"


This is the ONLY field you are allowed to modify.

All other fields must remain EXACTLY identical to the input.

--------------------------------------------------
OUTPUT FORMAT
--------------------------------------------------

Return ONLY valid JSON with no markdown, no comments, no explanation.

DO NOT return the full question objects.
Return ONLY the IDs of the questions you want to SELECT.

{{
  "selected_ids": ["id1", "id2", "id3", ...],
  "selectionSummary": {{
    "initialCount": {total_input},
    "selectedCount": <number of IDs in selected_ids>,
    "removedCount": <number removed>,
    "removalReasons": {{
      "duplicates": <count>,
      "nonStandardCategory": <count>,
      "categoryOverRepresentation": <count>,
      "lowQuality": <count>
    }}
  }}
}}

Here is the question bank to review:

Topic: {topic}

Questions:
{questions_json}
"""

        current_model_idx = 0
        selected_result = None

        while current_model_idx < len(modelChain):

            model_name = modelChain[current_model_idx]

            try:

                print(f"Requesting {model_name}")

                response = client.models.generate_content(
                    model=model_name,
                    contents=[selection_prompt],
                    config={
                        "response_mime_type": "application/json",
                        "temperature": 0.1
                    }
                )

                selected_result = response.text

                print("Success")

                time.sleep(7)

                break

            except APIError as e:

                print(f"{model_name} exhausted : {e.message}")

                current_model_idx += 1
                time.sleep(7)

            except Exception as e:

                print(e)

                current_model_idx += 1

        if selected_result:

            try:

                # Safe JSON cleaning — strip markdown fences only
                clean_json = selected_result.strip()
                if clean_json.startswith("```"):
                    clean_json = clean_json.split("\n", 1)[-1]
                if clean_json.endswith("```"):
                    clean_json = clean_json.rsplit("```", 1)[0]
                clean_json = clean_json.strip()

                if "{" in clean_json:
                    clean_json = clean_json[
                        clean_json.find("{"):
                        clean_json.rfind("}") + 1
                    ]

                parsed = json.loads(clean_json)

                # LLM returns only selected IDs — much smaller response,
                # eliminates truncation that caused the parse failures
                selected_ids = set(parsed.get("selected_ids", []))
                selection_summary = parsed.get("selectionSummary", {})

                # Derive selected and not_selected locally from the original
                # question objects — no risk of truncation or data loss
                selected_questions = []
                not_selected_questions = []

                for q in all_questions:
                    q_copy = dict(q)
                    if q.get("id") in selected_ids:
                        q_copy["sourceType"] = "TB-Selected"
                        selected_questions.append(q_copy)
                    else:
                        q_copy["sourceType"] = "TB-Extra"
                        not_selected_questions.append(q_copy)

                selected_count = len(selected_questions)
                extra_count = len(not_selected_questions)
                print(f"LLM selected {selected_count} IDs, {extra_count} go to extra (target: {target_min}-{target_max})")
                if selected_count > target_max:
                    print(f"WARNING: LLM exceeded target ({selected_count} > {target_max}). Consider re-running.")
                elif selected_count < target_min:
                    print(f"WARNING: LLM returned fewer than minimum ({selected_count} < {target_min}).")

                # --- Save TB-Selected file ---
                selected_data = dict(topic_data)
                selected_data["questions"] = selected_questions
                selected_data["selectionSummary"] = selection_summary

                selected_filename = json_file.replace(".json", "_TB-Selected.json")
                output_path_selected = os.path.join(output_folder_selected, selected_filename)

                with open(output_path_selected, "w", encoding="utf-8") as f:
                    json.dump(selected_data, f, indent=2, ensure_ascii=False)

                generated_files.append(output_path_selected)
                print(f"Saved TB-Selected: {output_path_selected} ({selected_count} questions)")

                # --- Save TB-Extra file ---
                extra_data = dict(topic_data)
                extra_data["questions"] = not_selected_questions
                extra_data.pop("selectionSummary", None)

                extra_filename = json_file.replace(".json", "_TB-Extra.json")
                extra_path = os.path.join(output_folder_extra, extra_filename)

                with open(extra_path, "w", encoding="utf-8") as f:
                    json.dump(extra_data, f, indent=2, ensure_ascii=False)

                generated_files.append(extra_path)
                print(f"Saved TB-Extra: {extra_path} ({extra_count} questions)")

                validate_file(
                    input_path=output_path_selected,
                    subject_name=subject_name,
                    gemini_client=client,
                    model_chain=modelChain,
                    source_type="TB-Selected",
                    output_path=output_path_selected      # overwrite instead of creating _validated
                )

                validate_file(
                    input_path=extra_path,
                    subject_name=subject_name,
                    gemini_client=client,
                    model_chain=modelChain,
                    source_type="TB-Extra",
                    output_path=extra_path      # overwrite instead of creating _validated
                )

            except Exception as e:

                print(f"Failed parsing {json_file}: {e}")

                failed_path = os.path.join(
                    output_folder_selected,
                    json_file.replace(".json", "_FAILED.txt")
                )

                with open(
                    failed_path,
                    "w",
                    encoding="utf-8"
                ) as f:

                    f.write(selected_result)

                print(f"Raw response saved to {failed_path}")

        else:

            print(f"Failed: {json_file}")

    print("\n==========================================")
    print("TB-Selected generation complete.")
    print(f"Files generated: {len(generated_files)}")
    print("==========================================")

    return generated_files