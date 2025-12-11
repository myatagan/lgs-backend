import os
import json
import requests

API_KEY = os.getenv("GEMINI_API_KEY2")
if not API_KEY:
    raise ValueError("❌ GEMINI_API_KEY2 environment variable tanımlı değil!")

GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.5-flash:generateContent?key=" + API_KEY
)

def generate_questions(lesson, topic, difficulty, count):

    prompt = f"""
    Sen bir 8. sınıf LGS soru üretme uzmanısın. Görevin yalnızca belirtilen konuya TAM UYUMLU,
    MEB kazanımlarına uygun sorular üretmektir.

    📌 Ders: {lesson}
    📌 Konu: {topic}
    📌 Zorluk: {difficulty}
    📌 Soru Sayısı: {count}

    KESİNLİKLE, belirtilen konu DIŞINDA tek bir soru bile üretme.
    Ünite veya ders ile ilişkili gibi olsa bile, sadece {topic} konusuna bağlı kal.

    Soru formatı kesinlikle şu JSON şeklinde olmalıdır:
    [
      {{
        "question": "Soru metni",
        "choices": ["A) ...", "B) ...", "C) ...", "D) ..."],
        "answer": "A",
        "explanation": "Detaylı çözüm"
      }}
    ]

    Kurallar:
    - Sadece saf JSON üret.
    - JSON dışında bir karakter bile ekleme.
    - Kod bloğu kullanma.
    - 'İşte sorular' gibi açıklama yazma.
    - Sorular LGS MEB müfredat seviyesinde olmalı.
    - Her şık mantıklı ve konuya uygun olmalı.
    - Çözüm açıklaması gerçekten konuya dayanmalı.
    - Soruları akademik, ölçme-değerlendirme mantığına uygun hazırla.

    Şimdi sadece belirtilen konuya %100 uygun {count} adet soru üret.
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
