from flask import Flask, request, jsonify
from flask_cors import CORS
import time
import requests

app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "*"}})

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
    return jsonify({"ok": True})


@app.route("/generate", methods=["POST", "OPTIONS"])
def generate():
    if request.method == "OPTIONS":
        return ("", 204)

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
        })

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            return jsonify({
                "ok": False,
                "error": "AI rate limit aşıldı. Lütfen bekleyin."
            }), 429
        raise

    except Exception as e:
        # 🔥 BU SATIR SAYESİNDE ARTIK RENDER LOG BOŞ KALMAZ
        app.logger.exception("🔥 Generate endpoint error")

        # 🔥 500 YERİNE KONTROLLÜ BAŞARISIZLIK
        return jsonify({
            "ok": False,
            "error": str(e),
            "questions": []
        }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
