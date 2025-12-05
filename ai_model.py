import google.generativeai as genai
import json
import re

# ----------------------------------------------------
# 1) API KEY ENVIRONMENT VARIABLE ÜZERİNDEN ALINIYOR
# ----------------------------------------------------
import os
genai.configure(api_key=os.getenv("GEMINI_API_KEY2"))

# RAM dostu, hızlı, düşük token tüketimli model:
model = genai.GenerativeModel(
    model_name="models/gemini-2.0-flash-lite",
    generation_config={
        "temperature": 0.4,
        "max_output_tokens": 1200,   # RAM taşmasını engeller
    }
)


# ----------------------------------------------------
# 2) MODELİN ÜRETTİĞİ KARMAŞIK CEVAPTAN JSON'I AYIKLA
# ----------------------------------------------------
def extract_json(text):
    """
    Model bazen JSON dışı açıklama ekleyebilir.
    Bu fonksiyon sadece köşeli parantez içindeki gerçek JSON'u ayıklar.
    """
    match = re.search(r"(\[.*\])", text, re.DOTALL)
    if match:
        return match.group(1)
    return None


# ----------------------------------------------------
# 3) SORU ÜRETME FONKSİYONU
# ----------------------------------------------------
def generate_questions(lesson, topic, difficulty, count):

    prompt = f"""
    SEN BİR LGS SORU ÜRETİCİSİN.
    Sadece JSON çıktısı ver. Kod bloğu verme, açıklama yazma.

    AŞAĞIDAKİ FORMATTA {count} ADET SORU ÜRET:

    [
      {{
        "question": "Soru metni",
        "choices": ["A) ...", "B) ...", "C) ...", "D) ..."],
        "answer": "A",
        "explanation": "Çözüm"
      }}
    ]

    Kurallar:
    - Asla JSON dışına çıkma
    - Sorular MEB LGS formatında olsun
    - Ders: {lesson}
    - Konu: {topic}
    - Zorluk: {difficulty}
    """

    try:
        response = model.generate_content(prompt)
    except Exception as e:
        print("❌ MODEL ÇAĞRI HATASI:", e)
        return {"error": "Model çağrısı başarısız oldu."}

    raw = response.text or ""
    json_text = extract_json(raw)

    if not json_text:
        print("❌ JSON bulunamadı (ham veri):", raw[:300])
        return {"error": "Model JSON formatında cevap üretemedi."}

    try:
        parsed = json.loads(json_text)
        return parsed
    except Exception as e:
        print("❌ JSON parse hatası:", e)
        print("Gelen JSON:", json_text)
        return {"error": "JSON parse edilemedi."}
