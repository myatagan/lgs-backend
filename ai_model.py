import os
import requests
import re

# ==================================================
# GEMINI CONFIG
# ==================================================
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY tanımlı değil")

GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.5-flash:generateContent?key=" + API_KEY
)

HEADERS = {"Content-Type": "application/json"}


# ==================================================
# LOW LEVEL GEMINI CALL (TEK ÇAĞRI, SAFE)
# ==================================================
def _call_gemini(prompt: str) -> str:
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 2000
        }
    }

    r = requests.post(
        GEMINI_API_URL,
        headers=HEADERS,
        json=payload,
        timeout=20  # gunicorn worker öldürmez
    )

    # 🔥 429 VE DİĞER HATALAR BURADA YAKALANIR
    r.raise_for_status()

    return r.json()["candidates"][0]["content"]["parts"][0]["text"]


# ==================================================
# PARSE SINGLE QUESTION BLOCK
# ==================================================
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


# ==================================================
# MAIN ENTRY — TEK GEMINI ÇAĞRISI
# ==================================================
def generate_questions(lesson, topic, difficulty, count):
    count = int(count)

    prompt = f"""
Sen bir 8. sınıf LGS soru üretme uzmanısın.

Ders: {lesson}
Konu: {topic}
Zorluk: {difficulty}

AŞAĞIDAKİ FORMATTA TAM OLARAK {count} SORU ÜRET:

Soru 1:
Soru: ...
A) ...
B) ...
C) ...
D) ...
Cevap: A
Çözüm: ...

Soru 2:
...

KURALLAR:
- SADECE BU FORMAT
- Markdown YOK
- Açıklama YOK
"""

    raw = _call_gemini(prompt)

    # 🔥 BLOK BLOK AYIR
    blocks = raw.split("Soru ")
    questions = []

    for block in blocks:
        if len(questions) >= count:
            break

        q = _parse_question_block(block)
        if q:
            questions.append(q)

    if len(questions) == 0:
        raise RuntimeError("Model geçerli soru üretemedi")

    return questions
