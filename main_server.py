from flask import Flask, request, jsonify
import time
import traceback
import os
from typing import Dict, List
from football_service_matcher import user_text_to_message
from whatsApp import send_message
from config import VERIFY_TOKEN

app = Flask(__name__)

# ===============================
# שמירת היסטוריית שיחות בזיכרון
# ===============================
USER_HISTORY: Dict[str, List[str]] = {}
PROCESSED_MESSAGE_IDS: Dict[str, float] = {}
DEDUP_TTL_SECONDS = int(os.getenv("DEDUP_TTL_SECONDS", "3600"))  # שעה

def is_already_processed(msg_id: str | None) -> bool:
    if not msg_id:
        return False
    now = time.time()
    if len(PROCESSED_MESSAGE_IDS) > 1000:
        cutoff = now - DEDUP_TTL_SECONDS
        for mid in [m for m, ts in PROCESSED_MESSAGE_IDS.items() if ts < cutoff]:
            PROCESSED_MESSAGE_IDS.pop(mid, None)
    if msg_id in PROCESSED_MESSAGE_IDS:
        return True
    PROCESSED_MESSAGE_IDS[msg_id] = now
    return False

# ===============================
# אימות webhook מול Meta
# ===============================
@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Forbidden", 403

# ===============================
# קליטת הודעות חדשות מ-WhatsApp
# ===============================
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True) or {}

    msg_id, user_phone, text_body = None, None, None
    try:
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages") or []
                if messages:
                    msg = messages[0]
                    msg_id = msg.get("id")
                    user_phone = msg.get("from")
                    text_body = (msg.get("text") or {}).get("body")
                    break
            if text_body:
                break
    except Exception as e:
        print("Error parsing message:", e)
        return jsonify({"status": "parse_error"}), 200

    if not text_body or not user_phone:
        return jsonify({"status": "no_text"}), 200
    if is_already_processed(msg_id):
        return jsonify({"status": "duplicate"}), 200

    # שליפה או יצירת היסטוריה
    history = USER_HISTORY.get(user_phone, [])
    history.append(f"לקוח: {text_body}")

    try:
        response = user_text_to_message(user_phone, text_body, "\n".join(history))
    except Exception as e:
        print("GPT error:", e)
        response = {"text_to_send": "מצטערים, אירעה שגיאה זמנית."}

    text_to_send = response.get("text_to_send", "לא הצלחתי להבין 😅")
    send_message(user_phone, text_to_send)

    # עדכון ההיסטוריה
    history.append(f"נציג: {text_to_send}")
    USER_HISTORY[user_phone] = history

    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
