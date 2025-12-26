import os
import json
import requests

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
# 2) JSON TAMİR EDİCİ FONKSİYON
# ----------------------------------------------------------
def fix_json(raw):
    """Gemini'nın bozuk JSON çıktısını otomatik düzeltir."""

    if not raw:
        return raw

    # Kod bloğu işaretlerini temizle
    raw = raw.replace("```json", "").replace("```", "").strip()

    # UTF-8 BOM temizliği
    raw = raw.encode("utf-8").decode("utf-8-sig")

    # Tek tırnakları çift tırnağa çevir
    raw = raw.replace("'", '"')

    # JSON dizi kapanışı eksikse ekle
    if raw.startswith("[") and not raw.endswith("]"):
        raw += "]"

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
- Yalnızca saf JSON üret
- Açıklama, yorum, metin EKLEME
- Markdown, ```json KULLANMA

JSON formatı TAM OLARAK şu yapıda olmalıdır:

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
        ]
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

    # JSON'u düzelt
    fixed = fix_json(raw_text)

    # Parse et
    try:
        questions = json.loads(fixed)
    except json.JSONDecodeError:
        raise ValueError(f"❌ JSON parse edilemedi:\n{fixed}")

    return questions
