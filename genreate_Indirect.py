
import time
import os
import re
import json
from google.genai.errors import APIError
from utils import get_category_batches,get_language_specific_instructions


def generate_indirect(
        client,
        modelChain,
        uploaded_file,
        concepts_output,
        topic,
        obj_rules,
        subj_rules,
        subject_name,
        grade_level,
        chapter_name,
        chapter_number,
        textbook_ref,
        source_text_url,
        output_folder="output/indirect"):
    
    batches = get_category_batches(subject_name)

    current_model_idx = 0

    for batch_name, categories in batches.items():

        print(f"\n Processing {batch_name}...")

        categories_list_str = "\n".join(
            [f"- {c}" for c in categories]
        )

        language_instructions = get_language_specific_instructions(subject_name)

        topic_prompt = f"""
You are an expert CBSE Class 10 assessment designer.

{language_instructions}

Generate MCQs ONLY for the topic:
{topic} and {concepts_output}

You MUST generate exactly 2 distinct questions for EACH and EVERY category listed in the target list below. Do not skip any category.

Target Categories for this execution block:
{categories_list_str}

DO NOT generate questions from any other topic.

Overall question bank should contain a balanced mix of:
- mcq
- multi
- truefalse
- fillblanks
- matchfollowing
- subjective

Follow these rules STRICTLY while generation and json output {obj_rules} and {subj_rules}
----------------------------------
MATHEMATICAL & CHEMICAL FORMATTING RULES (STRICT)
----------------------------------
For all mathematical expressions, equations, variables, and fractions, you MUST use valid LaTeX notation wrapped in single dollar signs ($...$) for inline text or double dollar signs ($$...$$) for standalone equations.

Follow these syntax examples strictly:
- Fractions: Use $\\frac{{numerator}}{{denominator}}$
- Powers: Use $x^{{2}}$
- Multiplication/Division: Use $\\times$ and $\\div$
- Symbols: Use $\\sqrt{{x}}$, $\\pi$, $\\theta$, $\\le$, $\\ge$
- Stricly Do NOT use a single \ always double them like this \\
JSON Escaping Rules (MANDATORY):
- Return STRICT valid JSON only.
- Escape every quotation mark occurring inside any string value using a backslash (\").
- Never include unescaped double quotes inside questionText, explanation, optionText, sourceText, passages, or any other string field.
- The output must be directly parseable using Python's json.loads() without any preprocessing.

----------------------------------
COVERAGE REQUIREMENTS
----------------------------------
Cover every:
- Definition
- Fact
- Example
- Solved Example
- Activity
- Diagram
- Table
- Exercise Question
- Test Yourself Question
- Reflection Question
- Assertion Reason Question

belonging to this topic.

----------------------------------
DIFFICULTY (STRICT)
----------------------------------
This field is mandatory

Every generated question MUST have

"difficulty": "hard"

This is mandatory.

Do NOT generate any question with difficulty "easy" or "medium".
----------------------------------
COVERAGE AUDIT
----------------------------------
Before generating:

1. See concept ID from {concepts_output}
2. All questions MUST be of hard difficulty.

----------------------------------
OUTPUT FORMAT
----------------------------------

Return valid JSON exactly matching this schema:

{{
  "topic": "{topic}",
  "batch": "{batch_name}",
  "subject": "{subject_name}",
  "grade": {grade_level},
  "chapterName": "{chapter_name}",
  "chapterNumber": {chapter_number},
  "textbookRef": "{textbook_ref}",
  "questions":[
    {{
      "conceptId":"",
      "id":"A2.001",
      "topic":{topic},
      "questionType":"[must be from: mcq | multi | truefalse | fillblanks| matchfollowing | subjective]",
      "sourceType": "Indirect",
      "category":{categories_list_str},
      "difficulty":"hard",
      "questionText":"[Question text]",
      "options":[
        {{"optionText":"","isCorrect":false}},
        {{"optionText":"","isCorrect":true}},
        {{"optionText":"","isCorrect":false}},
        {{"optionText":"","isCorrect":false}}
      ],
      "multi":null,
      "blanks":null,
      "sourceTextbookUrl":{source_text_url},
      "pageNumber":[must be a number strictly],
      "marks":1 | 2 | 4,
      "explanationAnswer":"[Detailed explanation of correct answer]",
      "explanationQuestion":"[Detailed explanation of question]",
      "correctAnswer":"[Correct answer text]",
      "leftItems":null,
      "rightItems":null,
      "correctMappings":null,
      "set":"A"
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

Populate ONLY the fields required by the selected questionType.

1. questionType = "mcq"

- options MUST contain exactly four options.
- Exactly one option MUST have isCorrect=true.
- correctAnswer must contain the correct option text.
- marks must be 1
- multi, blanks, leftItems, rightItems and correctMappings must be null.

2. questionType = "multi"

- options contains all available choices.
- Do NOT use isCorrect inside options.
- multi contains all correct option texts.
- correctAnswer must be null.
- marks must be 1
- blanks, leftItems, rightItems and correctMappings must be null.

3. questionType = "truefalse"

- options must be null.
- correctAnswer must be either true or false.
- multi, blanks, leftItems, rightItems and correctMappings must be null.
- correctAnswer must be 50/50 true/false balance
- marks must be 1

4. questionType = "fillblanks"

- questionText must contain one or more blanks represented by ______.
- blanks must contain the answers in order.
- options must be null.
- correctAnswer must be null.
- leftItems, rightItems and correctMappings must be null.
- marks must be 1

5. questionType = "matchfollowing"

- Generate only if the concept naturally supports matching.
- Use 4 to 6 pairs whenever possible.
- Shuffle the rightItems so they are NOT in the same order as leftItems.
- Do NOT reveal the answer through ordering.
- correctMappings should contain the correct index mappings for eg.
- options, multi, blanks and correctAnswer must all be null.
- marks must be 1.

6. questionType = "subjective"

- subjectiveEvaluationPoints should contain the key marking points expected by an examiner.
- Generate evaluation points in the order in which an examiner would award marks.
- marks must be 2 or 4 based on question.

All the fields of the json file must be filled completely for each question answer pair
"""

        topic_result = None

        while current_model_idx < len(modelChain):

            model_name = modelChain[current_model_idx]

            try:

                print(f" Requesting {model_name}")

                response = client.models.generate_content(
                    model=model_name,
                    contents=[uploaded_file, concepts_output,obj_rules,subj_rules, topic_prompt],
                    config={"response_mime_type": "application/json",
                            "temperature": 0.6
                    },
                )

                topic_result = response.text

                print(f" Success : {batch_name}")

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

            topic_folder = os.path.join(
                output_folder,
                re.sub(r"[^A-Za-z0-9]+", "_", topic)
            )

            os.makedirs(topic_folder, exist_ok=True)

            filename = os.path.join(
                topic_folder,
                f"{batch_name}.json"
            )

            with open(filename, "w", encoding="utf-8") as f:
                f.write(topic_result)

            print(f" Saved {filename}")

        else:

            print(f" Failed {batch_name}")

            if current_model_idx >= len(modelChain):
                print("All models exhausted.")
                break
