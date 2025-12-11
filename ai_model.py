import google.generativeai as genai
import os
import json

# API KEY'i Render Environment Variables üzerinden alıyoruz
API_KEY = os.getenv("GEMINI_API_KEY2")
if not API_KEY:
    raise ValueError("❌ GEMINI_API_KEY2 environment variable tanımlı değil!")

genai.configure(api_key=API_KEY)

# JSON çıkışı zorlayan model ayarı
model = genai.GenerativeModel(
    "models/gemini-2.5-flash",
    generation_config={
        "response_mime_type": "application/json"
    }
)

def generate_questions(lesson, topic, difficulty, count):

    prompt = {
        "lesson": lesson,
        "topic": topic,
        "difficulty": difficulty,
        "count": count,
        "instructions": """
        Lütfen aşağıdaki JSON formatına TAM UYUMLU sorular üret:

        [
          {
            "question": "Soru metni",
            "choices": ["A) ...", "B) ...", "C) ...", "D) ..."],
            "answer": "A",
            "explanation": "Detaylı çözüm"
          }
        ]

        - Kesinlikle metin açıklaması ekleme
        - Kod bloğu ekleme
        - JSON dışında tek bir karakter bile yazma
        - Tüm sorular 4 şıklı olsun
        """
    }

    try:
        response = model.generate_content(prompt)
        result = json.loads(response.text)
        return result

    except Exception as e:
        print("❌ JSON üretim hatası:", e)
        return {"error": "Model düzgün JSON üretmedi."}
