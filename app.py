from flask import Flask, request, jsonify
from flask_cors import CORS
import time
import logging

app = Flask(__name__)

# 🔥 LOGLARI GÖR
logging.basicConfig(level=logging.INFO)

# 🔥 CORS — SADECE NETLIFY DOMAIN
CORS(
    app,
    resources={r"/*": {"origins": ["https://lgssorubankasi.netlify.app"]}},
    supports_credentials=False
)

# -----------------------------
# RATE LIMIT
# -----------------------------
LAST_CALL = 0
MIN_INTERVAL = 5  # saniye

def rate_limited():
    global LAST_CALL
    now = time.time()
    if now - LAST_CALL < MIN_INTERVAL:
        return True
    LAST_CALL = now
    return False


# -----------------------------
# HEALTH
# -----------------------------
@app.route("/", methods=["GET"])
def home():
    return jsonify({"ok": True})


# -----------------------------
# GENERATE
# -----------------------------
@app.route("/generate", methods=["POST", "OPTIONS"])
def generate():
    # 🔥 OPTIONS mutlaka dönmeli
    if request.method == "OPTIONS":
        return ("", 204)

    try:
        if rate_limited():
            return jsonify({
                "ok": False,
                "error": "Çok hızlı istek. Lütfen birkaç saniye bekleyin."
            }), 429

        data = request.get_json(silent=True) or {}

        lesson = data.get("lesson")
        topic = data.get("topic")
        difficulty = data.get("difficulty")
        count = data.get("count")

        if not all([lesson, topic, difficulty, count]):
            return jsonify({
                "ok": False,
                "error": "Eksik alan"
            }), 400

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
        }), 200

    except Exception as e:
        # 🔥 ASLA crash etme
        app.logger.exception("🔥 Generate error")

        return jsonify({
            "ok": False,
            "error": str(e),
            "questions": []
        }), 200  # <-- ÖNEMLİ
