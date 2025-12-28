import os
import requests
import re
import time

# -------------------------------------------------
# API KEY
# -------------------------------------------------
API_KEY = os.getenv("GEMINI_API_KEY2")
if not API_KEY:
    raise ValueError("❌ GEMINI_API_KEY2 environment variable tanımlı değil!")

GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.5-flash:generateContent?key=" + API_KEY
)

# -------------------------------------------------
# TEK SORU ÜRET
# -------------------------------------------------
def generate_one_question(lesson, topic, difficulty):
    prompt = f"""
Sen bir 8. sınıf LGS soru üretme uzmanısın.

Ders: {lesson}
Konu: {topic}
Zorluk: {difficulty}

AŞAĞIDAKİ FORMAT DIŞINA ASLA ÇIKMA.
Satır sırasını bozma, ek metin yazma.

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
            "temperature": 0.3,
            "maxOutputTokens": 500
        }
    }

    r = requests.post(GEMINI_API_URL, json=payload, timeout=60)
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]


# -------------------------------------------------
# PARSE
# -------------------------------------------------
def parse_question(text):
    def find(patterns):
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE | re.MULTILINE)
            if m:
                return m.group(1).strip()
        return ""

    question = find([
        r"^Soru\s*:\s*(.+)$"
    ])

    choices = [
        "A) " + find([r"^A[\)\.\-\s]\s*(.+)$"]),
        "B) " + find([r"^B[\)\.\-\s]\s*(.+)$"]),
        "C) " + find([r"^C[\)\.\-\s]\s*(.+)$"]),
        "D) " + find([r"^D[\)\.\-\s]\s*(.+)$"]),
    ]

    answer = find([
        r"^Cevap\s*:\s*([A-D])$",
        r"^Doğru\s*Cevap\s*:\s*([A-D])$"
    ])

    explanation = find([
        r"^Çözüm\s*:\s*(.+)$",
        r"^Çözümü\s*:\s*(.+)$",
        r"^Açıklama\s*:\s*(.+)$"
    ])

    # Minimum güvenlik
    if not question or not answer:
        raise ValueError("Soru veya cevap bulunamadı")

    # Şıklar boşsa, yine hata
    if any(len(c.strip()) <= 3 for c in choices):
        raise ValueError("Şıklar eksik")

    return {
        "question": question,
        "choices": choices,
        "answer": answer,
        "explanation": explanation or "Çözüm bilgisi verilmemiştir."
    }

# -------------------------------------------------
# ÇOKLU SORU + RETRY
# -------------------------------------------------
def generate_questions(lesson, topic, difficulty, count):
    questions = []
    max_total_attempts = count * 5  # üst sınır

    attempts = 0
    while len(questions) < count and attempts < max_total_attempts:
        attempts += 1
        try:
            raw = generate_one_question(lesson, topic, difficulty)
            q = parse_question(raw)
            questions.append(q)
        except Exception:
            time.sleep(0.4)

    if not questions:
        raise ValueError("Hiç geçerli soru üretilemedi")

    return questions
