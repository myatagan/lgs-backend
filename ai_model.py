import os
import json
import requests

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("GEMINI API KEY tanımlı değil")

GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.5-flash:generateContent?key=" + API_KEY
)

HEADERS = {"Content-Type": "application/json"}


def generate_questions(lesson, topic, difficulty, count):
    count = int(count)

    prompt = f"""
You are an exam question generator for 8th grade LGS.

Lesson: {lesson}
Topic: {topic}
Difficulty: {difficulty}
Number of questions: {count}

STRICT RULES:
- Output ONLY valid JSON
- No markdown
- No explanation text outside JSON

FORMAT:
[
  {{
    "question": "...",
    "choices": ["A) ...", "B) ...", "C) ...", "D) ..."],
    "answer": "A",
    "explanation": "..."
  }}
]
"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 2000,
            "response_mime_type": "application/json"
        }
    }

    response = requests.post(
        GEMINI_API_URL,
        headers=HEADERS,
        json=payload,
        timeout=60
    )

    response.raise_for_status()

    raw = response.json()["candidates"][0]["content"]["parts"][0]["text"]

    try:
        questions = json.loads(raw)
    except Exception:
        raise ValueError("Model geçerli JSON üretemedi")

    if not isinstance(questions, list) or len(questions) == 0:
        raise ValueError("Model boş soru döndürdü")

    return questions[:count]
