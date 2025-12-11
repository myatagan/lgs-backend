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

    # UTF-8 BOM karakterlerini temizle
    raw = raw.encode("utf-8").decode("utf-8-sig")

    # Tek tırnakları çift tırnağa çevir (JSON uyumluluğu için)
    raw = raw.replace("'", '"')

    # Eğer JSON dizi başlıyor ama kapanmıyorsa tamir et
    if raw.startswith("[") and not raw.endswith("]"):
        raw += "]"

    # Fazla boşlukları temizle
    raw = raw.strip()

    return raw


# ----------------------------------------------------------
# 3) SORU ÜRETEN ANA FONKSİYON
# ----------------------------------------------------------
def generate_questions(lesson, topic, difficulty, count):

    # --- MODEL PROMPTU ---
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
    - Sadece saf JSON ür
