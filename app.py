from flask import Flask, request, jsonify
from flask_cors import CORS
import os, time, uuid, threading

app = Flask(__name__)

CORS(
    app,
    resources={r"/*": {"origins": ["https://lgssorubankasi.netlify.app"]}},
    methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

# -------------------------
# In-memory job store
# -------------------------
JOBS = {}  # job_id -> {"status": "pending|done|error", "result": [...], "error": "...", "created": ts}
JOBS_LOCK = threading.Lock()
JOB_TTL_SEC = 10 * 60  # 10 dk

def _cleanup_jobs():
    now = time.time()
    with JOBS_LOCK:
        dead = [jid for jid, j in JOBS.items() if now - j["created"] > JOB_TTL_SEC]
        for jid in dead:
            del JOBS[jid]

def _run_generation(job_id: str, lesson: str, topic: str, difficulty: str, count: int):
    try:
        from ai_model import generate_questions

        qs = generate_questions(
            lesson=lesson,
            topic=topic,
            difficulty=difficulty,
            count=count
        )

        with JOBS_LOCK:
            JOBS[job_id]["status"] = "done"
            JOBS[job_id]["result"] = qs

    except Exception as e:
        app.logger.exception("LLM generation failed")
        with JOBS_LOCK:
            JOBS[job_id]["status"] = "error"
            JOBS[job_id]["error"] = str(e)

@app.get("/")
def home():
    return jsonify({"ok": True, "message": "API alive"})

@app.route("/generate", methods=["POST", "OPTIONS"])
def generate():
    if request.method == "OPTIONS":
        return ("", 204)

    _cleanup_jobs()

    data = request.get_json(silent=True) or {}
    lesson = (data.get("lesson") or "").strip()
    topic = (data.get("topic") or "").strip()
    difficulty = (data.get("difficulty") or "").strip()
    count_raw = data.get("count")

    try:
        count = int(count_raw)
    except Exception:
        return jsonify({"ok": False, "error": "count sayı olmalı"}), 400

    if not (lesson and topic and difficulty):
        return jsonify({"ok": False, "error": "Eksik alan"}), 400
    if count < 1:
        return jsonify({"ok": False, "error": "count en az 1"}), 400
    if count > 10:
        count = 10

    job_id = uuid.uuid4().hex
    with JOBS_LOCK:
        JOBS[job_id] = {"status": "pending", "result": None, "error": None, "created": time.time()}

    t = threading.Thread(
        target=_run_generation,
        args=(job_id, lesson, topic, difficulty, count),
        daemon=True
    )
    t.start()

    # 🔥 hemen dön: worker timeout yok
    return jsonify({"ok": True, "job_id": job_id}), 200

@app.get("/job/<job_id>")
def job_status(job_id):
    _cleanup_jobs()
    with JOBS_LOCK:
        j = JOBS.get(job_id)
        if not j:
            return jsonify({"ok": False, "error": "Job not found"}), 404

        if j["status"] == "done":
            return jsonify({"ok": True, "status": "done", "questions": j["result"]}), 200
        if j["status"] == "error":
            return jsonify({"ok": False, "status": "error", "error": j["error"]}), 200

        return jsonify({"ok": True, "status": "pending"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
