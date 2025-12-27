from flask import Flask, request, jsonify
from flask_cors import CORS
import os

from ai_model import generate_questions

app = Flask(__name__)

# CORS (Netlify domainini env ile yönetmek daha temiz)
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "https://lgssorubankasi.netlify.app").split(",")

CORS(
    app,
    resources={r"/*": {"origins": [o.strip() for o in ALLOWED_ORIGINS]}},
    supports_credentials=False,
    methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"]
)

# -------------------------
# Küçük yardımcılar
# -------------------------
def _as_int(value, default=None):
    """'5' gibi stringleri güvenle int'e çevirir."""
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

def _bad_request(msg):
    return jsonify({"ok": False, "error": msg}), 400

# -------------------------
# Sağlık kontrolü
# -------------------------
@app.get("/")
def home():
    return jsonify({"ok": True, "message": "LGS Soru Bankası API çalışıyor."})

@app.get("/favicon.ico")
def favicon():
    # Tarayıcıların otomatik isteği (404 spam olmasın)
    return ("", 204)

# -------------------------
# Asıl endpoint
# -------------------------
@app.route("/generate", methods=["POST", "OPTIONS"])
def generate():
    # CORS preflight (flask-cors çoğunu halleder ama garanti olsun)
    if request.method == "OPTIONS":
        return ("", 204)

    data = request.get_json(silent=True) or {}

    lesson = (data.get("lesson") or "").strip()
    topic = (data.get("topic") or "").strip()
    difficulty = (data.get("difficulty") or "").strip()
    count = _as_int(data.get("count"), default=None)

    # Zorunlu alan kontrolleri
    if not lesson:
        return _bad_request("lesson alanı zorunlu.")
    if not topic:
        return _bad_request("topic alanı zorunlu.")
    if not difficulty:
        return _bad_request("difficulty alanı zorunlu.")
    if count is None:
        return _bad_request("count alanı sayı olmalı (örn: 5).")

    # Güvenlik/performans sınırları
    # (Render free/mini planlarda RAM/CPU kısıtlı → limit şart)
    if count < 1:
        return _bad_request("count en az 1 olmalı.")
    if count > 10:
        # Çok soru aynı anda model çağrısı demek; 10 üstünü kesiyoruz
        count = 10

    try:
        questions = generate_questions(
            lesson=lesson,
            topic=topic,
            difficulty=difficulty,
            count=count
        )
        return jsonify({"ok": True, "questions": questions})

    except Exception as e:
        # Yanıltıcı “VERİ TABANI” vs. yok. Gerçek hata.
        app.logger.exception("Generate error")
        return jsonify({"ok": False, "error": str(e)}), 500


if __name__ == "__main__":
    # Local test
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
