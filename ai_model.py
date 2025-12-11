import os
import google.generativeai as genai
import json
import re

# ✅ API KEY ENV'DEN OKUNUYOR
API_KEY = os.getenv("GEMINI_API_KEY2")

if not API_KEY:
    raise ValueError("❌ GEMINI_API_KEY2 environment variable TANIMLI DEĞİL!")

genai.configure(api_key=API_KEY)

model = genai.GenerativeModel("models/gemini-2.5-flash")

def extract_json(text):
    match = re.search(r"(\[.*\])", text, re.DOTALL)
    if match:
        return match.group(1)
    return None

def generate_questions(lesson, topic, difficulty, count):

    prompt = f"""
    SADECE JSON DÖNDÜR. AÇIKLAMA YAZMA.

    FORMAT:
    [
      {{
        "question": "Soru metni",
        "choices": ["A) ...", "B) ...", "C) ...", "D) ..."],
        "answer": "A",
        "explanation": "Detaylı çözüm"
      }}
    ]

    SORU SAYISI: {count}
    DERS: {lesson}
    KONU: {topic}
    ZORLUK: {difficulty}
    """

    response = model.generate_content(prompt)
    raw = response.text

    json_text = extract_json(raw)

    if not json_text:
        return {"error": "❌ Model JSON üretmedi"}

    try:
        return json.loads(json_text)
    except:
        return {"error": "❌ JSON parse edilemedi"}
