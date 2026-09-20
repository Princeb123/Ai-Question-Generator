import os
import re
import json
import time
from pathlib import Path
from google.genai.errors import APIError
from google.genai import types

def generate_visual(
        client,
        modelChain,
        figures_dir,
        obj_rules,
        subj_rules,
        subject_name,
        grade_level,
        chapter_name,
        chapter_number,
        textbook_ref,
        output_folder="output/tbfull"):
    """
    Iterates through the figures directory, reads each image and its corresponding text caption,
    and runs them through the model fallback chain to generate Visual-Interpretation MCQs.
    """
    
    figures_path = Path(figures_dir)
    # Ensure the target directory exists
    os.makedirs(output_folder, exist_ok=True)
    
    # Supported image formats
    valid_extensions = {'.png', '.jpg', '.jpeg', '.webp'}
    image_files = [f for f in figures_path.iterdir() if f.suffix.lower() in valid_extensions]
    
    if not image_files:
        print(f"No valid images found in {figures_dir}")
        return None

    print(f"Found {len(image_files)} images to process for Visual Interpretation Questions...")
    
    # Master list to accumulate all generated questions across all images
    all_questions = []

    for idx, img_path in enumerate(image_files, start=1):
        print(f"\n--- Processing Image {idx}/{len(image_files)}: {img_path.name} ---")
        
        # 1. Read corresponding caption file if it exists
        caption_file = figures_path / f"{img_path.stem}_caption.txt"
        caption_text = ""
        
        if caption_file.exists():
            with open(caption_file, 'r', encoding='utf-8') as f:
                caption_text = f.read().strip()
            print(f"  [Success] Found caption: '{caption_text[:30]}...'")

            figure_match = re.match(r'^(Fig(?:ure)?\.?\s*\d+\.\d+)', caption_text, re.IGNORECASE)
            if figure_match:
                display_name = figure_match.group(1) # Extracts "Fig 3.3"
                print(f"  [Success] Extracted textbook image name: '{display_name}'")
            else:
                print(f"  [Info] No 'Fig X.X' pattern found at start of caption. Using filename instead.")
        else:
            print(f"  [Warning] Caption file missing at expected path: {caption_file.name}")

        # 2. Convert raw image bytes into a format the GenAI SDK accepts
        with open(img_path, 'rb') as f:
            image_bytes = f.read()
            
        suffix = img_path.suffix.lower()
        mime_type = "image/jpeg" if suffix in ['.jpg', '.jpeg'] else f"image/{suffix[1:]}"
        image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

        # 3. Formulate the precise instruction matching your design criteria
        visual_prompt = f"""
You are an expert CBSE Class 10 assessment designer specializing in visual data processing.

Analyze the attached image and its original textbook caption:
"Caption: {caption_text}"

Generate at least 3  highly accurate, concept-driven visual questions testing image analysis or direct practical deduction.
Distribute them across the allowed question types wherever appropriate.
Overall question bank should contain a balanced mix of:
- mcq
- multi
- truefalse
- fillblanks
- matchfollowing
- subjective

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
- subjective

Choose the most appropriate question type for the concept being tested.

Follow these rules STRICTLY while generation and json output {obj_rules} and {subj_rules}

----------------------------------
MATHEMATICAL & CHEMICAL FORMATTING RULES (STRICT)
----------------------------------
For all mathematical expressions, equations, variables, chemical formulas, and fractions, you MUST use valid LaTeX notation wrapped in single dollar signs ($...$) for inline text or double dollar signs ($$...$$) for standalone equations.

Follow these syntax examples strictly:
- Fractions: Use $\\frac{{numerator}}{{denominator}}$
- Powers/Subscripts: Use $x^{{2}}$ or $H_{{2}}O$
- Multiplication/Division: Use $\\times$ and $\\div$
- Symbols: Use $\\sqrt{{x}}$, $\\pi$, $\\theta$, $\\le$, $\\ge$
- Do NOT use a single \ always double them like this \\
JSON Escaping Rules (MANDATORY):
- Return STRICT valid JSON only.
- Escape every quotation mark occurring inside any string value using a backslash (\").
- Never include unescaped double quotes inside questionText, explanation, optionText, sourceText, passages, or any other string field.
- The output must be directly parseable using Python's json.loads() without any preprocessing.

----------------------------------
OUTPUT FORMAT RULES
----------------------------------
Return valid JSON text conforming exactly to the structural layout below. 
Do NOT include any markdown code wrappers (like ```json) or trailing commentary.

The field "category" MUST strictly and uniquely be "Visual-Interpretation".
The field "sourceType" MUST strictly be "TB Full".
The field "imageName" MUST match exactly "{img_path.name}".
The field "imageCaption" MUST store the exact string text provided above(ignore \n).

JSON Object Structure:
{{
    "questions":[
    {{
        "conceptId": "VI.{{idx:03d}}",
        "id": "S6.{{idx:03d}}",
        "topic": null ,
        "questionType": "[must be from: mcq | fillblanks| muli | truefalse | matchfollowing | subjective]",
        "sourceType": "TB-Full",
        "category": "Visual-Interpretation",
        "difficulty": "easy | medium | hard",
        "questionText": "[Insert structured question asking to interpret elements inside this specific image layout]",
        "options": [
            {{"optionText": "[Option A]", "isCorrect": false}},
            {{"optionText": "[Option B]", "isCorrect": true}},
            {{"optionText": "[Option C]", "isCorrect": false}},
            {{"optionText": "[Option D]", "isCorrect": false}}
        ],
        "multi": null,
        "blanks": null,
        "sourceTextbookUrl": null,
        "pageNumber": null,
        "marks":1 | 2[if subjective] | 4[if subjective] ,
        "subjective_evaluation_points": ["1.Points for evaluation","2."..],
        "imageName": "{img_path.name}",
        "imageUrl": null,
        "imageCaption": "{caption_text}",
        "explanationAnswer": "[Detailed step-by-step resolution mapping why the correct answer satisfies the visual data]",
        "explanationQuestion": "[Step-by-step walkthrough detailing what features the student must identify inside the visual workspace]",
        "correctAnswer": "[correct answer text]",
        "leftItems": null,
        "rightItems": null,
        "correctMappings": null,
        "set": "A"
        }}
    ]
}}

1. questionType = "mcq"

- options MUST contain exactly four options.
- Exactly one option must have isCorrect=true.
- correctAnswer must contain the correct option text.
- multi, blanks, leftItems, rightItems and correctMappings must be null.

2. questionType = "multi"

- options contains all available choices.
- Do NOT use isCorrect inside options.
- multi contains all correct option texts.
- correctAnswer must be null.
- blanks, leftItems, rightItems and correctMappings must be null.

3. questionType = "truefalse"

- options must be null.
- correctAnswer must be either true or false.
- multi, blanks, leftItems, rightItems and correctMappings must be null.

4. questionType = "fillblanks"

- questionText must contain one or more blanks represented by ______.
- blanks must contain the answers in order.
- options must be null.
- correctAnswer must be null.
- leftItems, rightItems and correctMappings must be null.

5. questionType="matchfollowing":

- Generate only if the concept naturally supports matching.
- Use 4 to 6 pairs whenever possible.
- Shuffle the rightItems so they are NOT in the same order as leftItems.
- Do NOT reveal the answer through ordering.
- correctMappings contains the correct index mappings.
- options, multi, blanks and correctAnswer must all be null.

6. questionType = "subjective":
- Must be a subjective(long/short answer)
- Assign marks based on complexity of question
- marks=2 for short answer and marks=4 for long answer
- subjective_evaluation_points must contain the key marking points expected by an examiner.
- Generate evaluation points in the order in which an examiner would award marks.

Never populate fields that are not applicable to the selected question type.
"""

        topic_result = None
        current_model_idx = 0

        # 4. Model Fallback Engine Routing
        while current_model_idx < len(modelChain):
            model_name = modelChain[current_model_idx]
            try:
                print(f"  Requesting {model_name} for visual generation...")
                
                response = client.models.generate_content(
                    model=model_name,
                    contents=[obj_rules, subj_rules, image_part, visual_prompt],
                    config={"response_mime_type": "application/json",
                            "temperature": 0.3
                    },
                )
                
                topic_result = response.text
                print(f"  Success via {model_name}")
                time.sleep(7)
                break
                
            except APIError as e:
                print(f"  {model_name} exhausted: {e.message}")
                current_model_idx += 1
                time.sleep(7)
            except Exception as e:
                print(f"  Unexpected exception on model {model_name}: {e}")
                current_model_idx += 1
                time.sleep(7)

        # 5. Parse output and append to aggregate lists
        if topic_result:
            try:
                cleaned_json = topic_result.strip()
                if cleaned_json.startswith("```json"):
                    cleaned_json = cleaned_json.split("```json")[1].split("```")[0].strip()
                elif cleaned_json.startswith("```"):
                    cleaned_json = cleaned_json.split("```")[1].split("```")[0].strip()
                
                question_obj = json.loads(cleaned_json)

                # Unwrap before adding to all_questions
                if isinstance(question_obj, dict) and "questions" in question_obj:
                    batch = question_obj["questions"]
                elif isinstance(question_obj, list):
                    batch = question_obj
                else:
                    print(f"  [Warning] Unexpected JSON structure for {img_path.name}: {type(question_obj)}")
                    batch = []

                for q in batch:
                    if isinstance(q, dict):
                        all_questions.append(q)
                    elif isinstance(q, list):
                        # safety net for double nesting
                        all_questions.extend(q)
                    else:
                        print(f"  [Warning] Skipped non-dict item in batch for {img_path.name}")

            except Exception as parse_err:
                print(f"  [Error] Failed parsing JSON for {img_path.name}: {parse_err}")
        else:
            print(f"  [Critical] All models failed for {img_path.name}")

        if current_model_idx >= len(modelChain):
            print("  Warning: All fallback models exhausted during this specific run cycle step.")

    # 6. Build the final unified JSON payload structure matching your exact requirements
    if all_questions:
        final_payload = {
            "subject": subject_name,
            "grade": grade_level,
            "chapterName": chapter_name,
            "chapterNumber": chapter_number,
            "textbookRef": textbook_ref,
            "questions": all_questions
        }
        
        # Safe filename production
        safe_chap_name = re.sub(r'[^A-Za-z0-9]+', '_', chapter_name)
        filename = os.path.join(
            output_folder,
            f"visual_mcqs_ch_{chapter_number}_{safe_chap_name}.json"
        )
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(final_payload, f, indent=2, ensure_ascii=False)
            
        print(f"\n🎉 Successfully compiled all questions! Output written directly to: {filename}")
        return filename

    return None