import google.generativeai as genai
import json
import re
import os

# <-- ENVIRONMENT VARIABLE'DAN KEY AL!
genai.configure(api_key=os.environ.get("GEMINI_API_KEY2"))

model = genai.GenerativeModel("models/gemini-2.5-flash")



def extract_json(text):
    """
    Model bazen JSON dışı konuşmalar eklediği için
    cevap içindeki { ... } veya [ ... ] arasındaki
    gerçek JSON bölümünü ayıklar.
    """
    match = re.search(r"(\[.*\]|\{.*\})", text, re.DOTALL)
    if match:
        return match.group(1)
    return None


def generate_questions(lesson, topic, difficulty, count):

    prompt = f"""
    Lütfen TAMAMEN aşağıdaki JSON formatında cevap üret.

    Kesin kurallar:
    - Sadece JSON döndür (kod bloğu yok, açıklama yok)
    - JSON dışına hiçbir karakter ekleme
    - Sorular LISTE ([ ... ]) formatında olsun

    Format:
    [
      {{
        "question": "Soru metni",
        "choices": ["A) ...", "B) ...", "C) ...", "D) ..."],
        "answer": "A",
        "explanation": "Detaylı çözüm"
      }}
    ]

    Üretilecek soru sayısı: {count}
    Ders: {lesson}
    Konu: {topic}
    Zorluk: {difficulty}
    """

    response = model.generate_content(prompt)
    raw = response.text

    # JSON kısmını ayıkla
    json_text = extract_json(raw)

    if not json_text:
        print("❌ JSON bulunamadı:")
        print(raw)
        return {"error": "Model JSON formatında cevap döndüremedi."}

    try:
        data = json.loads(json_text)
        return data
    except:
        print("❌ JSON parse edilemedi:")
        print(json_text)
        return {"error": "Model JSON formatında cevap döndüremedi."}
