import os
import re
import json
import time
from google.genai.errors import APIError
from utils import get_language_specific_instructions
from validate import validate_file


def generate_tbreversed(
    client,
    modelChain,
    subject_name,
    input_folder="output/tbselected",
    output_folder="output/tbreversed",
    min_coverage_ratio=0.95,  # Must convert at least 95% of input questions
):
    """
    Generates TB-Reversed JSONs topic-wise.

    Reads every JSON from output/tbselected,
    transforms each question to its reversed/indirect form,
    saves with the SAME filename in output/tbreversed.

    """

    os.makedirs(output_folder, exist_ok=True)

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
        min_required = max(1, int(total_input * min_coverage_ratio))

        print(f"Input: {total_input} questions | Must convert >= {min_required}")

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

        reversal_prompt = rf"""
You are an expert CBSE question designer specialising in higher-order thinking questions.

{language_instructions}

Your task is to transform EVERY question in the provided bank into its REVERSED form.

--------------------------------------------------
WHAT IS A REVERSED QUESTION
--------------------------------------------------

A reversed question swaps the given information and the expected answer
while testing the SAME underlying concept:

    given ↔ unknown
    cause ↔ effect
    input ↔ output
    statement ↔ conclusion
    definition ↔ term
    example ↔ concept
    observation ↔ explanation
    formula ↔ application
    symptom ↔ diagnosis
    process ↔ result

EXAMPLES OF REVERSALS:

Original :
  "What is the near point of a normal human eye?"
  Answer: 25 cm

Reversed :
  "A person can read a book comfortably only when it is held at least
   25 cm away. Which of the following best describes this person's vision?"
  Answer: Normal vision — 25 cm is the standard near point

---

Original :
  "Which type of lens is used to correct myopia?"
  Answer: Concave lens

Reversed :
  "An optometrist prescribes a diverging lens for a patient. Which
   visual defect is the patient most likely suffering from?"
  Answer: Myopia (near-sightedness)

---

Original :
  "When copper is heated in air, what product is formed?"
  Answer: Copper(II) oxide (CuO)

Reversed :
  "A student heats a reddish-brown metal in air and observes a black
   coating forming on its surface. The black substance formed is most
   likely which compound?"
  Answer: Copper(II) oxide (CuO)

---

Original :
  "Assertion: Sodium is stored in kerosene.
   Reason: Sodium reacts vigorously with air and water."
  Answer: Both A and R are true, R is the correct explanation

Reversed :
  "A metal X cannot be stored in open air or water. To safely store it,
   a technician submerges it in an organic liquid. Which property of X
   best explains this storage requirement?"
  Answer: X reacts vigorously with both air and water

--------------------------------------------------
REVERSAL RULES
--------------------------------------------------

1. COVERAGE: You MUST reverse at least {min_required} out of {total_input}
   questions. Target is ALL {total_input}. Do not skip questions.

2. Questions that CANNOT be meaningfully reversed (e.g. a diagram-label
   question where no logical inverse exists) must be SKIPPED ENTIRELY.
   Do NOT include them in the output in any form.
   This exception should apply to VERY FEW questions (< 5%).

3. NEW QUESTION TEXT: The reversed question must be genuinely different
   in structure and phrasing from the original. Do not just rephrase
   the original. The direction of reasoning must flip.

4. NEW OPTIONS(For MCQs): Generate 4 fresh, plausible MCQ options for the reversed
   question. Do NOT reuse the original options verbatim. Distractors must
   target common misconceptions about the concept.

5. NEW CORRECT ANSWER: The correct answer for the reversed question may
   be different text from the original — reflect what the reversed
   question actually asks for.

6. NEW EXPLANATION: Write a fresh explanationAnswer and explanationQuestion
   appropriate to the reversed question's reasoning direction.

7. PRESERVE: Keep conceptId, category, topic, marks, questionType
   identical to the source question.

8. DIFFICULTY: Increase by one level if possible:
   easy → medium, medium → hard, hard → hard (stays hard)

9. IDs: Prefix the original ID with "REV-"
   Example: "R1.001" becomes "REV-R1.001"

10. sourceType: Set to "TB-Reversed" for every output question.

JSON Escaping Rules (MANDATORY):

- Return STRICT valid JSON only.
- Escape every quotation mark occurring inside any string value using a backslash (\").
- Never include unescaped double quotes inside questionText, explanation, optionText, sourceText, passages, or any other string field.
- The output must be directly parseable using Python's json.loads() without any preprocessing.

--------------------------------------------------
OUTPUT FORMAT
--------------------------------------------------

Return ONLY valid JSON. No markdown. No comments. No explanation.

{{
  "questions": [
    {{
      "conceptId": "<same as source>",
      "id": "REV-<original id>",
      "topic": "<same as source>",
      "sourceType": "TB-Reversed",
      "questionType": "<same as source>",
      "category": "<same as source>",
      "difficulty": "<one level higher or same if already hard>",
      "topic": "<same as source or null>",
      "questionText": "<new reversed question text>",
      "options": [
        {{"optionText": "<new option A>", "isCorrect": false}},
        {{"optionText": "<new option B>", "isCorrect": true}},
        {{"optionText": "<new option C>", "isCorrect": false}},
        {{"optionText": "<new option D>", "isCorrect": false}}
      ],
      "correctAnswer": "<text of correct option>",
      "explanationAnswer": "<why this answer is correct>",
      "explanationQuestion": "<step by step reasoning to reach the answer>",
      "marks": <same as source or null>,
      "pageNumber": <same as source or null>,
      "multi": null,
      "blanks": null,
      "sourceTextbookUrl": null,
      "leftItems": null,
      "rightItems": null,
      "correctMappings": null,
      "set": "A"
    }}
  ],
  "reversalSummary": {{
    "inputCount": {total_input},
    "reversedCount": <how many were genuinely reversed>,
    "skippedCount": <how many were skipped as non-reversible>,
    "coveragePercent": <reversedCount / inputCount * 100>
  }}
}}

Topic: {topic}
Subject: {subject}
Grade: {grade}
Chapter: {chapter_name}

Source questions to reverse:
{questions_json}
"""

        current_model_idx = 0
        reversed_result = None

        while current_model_idx < len(modelChain):

            model_name = modelChain[current_model_idx]

            try:

                print(f"Requesting {model_name}")

                response = client.models.generate_content(
                    model=model_name,
                    contents=[reversal_prompt],
                    config={
                        "response_mime_type": "application/json",
                        "temperature": 0.1
                    }
                )

                reversed_result = response.text

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

        if reversed_result:

            try:

                # Safe JSON cleaning — strip markdown fences only,
                # no regex on the body to avoid corrupting valid escapes
                clean_json = reversed_result.strip()
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

                reversed_questions = parsed.get("questions", [])
                reversal_summary = parsed.get("reversalSummary", {})

                reversed_count = len(reversed_questions)
                coverage_pct = round(reversed_count / total_input * 100, 1) if total_input else 0

                print(f"Reversed: {reversed_count}/{total_input} ({coverage_pct}%)")

                if reversed_count < min_required:
                    print(
                        f"WARNING: Coverage {coverage_pct}% is below "
                        f"{min_coverage_ratio*100}% target. "
                        f"Consider re-running this file."
                    )

                # Build output preserving all original metadata
                output_data = {
                    "subject": subject,
                    "grade": grade,
                    "chapterName": chapter_name,
                    "chapterNumber": chapter_number,
                    "textbookRef": textbook_ref,
                    "questions": reversed_questions,
                    "reversalSummary": {
                        **reversal_summary,
                        "inputCount": total_input,
                        "reversedCount": reversed_count,
                        "skippedCount": total_input - reversed_count,
                        "coveragePercent": coverage_pct,
                        "targetCoveragePercent": min_coverage_ratio * 100,
                    }
                }

                output_path = os.path.join(
                    output_folder,
                    json_file
                )

                with open(
                    output_path,
                    "w",
                    encoding="utf-8"
                ) as f:

                    json.dump(
                        output_data,
                        f,
                        indent=2,
                        ensure_ascii=False
                    )

                generated_files.append(output_path)

                validate_file(
                    input_path=output_path,
                    subject_name=subject_name,
                    gemini_client=client,
                    model_chain=modelChain,
                    source_type="TB-Reversed",
                    output_path=output_path
                )

                print(f"Saved: {output_path}")

            except Exception as e:

                print(f"Failed parsing {json_file}: {e}")

                failed_path = os.path.join(
                    output_folder,
                    json_file.replace(".json", "_FAILED.txt")
                )

                with open(
                    failed_path,
                    "w",
                    encoding="utf-8"
                ) as f:

                    f.write(reversed_result)

                print(f"Raw response saved to {failed_path}")

        else:

            print(f"All models exhausted for: {json_file}")

    print("\n==========================================")
    print("TB-Reversed generation complete.")
    print(f"Files generated: {len(generated_files)}")
    print("==========================================")

    return generated_files