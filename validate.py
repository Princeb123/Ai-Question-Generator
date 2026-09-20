"""
validate.py
===========
Validation + auto-repair pipeline for NCERT question banks.
Designed to plug into the existing Gemini-based generation pipeline.

Usage (standalone):
    python validate.py --input output/final/Light_tbfull.json
    python validate.py --input output/final/Light_indirect.json --source-type Indirect
    python validate.py --input output/final/Light_tbfull.json --no-llm

Usage (in pipeline, after combine_jsons):
    from validate import validate_file
    validate_file("output/final/AcidBases_tbfull.json", source_type="TB-Full")
"""

import os
import re
import sys
import json
import time  
import copy
import argparse
from typing import Optional

from google import genai
from google.genai.errors import APIError
from dotenv import load_dotenv
from utils import get_allowed_categories

load_dotenv(dotenv_path=".env.local")

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────


ALLOWED_DIFFICULTY = {"easy", "medium", "hard"}

ALLOWED_QUESTION_TYPES = {
    "mcq", "fillblanks", "multi", "truefalse", "matchfollowing", "subjective"
}

QTYPE_ALIASES = {
    "multiplechoice": "mcq",
    "multiple-choice": "mcq",
    "multiple choice": "mcq",
    "multiplechoice": "mcq",
    "multipleChoice": "mcq",
    "fill in the blanks": "fillblanks",
    "fill_in_the_blanks": "fillblanks",
    "fillinblanks": "fillblanks",
    "fill-in-the-blanks": "fillblanks",
    "true false": "truefalse",
    "true-false": "truefalse",
    "trueorfalse": "truefalse",
    "match the following": "matchfollowing",
    "match-the-following": "matchfollowing",
    "matchthefollowing": "matchfollowing",
    "multi select": "multi",
    "multiselect": "multi",
    "multi-select": "multi",
}

ALLOWED_SOURCE_TYPES = {
    "TB-Full", "TB-Selected","TB-Extra", "TB-Reversed", "Indirect",
}

SOURCE_TYPE_ALIASES = {
    "tb-full": "TB-Full",
    "tbfull": "TB-Full",
    "tb full": "TB-Full",
    "tb-selected": "TB-Selected",
    "tbselected": "TB-Selected",
    "tb selected": "TB-Selected",
    "tb-reversed": "TB-Reversed",
    "tbreversed": "TB-Reversed",
    "tb reversed": "TB-Reversed",
    "indirect": "Indirect",
    "extra":"TB-Extra"
}



CATEGORY_ALIASES = {
    "application-based": "Application",
    "application based": "Application",
    "definition": "Recall",
    "fact": "Recall",
    "example": "Comprehension",
    "hard": "Recall",
    "easy": "Recall",
    "medium": "Recall",
    "hots": "HOTS",
    "case study": "Case-Study",
    "casestudy": "Case-Study",
    "assertion reason": "Assertion-Reason",
    "assertionreason": "Assertion-Reason",
    "competency based": "Competency-Based",
    "competencybased": "Competency-Based",
    "data interpretation": "Data-Interpretation",
    "datainterpretation": "Data-Interpretation",
    "source based": "Source-Based",
    "sourcebased": "Source-Based",
    "visual interpretation": "Visual-Interpretation",
    "visualinterpretation": "Visual-Interpretation",
    "practical experimental": "Practical-Experimental",
    "practicalexperimental": "Practical-Experimental",
    "practical / experimental": "Practical-Experimental",
}

# Gemini model fallback chain — same pattern as your pipeline
MODEL_CHAIN = [
    "gemini-3.6-flash",
    "gemini-3.1-flash",
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash",
]


# ─────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────

class ValidationLog:
    def __init__(self):
        self.entries = []
        self.counts = {
            "nested_flattened": 0,
            "enum_fixed": 0,
            "datatype_fixed": 0,
            "field_inserted": 0,
            "llm_repair_invoked": 0,
            "llm_repair_succeeded": 0,
            "llm_repair_failed": 0,
            "model_retried": 0,
            "questions_passed": 0,
            "questions_failed": 0,
            "questiontext_generated": 0,
            "questions_dropped_missing_text": 0,
        }

    def log(self, qid: str, level: str, message: str):
        self.entries.append({"id": qid, "level": level, "message": message})
        print(f"  [{level}] [{qid}] {message}")

    def inc(self, key: str, by: int = 1):
        self.counts[key] = self.counts.get(key, 0) + by

    def summary(self):
        print("\n" + "=" * 55)
        print("VALIDATION SUMMARY")
        print("=" * 55)
        for k, v in self.counts.items():
            print(f"  {k}: {v}")
        errors   = [e for e in self.entries if e["level"] == "ERROR"]
        warnings = [e for e in self.entries if e["level"] == "WARNING"]
        print(f"  total_warnings: {len(warnings)}")
        print(f"  total_errors_remaining: {len(errors)}")
        print("=" * 55)


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def robust_json_load(path: str, vlog: Optional["ValidationLog"] = None):
    """
    Load a JSON file, auto-repairing unescaped double-quotes inside string
    values — the usual cause of upload failures when a question's text
    contains a quoted phrase, e.g.:
        "questionText": "What is the "respiration" process?"
    The stray inner quotes get backslash-escaped and parsing is retried
    until it succeeds or no more progress can be made.
    """
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    fixed_text = text
    fixes_applied = 0

    for _ in range(1000):
        try:
            data = json.loads(fixed_text)
            if fixes_applied and vlog:
                vlog.log("FILE", "FIX", f"Auto-escaped {fixes_applied} stray quote(s) in raw JSON before parsing")
            return data
        except json.JSONDecodeError as e:
            msg, pos = e.msg, e.pos

            if "Expecting ',' delimiter" in msg or "Expecting ':' delimiter" in msg:
                # a stray quote closed the string early — find it and escape it
                q_idx = fixed_text.rfind('"', 0, pos)
                if q_idx == -1:
                    raise
                fixed_text = fixed_text[:q_idx] + '\\"' + fixed_text[q_idx + 1:]
                fixes_applied += 1
                continue

            if "Unterminated string" in msg:
                # a later quote wasn't escaped, so the string never closed —
                # escape the next quote found after the string's start
                q_idx = fixed_text.find('"', pos + 1)
                if q_idx == -1:
                    raise
                fixed_text = fixed_text[:q_idx] + '\\"' + fixed_text[q_idx + 1:]
                fixes_applied += 1
                continue

            # some other malformation we don't know how to auto-repair
            raise

    # gave up after too many attempts — surface the original error
    return json.loads(text)



def flatten_questions(raw: list, vlog: ValidationLog) -> list:
    flat = []
    for item in raw:
        if isinstance(item, list):
            flat.extend(item)
            vlog.inc("nested_flattened", len(item))
        elif isinstance(item, dict):
            if "questions" in item and "questionType" not in item:
                inner = item["questions"]
                if isinstance(inner, list):
                    flat.extend(inner)
                    vlog.inc("nested_flattened", len(inner))
            else:
                flat.append(item)
    return flat


def normalise_enum(value: str, alias_map: dict, allowed: set) -> Optional[str]:
    if not value:
        return None
    if value in allowed:
        return value
    key = value.lower().strip()
    if key in alias_map:
        return alias_map[key]
    for a in allowed:
        if a.lower() == key:
            return a
    return None


def infer_category(q: dict) -> str:
    qt   = (q.get("questionType") or "").lower()
    text = (q.get("questionText") or "").lower()

    if qt == "assertion-reason" or ("assertion" in text and "reason" in text):
        return "Assertion-Reason"
    if qt == "competency-based":
        return "Competency-Based"
    if any(w in text for w in ["activity", "experiment", "observe", "apparatus", "procedure"]):
        return "Practical-Experimental"
    if any(w in text for w in ["read the following", "passage", "source", "extract"]):
        return "Source-Based"
    if any(w in text for w in ["graph", "table", "data", "interpret", "figure", "diagram"]):
        return "Data-Interpretation"
    if any(w in text for w in ["calculate", "find the", "determine", "compute", "how much", "what is the value"]):
        return "Application"
    if any(w in text for w in ["evaluate", "assess", "justify", "consequence", "implication"]):
        return "Evaluation"
    if any(w in text for w in ["analyse", "analyze", "compare", "differentiate", "distinguish"]):
        return "Analysis"
    if any(w in text for w in ["explain", "describe", "why", "how does", "what happens", "reason"]):
        return "Comprehension"
    if qt in ["truefalse", "fillblanks"]:
        return "Recall"
    if qt == "subjective":
        return "Analysis"
    return "Recall"


def clean_json_text(raw: str) -> str:
    """Strip markdown fences — same pattern used in your generators."""
    raw = raw.strip()
    if raw.startswith("```json"):
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif raw.startswith("```"):
        raw = raw.split("```")[1].split("```")[0].strip()
    return raw


# ─────────────────────────────────────────────
# AUTO-FIX (no LLM)
# ─────────────────────────────────────────────

def auto_fix(q: dict, file_source_type: str, vlog: ValidationLog) -> tuple[dict, list[str]]:
    """
    Apply all automatic fixes to a single question.
    Returns (fixed_question, list_of_remaining_unfixable_errors).
    """
    q = copy.deepcopy(q)
    unfixable = []
    qid = q.get("id", "?")

    # ── questionType ──────────────────────────
    qt_raw = q.get("questionType") or ""
    qt     = normalise_enum(qt_raw, QTYPE_ALIASES, ALLOWED_QUESTION_TYPES)
    if qt and qt != qt_raw:
        vlog.log(qid, "FIX", f"questionType '{qt_raw}' → '{qt}'")
        q["questionType"] = qt
        vlog.inc("enum_fixed")
    elif not qt:
        if qt_raw:
            unfixable.append(f"Invalid questionType='{qt_raw}'")
        else:
            unfixable.append("Missing questionType")

    qt_clean = (q.get("questionType") or "").lower().strip()

    # ── category ──────────────────────────────
    cat_raw = q.get("category") or ""
    cat     = normalise_enum(cat_raw, CATEGORY_ALIASES, ALLOWED_CATEGORIES)
    if not cat_raw or cat is None:
        inferred = infer_category(q)
        vlog.log(qid, "FIX", f"category '{cat_raw}' → inferred '{inferred}'")
        q["category"] = inferred
        vlog.inc("field_inserted" if not cat_raw else "enum_fixed")
    elif cat != cat_raw:
        vlog.log(qid, "FIX", f"category '{cat_raw}' → '{cat}'")
        q["category"] = cat
        vlog.inc("enum_fixed")

    # ── difficulty ────────────────────────────
    diff_raw = q.get("difficulty") or ""
    if diff_raw.lower() not in ALLOWED_DIFFICULTY:
        vlog.log(qid, "FIX", f"difficulty '{diff_raw}' → 'medium'")
        q["difficulty"] = "medium"
        vlog.inc("field_inserted" if not diff_raw else "enum_fixed")

    # ── questionText ──────────────────────────
    if not (q.get("questionText") or "").strip():
        unfixable.append("Empty/missing questionText")

    # ── sourceType ────────────────────────────
    src_raw = q.get("sourceType") or ""
    src     = normalise_enum(src_raw, SOURCE_TYPE_ALIASES, ALLOWED_SOURCE_TYPES)
    if not src_raw or src is None:
        vlog.log(qid, "FIX", f"sourceType '{src_raw}' → '{file_source_type}'")
        q["sourceType"] = file_source_type
        vlog.inc("field_inserted" if not src_raw else "enum_fixed")
    elif src != src_raw:
        vlog.log(qid, "FIX", f"sourceType '{src_raw}' → '{src}'")
        q["sourceType"] = src
        vlog.inc("enum_fixed")

    # ── pageNumber ────────────────────────────
    pn = q.get("pageNumber")
    if pn is not None and not isinstance(pn, bool):
        if isinstance(pn, (int, float)):
            pass  # already numeric, nothing to do
        else:
            fixed_pn = None
            if isinstance(pn, str):
                m = re.search(r"-?\d+", pn)
                if m:
                    fixed_pn = int(m.group())
            elif isinstance(pn, list):
                for item in pn:
                    if isinstance(item, bool):
                        continue
                    if isinstance(item, (int, float)):
                        fixed_pn = item
                        break
                    if isinstance(item, str):
                        m = re.search(r"-?\d+", item)
                        if m:
                            fixed_pn = int(m.group())
                            break
            elif isinstance(pn, dict):
                for v in pn.values():
                    if isinstance(v, bool):
                        continue
                    if isinstance(v, (int, float)):
                        fixed_pn = v
                        break
                    if isinstance(v, str):
                        m = re.search(r"-?\d+", v)
                        if m:
                            fixed_pn = int(m.group())
                            break

            if fixed_pn is not None:
                vlog.log(qid, "FIX", f"pageNumber {pn!r} → {fixed_pn}")
                q["pageNumber"] = fixed_pn
                vlog.inc("datatype_fixed")
            else:
                unfixable.append(f"pageNumber={pn!r} could not be converted to a number")

    # ── marks ─────────────────────────────────
    if q.get("marks") is None:
        default = 2 if qt_clean == "subjective" else 1
        q["marks"] = default
        vlog.log(qid, "FIX", f"marks missing → {default}")
        vlog.inc("field_inserted")

    # ── set ───────────────────────────────────
    if not q.get("set"):
        q["set"] = "A"
        vlog.log(qid, "FIX", "set missing → 'A'")
        vlog.inc("field_inserted")

    # ── subjective field rename ────────────────
    if qt_clean == "subjective":
        if q.get("subjectiveEvaluationPoints") and not q.get("subjective_evaluation_points"):
            q["subjective_evaluation_points"] = q.pop("subjectiveEvaluationPoints")
            vlog.log(qid, "FIX", "subjectiveEvaluationPoints → subjective_evaluation_points")
            vlog.inc("field_inserted")

    # ── MCQ ───────────────────────────────────
    if qt_clean == "mcq":
        opts = q.get("options") or []
        if len(opts) < 2:
            unfixable.append(f"MCQ has <2 options ({len(opts)})")
        else:
            # every option must explicitly carry isCorrect as a real bool
            # (covers missing key, null, "false"/"true" strings, 0/1, etc.)
            normalized = 0
            for o in opts:
                raw = o.get("isCorrect")
                as_bool = raw if isinstance(raw, bool) else (
                    str(raw).strip().lower() == "true" if raw is not None else False
                )
                if raw is None or not isinstance(raw, bool) or "isCorrect" not in o:
                    normalized += 1
                o["isCorrect"] = as_bool
            if normalized:
                vlog.log(qid, "FIX", f"MCQ: normalized isCorrect to explicit bool on {normalized} option(s)")
                vlog.inc("field_inserted", normalized)

            correct = [o for o in opts if o.get("isCorrect")]
            if len(correct) == 0:
                unfixable.append("MCQ has 0 correct options")
            elif len(correct) > 1:
                first = True
                for o in opts:
                    if o.get("isCorrect"):
                        if not first:
                            o["isCorrect"] = False
                        first = False
                vlog.log(qid, "FIX", "MCQ multiple correct → kept first only")
                vlog.inc("datatype_fixed")
        if not q.get("correctAnswer"):
            correct_opt = next((o["optionText"] for o in opts if o.get("isCorrect")), None)
            if correct_opt:
                q["correctAnswer"] = correct_opt
                vlog.log(qid, "FIX", "correctAnswer populated from options")
                vlog.inc("field_inserted")

    # ── fillblanks ────────────────────────────
    elif qt_clean == "fillblanks":
        if not q.get("blanks"):
            unfixable.append("fillblanks missing blanks[]")
        # else:
        #     if not q.get("correctAnswer"):
        #         q["correctAnswer"] = ", ".join(str(b) for b in q["blanks"])
        #         vlog.log(qid, "FIX", "correctAnswer populated from blanks[]")
        #         vlog.inc("field_inserted")

    # ── truefalse ─────────────────────────────
    elif qt_clean == "truefalse":
        ca = q.get("correctAnswer")
        if ca is None:
            unfixable.append("truefalse missing correctAnswer")
        elif isinstance(ca, str):
            if ca.lower() == "true":
                q["correctAnswer"] = True
                vlog.log(qid, "FIX", "correctAnswer 'true' str → bool True")
                vlog.inc("datatype_fixed")
            elif ca.lower() == "false":
                q["correctAnswer"] = False
                vlog.log(qid, "FIX", "correctAnswer 'false' str → bool False")
                vlog.inc("datatype_fixed")
            else:
                unfixable.append(f"truefalse correctAnswer='{ca}' not parseable")

    # ── multi ─────────────────────────────────
    elif qt_clean == "multi":
        opts = q.get("options") or []
        multi = q.get("multi") or []

        if not opts:
            unfixable.append("multi missing options")

        if not multi:
            unfixable.append("multi missing multi[]")

        # Remove isCorrect if present
        for opt in opts:
            if "isCorrect" in opt:
                del opt["isCorrect"]
                vlog.log(qid, "FIX", "Removed isCorrect from multi options")
                vlog.inc("field_removed")

        # correctAnswer must always be null
        if q.get("correctAnswer") is not None:
            q["correctAnswer"] = None
            vlog.log(qid, "FIX", "Removed correctAnswer for multi question")
            vlog.inc("field_removed")

    # ── matchfollowing ────────────────────────
    elif qt_clean == "matchfollowing":
        left  = q.get("leftItems") or []
        right = q.get("rightItems") or []
        maps  = q.get("correctMappings") or []
        if not left:  unfixable.append("matchfollowing missing leftItems")
        if not right: unfixable.append("matchfollowing missing rightItems")
        if not maps:  unfixable.append("matchfollowing missing correctMappings")
        else:
            for m in maps:
                if isinstance(m, dict):
                    li = m.get("leftIndex")
                    ri = m.get("rightIndex")
                    if li is None or ri is None:
                        unfixable.append(f"correctMappings missing leftIndex/rightIndex: {m}")
                    else:
                        if li >= len(left):  unfixable.append(f"leftIndex {li} out of bounds")
                        if ri >= len(right): unfixable.append(f"rightIndex {ri} out of bounds")

    # ── subjective ────────────────────────────
    elif qt_clean == "subjective":
        pts = q.get("subjectiveEvaluationPoints") or q.get("subjective_evaluation_points")
        if not pts:
            unfixable.append("subjective missing subjectiveEvaluationPoints")

    return q, unfixable


# ─────────────────────────────────────────────
# LLM REPAIR  (Gemini — same client as pipeline)
# ─────────────────────────────────────────────

def build_repair_prompt(q: dict, errors: list) -> str:
    return f"""You are a question bank repair assistant for NCERT Class 10.

The following question JSON has validation errors.
Fix every error listed. Return ONLY the corrected JSON object — no explanation, no markdown.

ERRORS:
{chr(10).join(f"- {e}" for e in errors)}

RULES:
- questionType: one of mcq, fillblanks, multi, truefalse, matchfollowing, subjective
- difficulty: one of easy, medium, hard
- category: one of {ALLOWED_CATEGORIES}
- MCQ: exactly 1 isCorrect=true option; correctAnswer = that option text
- fillblanks: blanks[] lists the missing words in order
- truefalse: correctAnswer must be boolean true or false (not a string)
- multi: multi[] lists correct option texts
- matchfollowing: leftItems and rightItems are string arrays; correctMappings uses leftIndex and rightIndex (0-indexed integers)
- subjective: subjective_evaluation_points required — array of objects with "point" (string) and "marks" (number)
- pageNumber must be number not a string,array or object.
- Do NOT change: questionText, conceptId, id, topic, pageNumber, imageName, set

QUESTION JSON:
{json.dumps(q, indent=2, ensure_ascii=False)}
"""


def llm_repair(
    q: dict,
    errors: list,
    client,
    model_chain: list,
    vlog: ValidationLog
) -> Optional[dict]:
    """
    Try to repair a question using Gemini.
    Uses same fallback pattern as your pipeline generators.
    Returns repaired dict or None.
    """
    qid = q.get("id", "?")
    prompt = build_repair_prompt(q, errors)
    current_model_idx = 0

    while current_model_idx < len(model_chain):
        model_name = model_chain[current_model_idx]

        if current_model_idx > 0:
            vlog.inc("model_retried")
            vlog.log(qid, "INFO", f"Retrying repair with {model_name}")

        try:
            print(f"    Requesting repair via {model_name}")
            response = client.models.generate_content(
                model=model_name,
                contents=[prompt],
                config={"response_mime_type": "application/json"},
            )
            raw = response.text
            raw = clean_json_text(raw)
            repaired = json.loads(raw)

            if isinstance(repaired, dict) and repaired.get("questionType"):
                vlog.log(qid, "INFO", f"LLM repair succeeded via {model_name}")
                vlog.inc("llm_repair_succeeded")
                return repaired
            else:
                vlog.log(qid, "WARNING", f"LLM returned unexpected structure via {model_name}")
                current_model_idx += 1

        except APIError as e:
            vlog.log(qid, "WARNING", f"{model_name} API error: {e.message}")
            current_model_idx += 1
            time.sleep(7)

        except json.JSONDecodeError as e:
            vlog.log(qid, "WARNING", f"{model_name} returned invalid JSON: {e}")
            current_model_idx += 1

        except Exception as e:
            vlog.log(qid, "WARNING", f"{model_name} failed: {e}")
            current_model_idx += 1
            time.sleep(3)

    vlog.log(qid, "ERROR", "All models failed to repair this question")
    vlog.inc("llm_repair_failed")
    return None


# ─────────────────────────────────────────────
# LLM: GENERATE MISSING questionText
# ─────────────────────────────────────────────

def build_generate_questiontext_prompt(q: dict) -> str:
    return f"""You are a question bank repair assistant for NCERT Class 10 .

The following question JSON is missing "questionText" (or it is empty).
Using the other fields present (questionType, options/blanks/leftItems/rightItems/
correctAnswer/subjective_evaluation_points, topic, conceptId, category, etc.) figure out
what question was most likely intended, and write a clear, well-formed questionText for it.

Return ONLY a JSON object of the form: {{"questionText": "..."}}
No explanation, no markdown, no other fields.

If there is genuinely not enough information in the fields below to infer any reasonable
question, return exactly: {{"questionText": null}}

QUESTION JSON:
{json.dumps(q, indent=2, ensure_ascii=False)}
"""


def generate_missing_question_text(
    q: dict,
    client,
    model_chain: list,
    vlog: ValidationLog,
) -> Optional[str]:
    """
    Ask Gemini to author a questionText for a question that's missing one.
    Returns the generated text, or None if no model could produce one.
    """
    qid = q.get("id", "?")
    prompt = build_generate_questiontext_prompt(q)
    current_model_idx = 0

    while current_model_idx < len(model_chain):
        model_name = model_chain[current_model_idx]

        if current_model_idx > 0:
            vlog.inc("model_retried")
            vlog.log(qid, "INFO", f"Retrying questionText generation with {model_name}")

        try:
            print(f"    Requesting questionText generation via {model_name}")
            response = client.models.generate_content(
                model=model_name,
                contents=[prompt],
                config={"response_mime_type": "application/json"},
            )
            raw = clean_json_text(response.text)
            parsed = json.loads(raw)

            text = parsed.get("questionText") if isinstance(parsed, dict) else None
            if text and isinstance(text, str) and text.strip():
                vlog.log(qid, "INFO", f"questionText generated via {model_name}")
                return text.strip()
            else:
                vlog.log(qid, "WARNING", f"{model_name} could not infer a questionText")
                current_model_idx += 1

        except APIError as e:
            vlog.log(qid, "WARNING", f"{model_name} API error: {e.message}")
            current_model_idx += 1
            time.sleep(7)

        except json.JSONDecodeError as e:
            vlog.log(qid, "WARNING", f"{model_name} returned invalid JSON: {e}")
            current_model_idx += 1

        except Exception as e:
            vlog.log(qid, "WARNING", f"{model_name} failed: {e}")
            current_model_idx += 1
            time.sleep(3)

    return None


# ─────────────────────────────────────────────
# POST-REPAIR STRICT CHECK
# ─────────────────────────────────────────────

def strict_validate(q: dict) -> list:
    """Return remaining errors after all fixes. Empty list = clean."""
    errors = []
    qt = (q.get("questionType") or "").lower().strip()

    if qt not in ALLOWED_QUESTION_TYPES:
        errors.append(f"questionType='{q.get('questionType')}' invalid")
    if not (q.get("questionText") or "").strip():
        errors.append("questionText empty")
    if not q.get("category") or q["category"] not in ALLOWED_CATEGORIES:
        errors.append(f"category='{q.get('category')}' invalid")
    if not q.get("difficulty") or q["difficulty"] not in ALLOWED_DIFFICULTY:
        errors.append(f"difficulty='{q.get('difficulty')}' invalid")
    if not q.get("sourceType") or q["sourceType"] not in ALLOWED_SOURCE_TYPES:
        errors.append(f"sourceType='{q.get('sourceType')}' invalid")

    if qt == "mcq":
        opts = q.get("options") or []
        correct = sum(1 for o in opts if o.get("isCorrect"))
        if correct != 1:
            errors.append(f"MCQ has {correct} correct options (need 1)")
    if qt == "fillblanks" and not q.get("blanks"):
        errors.append("fillblanks missing blanks[]")
    if qt == "truefalse" and q.get("correctAnswer") is None:
        errors.append("truefalse missing correctAnswer")
    if qt == "multi" and not q.get("multi"):
        errors.append("multi missing multi[]")
    if qt == "matchfollowing":
        if not q.get("leftItems") or not q.get("rightItems") or not q.get("correctMappings"):
            errors.append("matchfollowing missing required structural fields")
    if qt == "subjective":
        pts = q.get("subjectiveEvaluationPoints") or q.get("subjective_evaluation_points")
        if not pts:
            errors.append("subjective missing subjectiveEvaluationPoints")

    return errors


# ─────────────────────────────────────────────
# INFER FILE-LEVEL SOURCE TYPE
# ─────────────────────────────────────────────

def infer_file_source_type(qs: list, override: Optional[str] = None) -> str:
    if override:
        canonical = normalise_enum(override, SOURCE_TYPE_ALIASES, ALLOWED_SOURCE_TYPES)
        return canonical or override
    src_counter = {}
    for q in qs:
        s = q.get("sourceType", "")
        if s:
            src_counter[s] = src_counter.get(s, 0) + 1
    if src_counter:
        top = max(src_counter, key=src_counter.get)
        canonical = normalise_enum(top, SOURCE_TYPE_ALIASES, ALLOWED_SOURCE_TYPES)
        if canonical:
            return canonical
    return "TB-Full"


# ─────────────────────────────────────────────
# MAIN VALIDATE FUNCTION
# ─────────────────────────────────────────────

def validate_file(
    input_path: str,
    subject_name: str,
    output_path: Optional[str] = None,
    source_type: Optional[str] = None,
    use_llm: bool = True,
    gemini_client=None,
    model_chain: Optional[list] = None,
) -> str:
    """
    Validate and auto-repair a combined question bank JSON file.

    Parameters
    ----------
    input_path   : path to the JSON file to validate
    output_path  : where to save the fixed file (default: input_validated.json)
    source_type  : override sourceType for all questions (e.g. "Indirect", "TB-Full")
    use_llm      : whether to call Gemini for questions that can't be auto-fixed
    gemini_client: pass your existing genai.Client() to reuse it
    model_chain  : override the model fallback chain

    Returns
    -------
    Path to the validated output file.
    """

    global ALLOWED_CATEGORIES
    ALLOWED_CATEGORIES = set(get_allowed_categories(subject_name))

    if output_path is None:
        output_path = input_path

    vlog = ValidationLog()
    mc   = model_chain or MODEL_CHAIN

    print(f"\n{'='*55}")
    print(f"VALIDATING: {input_path}")
    print(f"{'='*55}")

    # ── Parse ─────────────────────────────────
    try:
        data = robust_json_load(input_path, vlog)
    except json.JSONDecodeError as e:
        print(f"[FATAL] Cannot parse JSON even after quote-repair attempts: {e}")
        return input_path
    except FileNotFoundError:
        print(f"[FATAL] File not found: {input_path}")
        return input_path

    # ── Flatten ───────────────────────────────
    raw_qs = data.get("questions", [])
    qs = flatten_questions(raw_qs, vlog)
    print(f"Questions (after flatten): {len(qs)}")
    if vlog.counts["nested_flattened"]:
        print(f"  ↳ Flattened {vlog.counts['nested_flattened']} nested entries")

    # ── Source type ───────────────────────────
    file_src = infer_file_source_type(qs, source_type)
    print(f"File sourceType: {file_src}")

    # ── Gemini client ─────────────────────────
    client = gemini_client
    if use_llm and client is None:
        try:
            key = os.getenv("GEMINI_API_KEY")
            client = genai.Client(api_key=key)
        except Exception as e:
            print(f"[WARNING] Could not init Gemini client: {e}. LLM repair disabled.")
            use_llm = False

    # ── Process each question ─────────────────
    validated = []
    failed    = []
    dropped   = []

    for idx, q in enumerate(qs):
        qid = q.get("id", f"index_{idx}")

        # Step 0 — questionText missing: try to have the LLM write one;
        # if that's not possible, drop just this question (not the whole file).
        if not (q.get("questionText") or "").strip():
            generated = None
            if use_llm and client:
                vlog.log(qid, "INFO", "questionText missing — attempting LLM generation")
                generated = generate_missing_question_text(q, client, mc, vlog)

            if generated:
                q["questionText"] = generated
                vlog.log(qid, "FIX", "questionText generated by LLM")
                vlog.inc("questiontext_generated")
            else:
                vlog.log(qid, "ERROR", "questionText missing/ungeneratable — dropping question")
                vlog.inc("questions_dropped_missing_text")
                dropped.append({"id": qid, "reason": "questionText missing and could not be generated"})
                continue

        # Step 1 — auto-fix
        fixed_q, unfixable = auto_fix(q, file_src, vlog)

        # Step 2 — LLM repair if needed
        if unfixable:
            if use_llm and client:
                vlog.log(qid, "INFO", f"Sending to LLM ({len(unfixable)} unfixable errors)")
                vlog.inc("llm_repair_invoked")
                repaired = llm_repair(fixed_q, unfixable, client, mc, vlog)

                if repaired:
                    # re-run auto-fix on LLM output
                    repaired, _ = auto_fix(repaired, file_src, vlog)
                    remaining   = strict_validate(repaired)
                    if remaining:
                        vlog.log(qid, "ERROR", f"Still invalid after LLM repair: {remaining}")
                        failed.append({"id": qid, "errors": remaining, "question": repaired})
                        vlog.inc("questions_failed")
                    else:
                        validated.append(repaired)
                        vlog.inc("questions_passed")
                else:
                    remaining = strict_validate(fixed_q)
                    vlog.log(qid, "ERROR", f"LLM repair failed. Remaining: {remaining}")
                    failed.append({"id": qid, "errors": remaining, "question": fixed_q})
                    vlog.inc("questions_failed")
            else:
                remaining = strict_validate(fixed_q)
                if remaining:
                    vlog.log(qid, "ERROR", f"Cannot fix without LLM: {remaining}")
                    failed.append({"id": qid, "errors": remaining, "question": fixed_q})
                    vlog.inc("questions_failed")
                else:
                    validated.append(fixed_q)
                    vlog.inc("questions_passed")
        else:
            remaining = strict_validate(fixed_q)
            if remaining:
                vlog.log(qid, "ERROR", f"Strict check failed: {remaining}")
                failed.append({"id": qid, "errors": remaining, "question": fixed_q})
                vlog.inc("questions_failed")
            else:
                validated.append(fixed_q)
                vlog.inc("questions_passed")

    # ── Save output ───────────────────────────
    all_qs = validated + [f["question"] for f in failed]

    out_data = {k: v for k, v in data.items() if k != "questions"}
    out_data["questions"] = all_qs
    out_data["validationMeta"] = {
        "totalInput": len(qs),
        "passed": len(validated),
        "failed": len(failed),
        "dropped": len(dropped),
        "failedIds": [f["id"] for f in failed],
        "failedDetails": [{"id": f["id"], "errors": f["errors"]} for f in failed],
        "droppedIds": [d["id"] for d in dropped],
        "droppedDetails": dropped,
    }

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(out_data, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Saved: {output_path}")
    print(f"  {len(validated)} passed | {len(failed)} need review | {len(dropped)} dropped (missing questionText)")

    if failed:
        print(f"\n  Failed IDs:")
        for fq in failed:
            print(f"    {fq['id']}: {fq['errors']}")

    if dropped:
        print(f"\n  Dropped IDs (questionText missing, could not be repaired):")
        for dq in dropped:
            print(f"    {dq['id']}: {dq['reason']}")

    vlog.summary()
    return output_path


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Validate + auto-repair NCERT question bank JSON.")
    parser.add_argument("--input",       required=True,           help="Input JSON file path")
    parser.add_argument("--subject",     required=True,           help="Subject Name")
    parser.add_argument("--output",      default=None,            help="Output JSON file path")
    parser.add_argument("--source-type", default=None,            help="Override sourceType (e.g. Indirect, TB-Full)")
    parser.add_argument("--no-llm",      action="store_true",     help="Auto-fix only, no Gemini repair calls")
    args = parser.parse_args()

    validate_file(
        input_path=args.input,
        subject_name=args.subject,
        output_path=args.output,
        source_type=args.source_type,
        use_llm=not args.no_llm,
    )

if __name__ == "__main__":
    main()