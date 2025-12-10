import google.generativeai as genai
import json
import re
import os

<<<<<<< HEAD
# ==============================
# 1. ENV'DEN API KEY OKU
# ==============================

=======
# ✅ API key Render Environment Variable’dan alınır
>>>>>>> 268ea07425ac331a34efae388259794914748e9d
API_KEY = os.getenv("GEMINI_API_KEY2")

if not API_KEY:
    raise ValueError("❌ GEMINI_API_KEY2 environment variable tanımlı değil!")

genai.configure(api_key=API_KEY)

# ==============================
# 2. MODEL SEÇ
# ==============================

model = genai.GenerativeModel("models/gemini-2.5-flash")


# ==============================
# 3. JSON AYIKLAYICI
# ==============================

def extract_json(text):
    """
    Model JSON dışı açıklama eklerse sadece gerçek JSON kısmını ayıklar.
    """
    match = re.search(r"(\[.*\])", text, re.DOTALL)
    if match:
        return match.group(1)
    return None


# ==============================
# 4. SORU ÜRETİCİ
# ==============================

def generate_questions(lesson, topic, difficulty, count):

    prompt = f"""
SADECE aşağıdaki formatta JSON üret.
AÇIKLAMA EKLEME.
KOD BLOĞU KULLANMA.

[
  {{
    "question": "Soru",
    "choices": ["A) ...", "B) ...", "C) ...", "D) ..."],
    "answer": "A",
    "explanation": "Detaylı çözüm"
  }}
]

Ders: {lesson}
Konu: {topic}
Zorluk: {difficulty}
Soru Sayısı: {count}
"""

    response = model.generate_content(prompt)
    raw_text = response.text.strip()

    json_text = extract_json(raw_text)

    if not json_text:
        print("❌ JSON bulunamadı:")
        print(raw_text)
        return {"error": "Model JSON üretemedi"}

    try:
        data = json.loads(json_text)
        return data
    except Exception as e:
<<<<<<< HEAD
        print("❌ JSON parse hatası:", e)
        print(json_text)
        return {"error": "Model JSON formatında cevap döndüremedi"}
=======
        print("❌ GEMINI API HATASI:", e)
        return {"error": "Gemini API hatası oluştu."}


>>>>>>> 268ea07425ac331a34efae388259794914748e9d
