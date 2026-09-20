
import time
import os
import re
import json
from google.genai.errors import APIError
from utils import get_allowed_categories,get_language_specific_instructions

def generate_tbfull(
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

        page_instruction=""

        page_match=re.search(
            r"Pages\s+(\d+)-(\d+)\s+Focus",
            topic
        )

        if page_match:

            start_page,end_page=page_match.groups()

            page_instruction=f"""
        CRITICAL BOUNDARY:
        You MUST generate questions ONLY from content appearing between 
        Page {start_page} and Page {end_page}.
        Do NOT use information from pages before or after this range.
        Ignore any concepts outside these pages.
        """
        current_model_idx = 0

        allowed_categories = get_allowed_categories(subject_name)

        allowed_categories_str = "\n".join(
            f"- {c}" for c in allowed_categories
        )

        language_instructions = get_language_specific_instructions(subject_name)


        topic_prompt = rf"""
You are an expert CBSE Class 10 assessment designer.
{language_instructions}

Generate an OBJECTIVE QUESTION BANK ONLY for the topic:

{topic}

using the concepts below:

{concepts_output}

Do NOT generate questions from any other topic.
{page_instruction}

Generate at least 4 objective questions for every concept.

Distribute them across the allowed question types wherever appropriate.

Overall question bank should contain a balanced mix of:
- mcq
- multi
- truefalse
- fillblanks
- matchfollowing

----------------------------------
QUESTION TYPE RULES (STRICT)
----------------------------------

Allowed values:

questionType =
- mcq
- multi
- truefalse
- fillblanks
- matchfollowing

Choose the most appropriate question type for the concept being tested.

Definitions and facts may use:
- mcq
- truefalse
- fillblanks

Lists, classifications and multiple valid answers should use:
- multi

Relationships, pairing and associations should use:
- matchfollowing

Avoid generating unnecessary MCQs if another question type better evaluates the concept.

Follow these rules STRICTLY while generation and json output {rules}

----------------------------------
ALLOWED CATEGORY ENUM (STRICT)
----------------------------------

The value of the "category" field MUST be EXACTLY ONE of the following: 

{allowed_categories_str}

These are the ONLY valid values.

Do NOT invent new categories.

Do NOT modify capitalization.

Do NOT pluralize.

Do NOT abbreviate.

Do NOT combine categories.

Do NOT output any other value.

----------------------------------
FORMATTING RULES (STRICT)
----------------------------------
For all mathematical expressions, equations, variables, and fractions, you MUST use valid LaTeX notation wrapped in single dollar signs ($...$) for inline text or double dollar signs ($$...$$) for standalone equations.

Follow these syntax examples strictly:
- Fractions: Use $\\frac{{numerator}}{{denominator}}$
- Powers: Use $x^{{2}}$
- Multiplication/Division: Use $\\times$ and $\\div$
- Symbols: Use $\\sqrt{{x}}$, $\\pi$, $\\theta$, $\\le$, $\\ge$
- Do NOT use a single \ always double them like this \\
- For quoted text use '' only. As "" are used for json string indication.

JSON Escaping Rules (MANDATORY):
- Return STRICT valid JSON only.
- Escape every quotation mark occurring inside any string value using a backslash (\").
- Never include unescaped double quotes inside questionText, explanation, optionText, sourceText, passages, or any other string field.
- The output must be directly parseable using Python's json.loads() without any preprocessing.

QUESTION TYPE DISTRIBUTION

Aim for the following overall distribution:

- mcq : 45%
- multi : 15%
- truefalse : 15%
- fillblanks : 15%
- matchfollowing : 10%

These percentages are approximate. Prioritize pedagogical suitability over exact percentages.

----------------------------------
OUTPUT FORMAT
----------------------------------

Return valid JSON text conforming exactly to the following schema structure:

{{
  
  "subject": "{subject_name}",
  "grade": {grade_level},
  "chapterName": "{chapter_name}",
  "chapterNumber": {chapter_number},
  "textbookRef": "{textbook_ref}",
  "questions": [
    {{
      "conceptId": "",
      "id": "A2.001",
      "topic": "{topic}",
      "questionType": "[must be from: mcq | fillblanks | multi | truefalse | matchfollowing]",
      "sourceType": "TB-Full",
      "category": "{allowed_categories_str}",
      "difficulty": "[easy | medium | hard]",
      "questionText": "",
      "options": [
        {{ "optionText": "[Option A text]", "isCorrect": false }},
        {{ "optionText": "[Option B text]", "isCorrect": true }},
        {{ "optionText": "[Option C text]", "isCorrect": false }},
        {{ "optionText": "[Option D text]", "isCorrect": false }}
      ],
      "multi": null,
      "blanks": null,
      "sourceTextbookUrl": {source_text_url},
      "pageNumber": [Must be a number strictly],
      "marks":1,
      "subjective_evaluation_points":null,
      "explanationAnswer": "[Detailed explanation why it is correct and why other options are incorrect]",
      "explanationQuestion": "[Step by step explanation of the question text context]",
      "correctAnswer": "[Insert option text of the correct answer directly]",
      "leftItems": null,
      "rightItems": null,
      "correctMappings": null,
      "set": "A"
    }}
  ],
  "coverageReport": {{
      "totalQuestions": 0,
      "totalConceptsFound": 0,
      "totalConceptsCovered": 0,
      "coveragePercentage": "100%"
  }}
}}

Populate ONLY the fields required by the selected questionType.

1. questionType = "mcq"

- options MUST contain min two options.
- If subject is maths include options with opposite signs +ve and -ve to make it plausible.
- Exactly one option MUST have isCorrect=true.
- correctAnswer must contain the correct option text.
- If subject is maths include options with opposite signs +ve and -ve to make it plausible.
- multi, blanks, leftItems, rightItems and correctMappings must be null.

2. questionType = "multi"

- options contains all available choices.
- Do NOT use isCorrect inside options.
- multi contains all correct option texts.
- correctAnswer must be null.
- blanks, leftItems, rightItems and correctMappings must be null.

3. questionType = "truefalse"

- options must be null.
- correctAnswer must be either true or false boolean.
- multi, blanks, leftItems, rightItems and correctMappings must be null.
- correctAnswer must be 50/50 true/false balance

4. questionType = "fillblanks"

- questionText must contain one or more blanks represented by ______.
- blanks must contain the answers in order.
- options must be null.
- correctAnswer must be null.
- leftItems, rightItems and correctMappings must be null.

5. questionType="matchfollowing"

- Generate only if the concept naturally supports matching.
- Use 4 to 6 pairs whenever possible.
- Shuffle the rightItems so they are NOT in the same order as leftItems.
- Do NOT reveal the answer through ordering.
- correctMappings should contain the correct index mappings for eg.
- options, multi, blanks and correctAnswer must all be null.

Never populate fields that are not applicable to the selected question type.
All the fields of the json file must be filled completely for each question answer pair.DO NOT include any commentary in the json file.
"""

        topic_result = None

        while current_model_idx < len(modelChain):

            model_name = modelChain[current_model_idx]

            try:

                print(f" Requesting {model_name}")

                response = client.models.generate_content(
                    model=model_name,
                    contents=[uploaded_file, concepts_output,rules, topic_prompt],
                    config={"response_mime_type": "application/json",
                            "temperature": 0.2
                    },
                )

                topic_result = response.text

                print(f" Success")

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
                f"{re.sub(r'[^A-Za-z0-9]+','_',topic)}.json"
            )

            with open(filename, "w", encoding="utf-8") as f:
                f.write(topic_result)

            print(f" Saved {filename}")


            if current_model_idx >= len(modelChain):
                print("All models exhausted.")

        
            return filename
        
        return None