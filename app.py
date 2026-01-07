from flask import Flask, request, jsonify
from flask_cors import CORS
import time

app = Flask(__name__)

# ✅ CORS – Netlify demo için açık
CORS(app, resources={r"/*": {"origins": "*"}})

# -----------------------------
# Rate limit (backend)
# -----------------------------
LAST_CALL = 0
MIN_INTERVAL = 2  # ⬅️ 5 yerine 2 saniye

def rate_limited():
    global LAST_CALL
    now = time.time()
    if now - LAST_CALL < MIN_INTERVAL:
        return True
    LAST_CALL = now
    return False


@app.get("/")
def home():
    return jsonify({
        "ok": True,
        "message": "LGS Question Generator API is running"
    })


@app.route("/generate", methods=["POST", "OPTIONS"])
def generate():
    # Preflight
    if request.method == "OPTIONS":
        return ("", 204)

    if rate_limited():
        return jsonify({
            "ok": False,
            "retryable": True,
            "error": "Too many requests. Please wait a moment.",
            "questions": []
        }), 200

    data = request.get_json(silent=True) or {}

    lesson = data.get("lesson")
    topic = data.get("topic")
    difficulty = data.get("difficulty")
    count = data.get("count")

    # Basit validasyon
    if not all([lesson, topic, difficulty, count]):
        return jsonify({
            "ok": False,
            "error": "Missing required fields",
            "questions": []
        }), 200

    try:
        # 🔥 OpenRouter kullanan ai_model
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
        # 🔥 ARTIK HER HATA LOG’LANIYOR
        app.logger.exception("LLM generation failed")

        return jsonify({
            "ok": False,
            "retryable": True,
            "error": str(e),
            "questions": []
        }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
