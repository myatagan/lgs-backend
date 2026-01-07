import os
import json
import re
import time
import requests

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise RuntimeError("OPENROUTER_API_KEY tanımlı değil (Render env'e ekle).")

# OpenRouter Chat Completions endpoint
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
    # Bu header'lar opsiyonel ama önerilir
    "HTTP-Referer": "https://lgssorubankasi.netlify.app",
    "X-Title": "LGS Soru Bankasi",
}

# Ücretsiz/istikrarlı seçeneklerden biri:
# "mistralai/mistral-7b-instruct" genelde iyi çalışır.
MODEL = os.getenv("OPENROUTER_MODEL", "mistralai/mistral-7b-instruct")


def _strip_code_fences(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"^```(?:json)?\s*", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\s*```$", "", s)
    return s.strip()


def _extract_json_array(s: str) -> str:
    s = _strip_code_fences(s)
    first = s.find("[")
    last = s.rfind("]")
    if first != -1 and last != -1 and last > first:
        return s[first:last + 1].strip()
    return s


def _try_json_loads(s: str):
    s = _extract_json_array(s)

    # Akıllı tırnak düzeltmeleri
    s = s.replace("“", '"').replace("”", '"').replace("’", "'").replace("‘", "'")

    # trailing comma düzelt
    s = re.sub(r",\s*([}\]])", r"\1", s)

    return json.loads(s)


def _call_openrouter(prompt: str, temperature: float = 0.2, max_tokens: int = 1800) -> str:
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a strict generator. "
                    "You MUST output only valid JSON with no extra text."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    # Render/gunicorn timeout yememek için kısa timeout + retry
    last_err = None
    for _ in range(3):
        try:
            r = requests.post(OPENROUTER_URL, headers=HEADERS, json=payload, timeout=20)
            r.raise_for_status()
            data = r.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            last_err = e
            time.sleep(0.5)

    raise RuntimeError(f"OpenRouter çağrısı başarısız: {last_err}")


def generate_questions(lesson, topic, difficulty, count):
    count = int(count)

    prompt = f"""
You are an exam question generator for 8th grade LGS (Turkey).

Lesson: {lesson}
Topic: {topic}
Difficulty: {difficulty}
Number of questions: {count}

STRICT OUTPUT RULES:
- Output ONLY valid JSON (no markdown, no commentary).
- Output MUST be a JSON array.
- Each item MUST have these exact keys:
  - "question" (string)
  - "choices" (array of 4 strings starting with A) B) C) D))
  - "answer" (one of "A","B","C","D")
  - "explanation" (string)

EXAMPLE:
[
  {{
    "question": "....",
    "choices": ["A) ...", "B) ...", "C) ...", "D) ..."],
    "answer": "A",
    "explanation": "..."
  }}
]
"""

    # 1) üret
    raw = _call_openrouter(prompt, temperature=0.25, max_tokens=2000)

    # 2) parse
    try:
        questions = _try_json_loads(raw)
    except Exception:
        # 3) repair prompt (aynı modelle düzelt)
        repair_prompt = f"""
Fix the following content into STRICT JSON only.

Output MUST be a JSON array of objects with EXACT keys:
question (string), choices (array of 4 strings), answer ("A"-"D"), explanation (string).
No markdown. No extra text.

CONTENT:
{raw}
"""
        repaired = _call_openrouter(repair_prompt, temperature=0.0, max_tokens=2000)
        questions = _try_json_loads(repaired)

    # Şema doğrulama + temizlik
    if not isinstance(questions, list) or len(questions) == 0:
        raise ValueError("Model boş/geçersiz çıktı üretti")

    cleaned = []
    for q in questions:
        if not isinstance(q, dict):
            continue
        if not all(k in q for k in ("question", "choices", "answer", "explanation")):
            continue
        if not isinstance(q["choices"], list) or len(q["choices"]) != 4:
            continue
        if str(q["answer"]).strip() not in ("A", "B", "C", "D"):
            continue

        cleaned.append({
            "question": str(q["question"]).strip(),
            "choices": [str(c).strip() for c in q["choices"]],
            "answer": str(q["answer"]).strip(),
            "explanation": str(q["explanation"]).strip(),
        })

    if not cleaned:
        raise ValueError("Model geçerli soru üretemedi (şema dışı çıktı)")

    return cleaned[:count]
