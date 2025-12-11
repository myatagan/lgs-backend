import google.generativeai as genai
import google.generativeai as genai
import json
import re
import google.generativeai as genai

# ✅ API key Render Environment Variable’dan alınır
API_KEY = os.getenv("AIzaSyATnlSCTCp5Iithz7KCAWNP7flpJHVkGzw")

if not API_KEY:
    raise ValueError("❌ GEMINI_API_KEY2 environment variable tanımlı değil!")

genai.configure(api_key=API_KEY)

# ==============================
# 2. MODEL SEÇ
# ==============================

model = genai.GenerativeModel("models/gemini-2.5-flash")


# ✅ Model bazen açıklama eklediği için sadece JSON kısmını ayıklayan fonksiyon
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
SADECE ve TAMAMEN aşağıdaki formatta JSON üret.

❗ KURALLAR:
- SADECE JSON üret
- Açıklama, yorum, markdown YOK
- Kod bloğu YOK
- Dizi ([ ]) formatında olacak

FORMAT:
[
  {{
    "question": "Soru metni",
    "choices": ["A) ...", "B) ...", "C) ...", "D) ..."],
    "answer": "A",
    "explanation": "Detaylı çözüm"
  }}
]

ÜRETİLECEK SORU SAYISI: {count}
DERS: {lesson}
KONU: {topic}
ZORLUK: {difficulty}
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
            print("❌ JSON parse hatası:", e)
            print(json_text)
            return {"error": "JSON parse edilemedi."}

    except Exception as e:
        print("❌ GEMINI API HATASI:", e)
        return {"error": "Gemini API hatası oluştu."}

