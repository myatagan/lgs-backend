import os
import requests
import re
import time
from typing import Optional, Dict, List

# ============================
# GEMINI CONFIG
# ============================
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY tanımlı değil")

GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.5-flash:generateContent?key=" + API_KEY
)

HEADERS = {"Content-Type": "application/json"}

# ============================
# LOW LEVEL CALL (SAFE)
# ============================
def _call_gemini(prompt: str) -> str:
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 1200,
        },
    }

    try:
        r = requests.post(
            GEMINI_API_URL,
            headers=HEADERS,
            json=payload,
            timeout=15,  # 🔥 worker öldürmesin
        )
        r.raise_for_status()
        data = r.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]

    except requests.exceptions.Timeout:
        raise RuntimeError("AI isteği zaman aşımına uğradı")

    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"AI bağlantı hatası: {e}")

    except Exception as e:
        # beklenmeyen json shape vs.
        raise RuntimeError(f"AI cevap parse hatası: {e}")


# ============================
# PARSE ONE QUESTION (ROBUST)
# ============================
_LINE = r"[^\n\r]*"

def _find_line(text: str, patterns: List[str]) -> Optional[str]:
    """
    Birden fazla pattern dener, ilk eşleşen grubun içeriğini döndürür.
    Satır bazlı yakalar (DOTALL yok).
    """
    for p in patterns:
        m = re.search(p, text, flags=re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return None

def _normalize(text: str) -> str:
    # ufak normalize: smart quotes vb.
    return (
        text.replace("“", '"')
            .replace("”", '"')
            .replace("’", "'")
            .replace("‘", "'")
            .strip()
    )

def _parse_question_block(text: str) -> Optional[Dict]:
    text = _normalize(text)

    # Soru: satırı (bazı modeller "Soru -" yazabiliyor)
    question = _find_line(text, [
        rf"^\s*Soru\s*[:\-]\s*({_LINE})\s*$",
        rf"\n\s*Soru\s*[:\-]\s*({_LINE})\s*$",
    ])

    A = _find_line(text, [
        rf"^\s*A\)\s*({_LINE})\s*$",
        rf"\n\s*A\)\s*({_LINE})\s*$",
    ])
    B = _find_line(text, [
        rf"^\s*B\)\s*({_LINE})\s*$",
        rf"\n\s*B\)\s*({_LINE})\s*$",
    ])
    C = _find_line(text, [
        rf"^\s*C\)\s*({_LINE})\s*$",
        rf"\n\s*C\)\s*({_LINE})\s*$",
    ])
    D = _find_line(text, [
        rf"^\s*D\)\s*({_LINE})\s*$",
        rf"\n\s*D\)\s*({_LINE})\s*$",
    ])

    answer = _find_line(text, [
        r"^\s*Cevap\s*[:\-]\s*([A-D])\s*$",
        r"\n\s*Cevap\s*[:\-]\s*([A-D])\s*$",
    ])

    # Çözüm bazen çok satır olabilir → burada DOTALL kullanacağız ama sınır koyacağız.
    m_exp = re.search(r"Çözüm\s*[:\-]\s*(.+)\s*$", text, flags=re.IGNORECASE | re.DOTALL)
    explanation = m_exp.group(1).strip() if m_exp else None

    if not all([question, A, B, C, D, answer, explanation]):
        return None

    return {
        "question": question,
        "choices": [f"A) {A}", f"B) {B}", f"C) {C}", f"D) {D}"],
        "answer": answer,
        "explanation": explanation,
    }


# ============================
# MAIN ENTRY
# ============================
def generate_questions(lesson, topic, difficulty, count):
    count = int(count)
    questions = []

    # Daha net, sapmayı azaltan prompt
    prompt = f"""
Sen bir 8. sınıf LGS soru üretme uzmanısın.

Ders: {lesson}
Konu: {topic}
Zorluk: {difficulty}

TEK BİR SORU üret ve SADECE şu formatta yaz (başka hiçbir şey yazma):

Soru: ...
A) ...
B) ...
C) ...
D) ...
Cevap: A
Çözüm: ...

Not:
- Şıklar tek satır olsun.
- Cevap sadece A/B/C/D harfi olsun.
"""

    attempts = 0
    max_attempts = max(6, count * 3)  # biraz daha tolerans

    while len(questions) < count and attempts < max_attempts:
        attempts += 1

        raw = _call_gemini(prompt)
        q = _parse_question_block(raw)

        if q:
            questions.append(q)

        time.sleep(0.6)  # rate-limit + stabilite

    if not questions:
        raise ValueError("Model geçerli soru üretemedi")

    return questions[:count]
