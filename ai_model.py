import os
import json
import re
import time
import requests

# ============================
# OpenRouter config
# ============================
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise RuntimeError("OPENROUTER_API_KEY missing in environment variables")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://lgssorubankasi.netlify.app",
    "X-Title": "LGS Question Bank",
}

MODEL = "mistralai/mistral-7b-instruct"


# ============================
# Helpers
# ============================
def _strip_fences(text: str) -> str:
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"```$", "", text).strip()
    return text


def _extract_json(text: str) -> str:
    text = _strip_fences(text)
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        return text[start:end + 1]
    return text


def _safe_json_loads(text: str):
    text = _extract_json(text)
    text = text.replace("“", '"').replace("”", '"')
    text = re.sub(r",\s*([}\]])", r"\1", text)
    return json.loads(text)


def _call_llm(prompt: str, temperature=0.25, max_tokens=1600) -> str:
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a strict JSON generator. "
                    "Return ONLY valid JSON. No explanations."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    last_error = None
    for _ in range(3):
        try:
            r = requests.post(
                OPENROUTER_URL,
                headers=HEADERS,
                json=payload,
                timeout=20
            )
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            last_error = e
            time.sleep(0.5)

    raise RuntimeError(f"OpenRouter call failed: {last_error}")


# ============================
# Main API
# ============================
def generate_questions(lesson, topic, difficulty, count):
    count = int(count)

    prompt = f"""
Generate {count} multiple-choice exam questions for Turkish LGS (8th grade).

Lesson: {lesson}
Topic: {topic}
Difficulty: {difficulty}

RULES:
- Output ONLY valid JSON
- JSON must be an array
- Each item MUST have:
  - question (string)
  - choices (array of 4 strings starting with A) B) C) D))
  - answer (A, B, C, or D)
  - explanation (string)

FORMAT EXAMPLE:
[
  {{
    "question": "....",
    "choices": ["A) ...", "B) ...", "C) ...", "D) ..."],
    "answer": "A",
    "explanation": "..."
  }}
]
"""

    raw = _call_llm(prompt)

    try:
        questions = _safe_json_loads(raw)
    except Exception:
        # repair pass
        repair_prompt = f"""
Fix the following content into STRICT JSON only.
No markdown. No text outside JSON.

CONTENT:
{raw}
"""
        fixed = _call_llm(repair_prompt, temperature=0.0)
        questions = _safe_json_loads(fixed)

    if not isinstance(questions, list) or len(questions) == 0:
        raise ValueError("LLM returned empty or invalid output")

    clean = []
    for q in questions:
        if not isinstance(q, dict):
            continue
        if not all(k in q for k in ("question", "choices", "answer", "explanation")):
            continue
        if not isinstance(q["choices"], list) or len(q["choices"]) != 4:
            continue
        if q["answer"] not in ("A", "B", "C", "D"):
            continue

        clean.append({
            "question": q["question"].strip(),
            "choices": [c.strip() for c in q["choices"]],
            "answer": q["answer"].strip(),
            "explanation": q["explanation"].strip(),
        })

    if not clean:
        raise ValueError("No valid questions after validation")

    return clean[:count]
