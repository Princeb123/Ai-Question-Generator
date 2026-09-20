import time
import os
import re
from google.genai.errors import APIError
from utils import get_allowed_categories,get_language_specific_instructions


def generate_subjective(
        client,
        modelChain,
        uploaded_file,
        concepts_output,
        rules,
        topic,
        subject_name,
        grade_level,
        chapter_name,
        chapter_number,
        textbook_ref,
        source_text_url,
        output_folder="output/tbfull"):

    page_instruction = ""

    page_match = re.search(
        r"Pages\s+(\d+)-(\d+)\s+Focus",
        topic
    )

    if page_match:

        start_page, end_page = page_match.groups()

        page_instruction = f"""
CRITICAL BOUNDARY:
You MUST generate questions ONLY from content appearing between
Page {start_page} and Page {end_page}.

Do NOT use concepts outside this page range.
"""

    allowed_categories = get_allowed_categories(subject_name)

    allowed_categories_str = "\n".join(
        f"- {c}" for c in allowed_categories
    )
    current_model_idx = 0

    language_instructions = get_language_specific_instructions(subject_name)

    topic_prompt = rf"""
You are an expert CBSE Class 10 assessment designer.

{language_instructions}

Generate a SUBJECTIVE QUESTION BANK ONLY for the topic:

{topic}

using the concepts below:

{concepts_output}

Do NOT generate questions from any other topic.

{page_instruction}

Follow these rules STRICTLY while generation and json output {rules}

------------------------------------------------
QUESTION REQUIREMENTS
------------------------------------------------

Generate subjective questions ONLY.

For EVERY concept:

• Generate at least ONE Short Answer question.

• Generate ONE Long Answer question whenever the concept naturally supports detailed explanation.

Cover all important textbook content including:

- Definitions
- Facts
- Explanations
- Examples
- Activities
- Diagrams
- Tables
- Experiments
- Exercises
- Reflection Questions
- Assertion/Reason concepts
- Competency Based situations
- Application Based situations


Choose the marks appropriate to the complexity of the question.

------------------------------------------------
DIFFICULTY DISTRIBUTION
------------------------------------------------

Easy : 20%

Medium : 50%

Hard : 30%

------------------------------------------------
QUESTION QUALITY
------------------------------------------------

Prefer questions requiring students to:

- Explain
- Justify
- Compare
- Differentiate
- Analyse
- Predict
- Interpret observations
- Explain experiments
- Draw conclusions
- Explain diagrams
- Give reasons
- Apply concepts in real-life situations

Avoid simple one-line recall unless essential.
----------------------------------
ALLOWED CATEGORY ENUM (STRICT)
----------------------------------

The value of the "category" field MUST be EXACTLY ONE of the following strings.

{allowed_categories_str}

These are the ONLY valid values.

Do NOT invent new categories.

Do NOT modify capitalization.

Do NOT pluralize.

Do NOT abbreviate.

Do NOT combine categories.

Do NOT output any other value.

------------------------------------------------
FORMATTING RULES
------------------------------------------------

Use valid LaTeX where appropriate.

Examples:

$\\frac{{a}}{{b}}$

$x^{{2}}$

$\\sqrt{{x}}$

JSON Escaping Rules (MANDATORY):

- Return STRICT valid JSON only.
- Escape every quotation mark occurring inside any string value using a backslash (\").
- Never include unescaped double quotes inside questionText, explanation, optionText, sourceText, passages, or any other string field.
- The output must be directly parseable using Python's json.loads() without any preprocessing.

------------------------------------------------
OUTPUT FORMAT
------------------------------------------------

Return ONLY valid JSON.

{{
  "subject":"{subject_name}",
  "grade":{grade_level},
  "chapterName":"{chapter_name}",
  "chapterNumber":{chapter_number},
  "textbookRef":"{textbook_ref}",
  "questions":[
    {{
      "conceptId":"",
      "id":"S001.001",
      "topic":"{topic}",
      "questionType":"subjective",
      "sourceType":"TB-Full",
      "category":"{allowed_categories_str}",
      "difficulty":"easy | medium | hard",
      "questionText": "[Question text]",
      "options": null,
      "multi": null,
      "blanks": null,
      "sourceTextbookUrl": {source_text_url},
      "pageNumber": [Must be a number strictly],
      "marks":2 | 4,
      "subjective_evaluation_points":["Points for evaluation","",""],
      "explanationAnswer": "[Detailed explanation of expected answer]",
      "explanationQuestion": "[Step by step explanation of the question text context]",
      "correctAnswer": "[Insert text of the correct answer directly]",
      "leftItems": null,
      "rightItems": null,
      "correctMappings": null,
      "set": "A"
    }}
  ],
  "coverageReport":
  {{
      "totalQuestions":0,
      "totalConceptsFound":0,
      "totalConceptsCovered":0,
      "coveragePercentage":"100%"
  }}
}}

------------------------------------------------
RULES
------------------------------------------------

For EVERY question:

- questionType MUST always be "subjective"

- marks MUST be:
  - 2
  - 4

- subjectiveEvaluationPoints should contain the key marking points expected by an examiner.

- Generate evaluation points in the order in which an examiner would award marks.

- Every field must be populated.

Do NOT output any commentary.

Output ONLY valid JSON.
"""

    topic_result = None

    while current_model_idx < len(modelChain):

        model_name = modelChain[current_model_idx]

        try:

            print(f"Requesting {model_name}")

            response = client.models.generate_content(
                model=model_name,
                contents=[rules,uploaded_file, concepts_output,rules, topic_prompt],
                config={"response_mime_type": "application/json",
                        "temperature": 0.4
                        },
            )

            topic_result = response.text

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

    if topic_result:

        os.makedirs(output_folder, exist_ok=True)

        filename = os.path.join(
            output_folder,
            f"{re.sub(r'[^A-Za-z0-9]+','_',topic)}_subjective.json"
        )

        with open(filename, "w", encoding="utf-8") as f:
            f.write(topic_result)

        print(f"Saved {filename}")

        if current_model_idx >= len(modelChain):
            print("All models exhausted.")

        return filename

    return None