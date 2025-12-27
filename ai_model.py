import os
import requests
import re

API_KEY = os.getenv("GEMINI_API_KEY2")
if not API_KEY:
    raise ValueError("❌ GEMINI_API_KEY2 environment variable tanımlı değil!")

GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.5-flash:generateContent?key=" + API_KEY
)

def generate_one_question(lesson, topic, difficulty):
    prompt = f"""
Sen bir 8. sınıf LGS soru üretme uzmanısın.

Ders: {lesson}
Konu: {topic}
Zorluk: {difficulty}

Aşağıdaki format DIŞINA ÇIKMA:

Soru: ...
A) ...
B) ...
C) ...
D) ...
Cevap: A
Çözüm: ...
"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 600
        }
    }

    r = requests.post(GEMINI_API_URL, json=payload, timeout=60)
    r.raise_for_status()
    text = r.json()["candidates"][0]["content"]["parts"][0]["text"]

    return text


def parse_question(text):
    def find(pattern):
        m = re.search(pattern, text, re.DOTALL)
        return m.group(1).strip() if m else ""

    question = find(r"Soru:\s*(.*)")
    choices = [
        "A) " + find(r"A\)\s*(.*)"),
        "B) " + find(r"B\)\s*(.*)"),
        "C) " + find(r"C\)\s*(.*)"),
        "D) " + find(r"D\)\s*(.*)")
    ]
    answer = find(r"Cevap:\s*([A-D])")
    explanation = find(r"Çözüm:\s*(.*)")

    return {
        "question": question,
        "choices": choices,
        "answer": answer,
        "explanation": explanation
    }


def generate_questions(lesson, topic, difficulty, count):
    questions = []

    for _ in range(count):
        raw = generate_one_question(lesson, topic, difficulty)
        q = parse_question(raw)
        questions.append(q)

    return questions
