from flask import Flask, request, jsonify
from flask_cors import CORS
import time
import requests

app = Flask(__name__)

# ✅ CORS – Netlify için açık
CORS(app, resources={r"/*": {"origins": "*"}})

# -----------------------------
# Rate limit (backend tarafı)
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


@app.get("/")
def home():
    return jsonify({"ok": True, "message": "LGS API running"})


@app.route("/generate", methods=["POST", "OPTIONS"])
def generate():
    if request.method == "OPTIONS":
        return ("", 204)

    if rate_limited():
        return jsonify({
            "ok": False,
            "error": "Çok hızlı istek. Lütfen birkaç saniye bekleyin.",
            "retryable": True,
            "questions": []
        }), 200

    data = request.get_json(silent=True) or {}

    lesson = data.get("lesson")
    topic = data.get("topic")
    difficulty = data.get("difficulty")
    count = data.get("count")

    if not all([lesson, topic, difficulty, count]):
        return jsonify({
            "ok": False,
            "error": "Eksik alan",
            "questions": []
        }), 200

    try:
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

    # 🔥 Gemini 429 / 503 YUMUŞATMA
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code in (429, 503):
            app.logger.warning("AI temporary unavailable")
            return jsonify({
                "ok": False,
                "retryable": True,
                "error": "AI servis geçici olarak yoğun. 1-2 dakika sonra tekrar deneyin.",
                "questions": []
            }), 200
        raise

    except Exception as e:
        app.logger.exception("LLM generation failed")
        return jsonify({
            "ok": False,
            "error": str(e),
            "questions": []
        }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
