import os
from google.genai.errors import APIError


def extract_topics(client, modelChain, uploaded_file, output_file="topics.txt"):
    """
    Extract chapter topics from a PDF and save them to a text file.
    """


    topic_prompt = """
Analyze the attached textbook chapter PDF document. Map out the chapter headings sequentially, listing only the page number where a topic starts or changes. Do not output a line for every single page.

STRICT WIDE-TOPIC CHUNKING RULE:
- If a textbook topic spans 1 or 2 or 3 pages total, just list its starting page and the topic name.
- If a textbook topic spans MORE THAN 3 pages, partition it by explicitly defining the page boundaries. Keep each chunk up to 2 pages.

Example:
1. Page 1: 10.1 THE HUMAN EYE
2. Page 2: 10.2 DEFECTS OF VISION (Pages 2-4 Focus)
3. Page 5: 10.2 DEFECTS OF VISION (Pages 5-7 Focus)
4. Page 8: 10.3 REFRACTION OF LIGHT THROUGH A PRISM

Important:
1. Do not create separate topics for Questions/Exercises.
2. Do not include subtopics (e.g. 10.2.1).
3. Do not include the chapter title.

Output only the numbered list.
"""

    topics_output = None

    print("\n--- Extracting Topics ---")

    for model_name in modelChain:
        try:
            print(f"Trying {model_name}...")

            response = client.models.generate_content(
                model=model_name,
                contents=[uploaded_file, topic_prompt]
            )

            topics_output = response.text
            print(f"Success using {model_name}")
            break

        except APIError as e:
            print(f"{model_name} exhausted: {e.message}")
            print("Trying next model...")

    if topics_output is None:
        raise RuntimeError("All models were exhausted.")

    # Save topics to text file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(topics_output)

    print(f"💾 Topics saved to '{output_file}'")

    # return uploaded_file, topics_output