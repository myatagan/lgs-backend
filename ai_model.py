import os
import json
import requests

API_KEY = os.getenv("GEMINI_API_KEY2")
if not API_KEY:
    raise ValueError("❌ GEMINI_API_KEY2 environment variable tanımlı değil!")

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=" + API_KEY

def generate_questions(lesson, topic, difficulty, count):

    prompt = f"""
    Lütfen aşağıdaki JSON formatına TAM UYUMLU {count} adet soru üret:

    [
      {{
        "question": "Soru metni",
        "choices": ["A) ...", "B) ...", "C) ...", "D) ..."],
        "answer": "A",
        "explanation": "Detaylı çözüm"
      }}
    ]

    - JSON dışında açıklama yazma
    - Kod bloğu kullanma
    - Ekstra metin ekleme
    - Sadece saf JSON üret
    """

    payload = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ]
    }

    try:
        response = requests.post(GEMINI_API_URL, json=payload)
        data = response.json()

        raw_output = data["candidates"][0]["content"]["parts"][0]["text"]

        return json.loads(raw_output)

    except Exception as e:
        print("❌ JSON üretim hatası:", e)
        return {"error": "Model düzgün JSON üretmedi."}
