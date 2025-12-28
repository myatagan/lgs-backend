from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import time

app = Flask(__name__)

# -------------------------------------------------
# CORS
# -------------------------------------------------
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "https://lgssorubankasi.netlify.app"
).split(",")

CORS(
    app,
    resources={r"/*": {"origins": [o.strip() for o in ALLOWED_ORIGINS]}},
    methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"]
)

# -------------------------------------------------
# Rate limit (çok basit koruma)
# -------------------------------------------------
LAST_CALL_TIME = 0
MIN_INTERVAL = 2  # saniye

def rate_limited():
    global LAST_CALL_TIME
    now = time.time()
    if now - LAST_CALL_TIME < MIN_INTERVAL:
        return True
    LAST_CALL_TIME = now
    return False

# -------------------------------------------------
# Yardımcılar
# -------------------------------------------------
def bad_request(msg):
    return jsonify({"ok": False, "error": msg}), 400

def to_int(val):
    try:
        return int(val)
    except (TypeError, ValueError):
        return None

# -------------------------------------------------
# Sağlık endpointleri
# -------------------------------------------------
@app.get("/")
def home():
    return jsonify({"ok": True, "message": "LGS Soru Bankası API çalışıyor."})

@app.get("/health")
def health():
    return jsonify({"status": "ok"})

@app.get("/favicon.ico")
def favicon():
    return ("", 204)

# -------------------------------------------------
# ANA ENDPOINT
# -------------------------------------------------
@app.route("/generate", methods=["POST", "OPTIONS"])
def generate():
    if request.method == "OPTIONS":
        return ("", 204)

    if rate_limited():
        return jsonify({
            "ok": False,
            "error": "Çok hızlı istek. Lütfen 2 saniye bekleyin."
        }), 429

    data = request.get_json(silent=True) or {}

    lesson = (data.get("lesson") or "").strip()
    topic = (data.get("topic") or "").strip()
    difficulty = (data.get("difficulty") or "").strip()
    count = to_int(data.get("count"))

    # Zorunlu alanlar
    if not lesson:
        return bad_request("lesson alanı zorunlu.")
    if not topic:
        return bad_request("topic alanı zorunlu.")
    if not difficulty:
        return bad_request("difficulty alanı zorunlu.")
    if count is None:
        return bad_request("count geçerli bir sayı olmalı.")

    if count < 1:
        return bad_request("count en az 1 olmalı.")
    if count > 10:
        count = 10

    try:
        # 🔥 Lazy import → circular kesin biter
        from ai_model import generate_questions

        questions = generate_questions(
            lesson=lesson,
            topic=topic,
            difficulty=difficulty,
            count=count
        )

        return jsonify({
            "ok": True,
            "questions": questions
        })

    except Exception as e:
        app.logger.exception("Generate error")
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=True
    )
