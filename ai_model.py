import os
import requests
import re

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY tanımlı değil")

GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.5-flash:generateContent?key=" + API_KEY
)

HEADERS = {"Content-Type": "application/json"}


def _call_gemini(prompt: str) -> str:
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 1200
        }
    }

    r = requests.post(
        GEMINI_API_URL,
        headers=HEADERS,
        json=payload,
        timeout=60
    )
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]


def _parse_question_block(text: str):
    def find(pattern):
        m = re.search(pattern, text, re.DOTALL)
        return m.group(1).strip() if m else None

    question = find(r"Soru:\s*(.*)")
    A = find(r"A\)\s*(.*)")
    B = find(r"B\)\s*(.*)")
    C = find(r"C\)\s*(.*)")
    D = find(r"D\)\s*(.*)")
    answer = find(r"Cevap:\s*([A-D])")
    explanation = find(r"Çözüm:\s*(.*)")

    if not all([question, A, B, C, D, answer, explanation]):
        return None

    return {
        "question": question,
        "choices": [
            f"A) {A}",
            f"B) {B}",
            f"C) {C}",
            f"D) {D}",
        ],
        "answer": answer,
        "explanation": explanation
    }


def generate_questions(lesson, topic, difficulty, count):
    count = int(count)
    questions = []

    prompt = f"""
Sen bir 8. sınıf LGS soru üretme uzmanısın.

Ders: {lesson}
Konu: {topic}
Zorluk: {difficulty}

Her soruyu AŞAĞIDAKİ FORMATTA üret:

Soru: ...
A) ...
B) ...
C) ...
D) ...
Cevap: A
Çözüm: ...

SADECE BU FORMATI KULLAN.
"""

    attempts = 0
    while len(questions) < count and attempts < count * 2:
        attempts += 1
        raw = _call_gemini(prompt)
        q = _parse_question_block(raw)
        if q:
            questions.append(q)

    if not questions:
        raise ValueError("Model geçerli soru üretemedi")

    return questions
