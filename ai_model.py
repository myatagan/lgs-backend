import os
import json
import requests
import ast

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
# 2) JSON TEMİZLEYİCİ
# ----------------------------------------------------------
def fix_json(raw: str) -> str:
    """
    Model response'u string olarak gelir.
    JSON veya Python/JS literal olabilir.
    Burada sadece whitespace temizliyoruz.
    """
    if not raw:
        return raw
    return raw.strip()

# ----------------------------------------------------------
# 3) SORU ÜRETEN ANA FONKSİYON (RETRY'Lİ)
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

ÇIKTI KURALLARI (KRİTİK):
- Yalnızca saf veri yapısı üret
- Açıklama, yorum, metin EKLEME
- Markdown, ```json KULLANMA
- Metinlerde çift tırnak (") KULLANMA
- Satır sonu karakteri (\\n) KULLANMA
- Tüm metinler TEK SATIR olmalı

Çıktı formatı birebir şu yapıda olmalı:

[
  {{
    "question": "Soru metni",
    "choices": ["A) ...", "B) ...", "C) ...", "D) ..."],
    "answer": "A",
    "explanation": "Detayli cozum"
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
        ],
        "generationConfig": {
            "response_mime_type": "application/json",
            "temperature": 0.4,      # 🔥 düşürüldü
            "topP": 0.8,
            "maxOutputTokens": 1500  # 🔥 kısıtlandı
        }
    }

    headers = {
        "Content-Type": "application/json"
    }

    # ----------------------------------------------------------
    # 4) RETRY MEKANİZMASI (3 DENEME)
    # ----------------------------------------------------------
    last_error = None

    for attempt in range(1, 4):
        try:
            response = requests.post(
                GEMINI_API_URL,
                headers=headers,
                json=payload,
                timeout=60
            )

            response.raise_for_status()
            data = response.json()

            raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
            fixed = fix_json(raw_text)

            # Önce JSON dene
            try:
                questions = json.loads(fixed)
            except json.JSONDecodeError:
                # Olmazsa Python/JS literal dene
                questions = ast.literal_eval(fixed)

            # ----------------------------------------------------------
            # 5) ŞEMA DOĞRULAMA
            # ----------------------------------------------------------
            if not isinstance(questions, list):
                raise ValueError("Model çıktısı liste değil")

            for i, q in enumerate(questions):
                if not all(k in q for k in ("question", "choices", "answer", "explanation")):
                    raise ValueError(f"Eksik alanlar var (index {i})")

            return questions  # ✅ BAŞARILI

        except Exception as e:
            last_error = e
            continue  # bir sonraki denemeye geç

    # ----------------------------------------------------------
    # 6) 3 DENEME DE BAŞARISIZ
    # ----------------------------------------------------------
    raise ValueError(
        f"❌ Model 3 denemede de geçerli çıktı üretemedi.\n"
        f"Son hata: {last_error}"
    )
