import os
import json
import requests
import ast

# ----------------------------------------------------------
# 1) API KEY kontrolü
# ----------------------------------------------------------
API_KEY = os.getenv("GEMINI_API_KEY2")
if not API_KEY:
    raise ValueError("❌ GEMINI_API_KEY2 environment variable tanımlı değil!")

# Gemini Flash endpoint
GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.5-flash:generateContent?key=" + API_KEY
)

# ----------------------------------------------------------
# 2) JSON TEMİZLEYİCİ
# ----------------------------------------------------------
def fix_json(raw: str) -> str:
    """
    Model response'u string olarak gelir.
    JSON veya Python/JS literal olabilir.
    Burada sadece whitespace temizliyoruz.
    """
    if not raw:
        return raw
    return raw.strip()

# ----------------------------------------------------------
# 3) SORU ÜRETEN ANA FONKSİYON
# ----------------------------------------------------------
def generate_questions(lesson, topic, difficulty, count):

    # --- MODEL PROMPTU ---
    prompt = f"""
Sen bir 8. sınıf LGS soru üretme uzmanısın.
Görevin yalnızca belirtilen konuya TAM UYUMLU ve MEB kazanımlarına uygun sorular üretmektir.

Ders: {lesson}
Konu: {topic}
Zorluk Seviyesi: {difficulty}
Soru Sayısı: {count}

KESİNLİKLE belirtilen konu DIŞINDA soru üretme.
Üniteyle ilişkili olsa bile sadece {topic} konusuna bağlı kal.

ÇIKTI KURALLARI:
- Yalnızca saf veri yapısı üret
- Açıklama, yorum, metin EKLEME
- Markdown, ```json KULLANMA

Çıktı formatı birebir şu yapıda olmalı:

[
  {{
    "question": "Soru metni",
    "choices": ["A) ...", "B) ...", "C) ...", "D) ..."],
    "answer": "A",
    "explanation": "Detaylı çözüm"
  }}
]
"""

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "response_mime_type": "application/json",
            "temperature": 0.7,
            "maxOutputTokens": 2048
        }
    }

    headers = {
        "Content-Type": "application/json"
    }

    response = requests.post(
        GEMINI_API_URL,
        headers=headers,
        json=payload,
        timeout=60
    )

    response.raise_for_status()

    data = response.json()

    # Gemini cevabını çek
    raw_text = data["candidates"][0]["content"]["parts"][0]["text"]

    fixed = fix_json(raw_text)

    # ----------------------------------------------------------
    # 4) PARSE (JSON → olmazsa Python literal fallback)
    # ----------------------------------------------------------
    try:
        questions = json.loads(fixed)
    except json.JSONDecodeError:
        try:
            # Gemini bazen tek tırnaklı Python/JS literal döndürüyor
            questions = ast.literal_eval(fixed)
        except Exception as e:
            raise ValueError(
                f"❌ JSON parse edilemedi (JSON + literal başarısız): {e}\n"
                f"--- RAW RESPONSE ---\n{fixed}"
            )

    # ----------------------------------------------------------
    # 5) ŞEMA DOĞRULAMA (koruyucu katman)
    # ----------------------------------------------------------
    if not isinstance(questions, list):
        raise ValueError("❌ Model çıktısı liste değil")

    for i, q in enumerate(questions):
        if not all(k in q for k in ("question", "choices", "answer", "explanation")):
            raise ValueError(f"❌ Eksik alanlar var (index {i}): {q}")

    return questions
