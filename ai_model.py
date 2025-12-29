import os
import json
import re
import time
import requests

API_KEY = os.getenv("GEMINI_API_KEY3")
if not API_KEY:
    raise RuntimeError("❌ GEMINI_API_KEY2 environment variable tanımlı değil!")

GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.5-flash:generateContent?key=" + API_KEY
)

HEADERS = {"Content-Type": "application/json"}


# ---------------------------
# Low-level call
# ---------------------------
def _gemini(text: str, temperature: float = 0.2, max_tokens: int = 2048) -> str:
    payload = {
        "contents": [{"parts": [{"text": text}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
            # mime_type bazen yine sapabiliyor ama yardımcı oluyor
            "response_mime_type": "application/json",
        },
    }
    r = requests.post(GEMINI_API_URL, headers=HEADERS, json=payload, timeout=90)
    r.raise_for_status()
    data = r.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]


# ---------------------------
# Cleaning + extraction
# ---------------------------
def _strip_code_fences(s: str) -> str:
    s = s.strip()
    s = re.sub(r"^```(?:json)?\s*", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\s*```$", "", s)
    return s.strip()

def _extract_json_array(s: str) -> str:
    """
    Metin içinde JSON array arar: ilk '[' ile son ']' arasını alır.
    """
    s = _strip_code_fences(s)
    first = s.find("[")
    last = s.rfind("]")
    if first != -1 and last != -1 and last > first:
        return s[first:last+1].strip()
    return s.strip()

def _try_json_loads(s: str):
    s = _extract_json_array(s)

    # Akıllı tırnakları düzelt
    s = s.replace("“", '"').replace("”", '"').replace("’", "'").replace("‘", "'")

    # En sık görülen: trailing comma
    s = re.sub(r",\s*([}\]])", r"\1", s)

    return json.loads(s)


# ---------------------------
# Repair pass (LLM → valid JSON)
# ---------------------------
def _repair_to_strict_json(raw_text: str, lesson: str, topic: str) -> str:
    repair_prompt = f"""
You are a strict JSON fixer.

Convert the following content into STRICT JSON only.
Output MUST be a JSON array of objects with EXACT keys:
- question (string)
- choices (array of 4 strings, each starts with "A)","B)","C)","D)")
- answer (one of "A","B","C","D")
- explanation (string)

No markdown. No extra text. JSON only.

Context:
Lesson: {lesson}
Topic: {topic}

CONTENT TO FIX:
{raw_text}
"""
    return _gemini(repair_prompt, temperature=0.0, max_tokens=2048)


# ---------------------------
# Main: generate questions
# ---------------------------
def generate_questions(lesson, topic, difficulty, count):
    count = int(count)

    gen_prompt = f"""
Sen bir 8. sınıf LGS soru üretme uzmanısın.
Sadece şu konuya uygun soru üret: {topic}

Ders: {lesson}
Konu: {topic}
Zorluk: {difficulty}
Soru sayısı: {count}

ÇIKTI KURALLARI (çok önemli):
- SADECE JSON döndür.
- Markdown / açıklama / metin YOK.
- JSON bir ARRAY olacak.
- Her eleman: question, choices (4 şık), answer (A-D), explanation içerecek.

ÖRNEK FORMAT:
[
  {{
    "question": "....",
    "choices": ["A) ...", "B) ...", "C) ...", "D) ..."],
    "answer": "A",
    "explanation": "..."
  }}
]
"""

    # Toplam deneme stratejisi:
    # 1) Üret
    # 2) Parse olmazsa repair
    # 3) Olmazsa yeniden üret
    for attempt in range(4):
        raw = _gemini(gen_prompt, temperature=0.3, max_tokens=2500)

        # 1) direkt parse dene
        try:
            questions = _try_json_loads(raw)
        except Exception:
            # 2) repair dene
            try:
                repaired = _repair_to_strict_json(raw, lesson, topic)
                questions = _try_json_loads(repaired)
            except Exception:
                time.sleep(0.6)
                continue  # yeniden üret

        # Şema doğrulama
        if not isinstance(questions, list) or len(questions) == 0:
            time.sleep(0.6)
            continue

        cleaned = []
        for q in questions:
            if not isinstance(q, dict):
                continue
            if not all(k in q for k in ("question", "choices", "answer", "explanation")):
                continue
            if not isinstance(q["choices"], list) or len(q["choices"]) != 4:
                continue
            if q["answer"] not in ("A", "B", "C", "D"):
                continue
            cleaned.append({
                "question": str(q["question"]).strip(),
                "choices": [str(c).strip() for c in q["choices"]],
                "answer": str(q["answer"]).strip(),
                "explanation": str(q["explanation"]).strip(),
            })

        # count kadar değilse de kabul (istersen burada “tamamlamak için ek üretim” yapılır)
        if cleaned:
            return cleaned[:count]

        time.sleep(0.6)

    # Buraya geliyorsa: LLM + repair bile 4 turda üretemedi
    # (LLM üretme şartına sadık kalıyoruz; havuz yok.)
    raise ValueError("❌ LLM geçerli JSON üretemedi (repair dahil).")
