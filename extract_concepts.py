from google.genai.errors import APIError
from utils import get_language_specific_instructions


def extract_concepts(client,uploaded_file,topics_output,subject_name,output_file="concepts.txt"):

    language_instructions = get_language_specific_instructions(subject_name)

    concept_prompt = rf"""
    You are an expert CBSE Class 10 curriculum analyst.

    Analyze the entire PDF and extract ATOMIC CONCEPTS.

    {language_instructions}

    Definition of Atomic Concept:

    An atomic concept is the smallest examinable learning objective
    that can be tested independently in a single MCQ.

    Rules:

    1. Every definition is a separate Concept ID.
    2. Every fact is a separate Concept ID.
    3. Every example is a separate Concept ID.
    4. Every activity is a separate Concept ID.
    5. Every diagram interpretation is a separate Concept ID.
    6. Every table entry that can be tested independently is a separate Concept ID.
    7. Every exercise question learning objective is a separate Concept ID.
    8. Every Test Yourself question learning objective is a separate Concept ID.
    9. Every Reflection Question learning objective is a separate Concept ID.
    10. Every Assertion-Reason learning objective is a separate Concept ID.
    11. Do NOT combine multiple learning objectives into one Concept ID.
    12. If two ideas can be asked as separate MCQs, they must have separate Concept IDs.

    Examples:

    GOOD:

    C001 AI Definition
    C002 ML Definition
    C003 DL Definition
    C004 AI as umbrella term
    C005 ML subset of AI
    C006 DL subset of ML

    BAD:

    C001 AI, ML and DL

    Topic should be Exactly same topic from {topics_output}

    Output Format:

    Chapter: <Chapter Name>

    Concept ID: C001
    Topic:(Exactly same topic from {topics_output})
    Concept:
    Source Type: Definition/Example/Diagram/Activity/Table/Exercise

    Concept ID: C002
    Topic:
    Concept:
    Source Type: Definition/Example/Diagram/Activity/Table/Exercise

    Continue until every atomic concept in the PDF has been extracted.

    At the end provide:

    Total Atomic Concepts Identified:(Min 40)
    """

    try:

        response = client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=[uploaded_file,topics_output, concept_prompt],
        )

        concepts_output = response.text

        with open(
            output_file,
            "w",
            encoding="utf-8"
        ) as f:
            f.write(concepts_output)

        print("\nSaved to concept_inventory.txt")

    except APIError as e:
        print("Error:", e)