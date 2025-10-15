import openai
import json
import config

openai.api_key = config.OPENAI_API_KEY

TERMS_OF_SERVICE = (
    "📋 תנאי שירות:\n"
    "1. כל החולצות מקוריות וחדשות בלבד.\n"
    "2. הזמנות ותשלומים מתבצעים אך ורק דרך האתר הרשמי — לא דרך וואטסאפ.\n"
    "3. ניתן להחזיר חולצה תוך 14 יום כל עוד היא במצב חדש ולא נעשה בה שימוש.\n"
    "4. זמינות המידות והדגמים משתנה לפי מלאי.\n"
    "5. השירות כאן נועד לשאלות כלליות, בירורים ותמיכה לאחר רכישה בלבד."
)

def is_valid_json(s: str) -> bool:
    try:
        json.loads(s)
        return True
    except Exception:
        return False

def trim_history(history: str, limit: int = 10) -> str:
    """
    שומר רק את N ההודעות האחרונות מהיסטוריית השיחות כדי לחסוך מקום.
    """
    if not history:
        return ""
    lines = [line.strip() for line in history.split("\n") if line.strip()]
    if len(lines) > limit:
        lines = lines[-limit:]
    return "\n".join(lines)

def user_text_to_message(user_phone: str, user_text: str, history: str = "") -> dict:
    """
    שולח את הודעת המשתמש ל-GPT, כולל היסטוריית שיחות מצומצמת ותנאי השירות.
    """
    short_history = trim_history(history)

    system_message = (
        "אתה נציג שירות לקוחות בחנות חולצות כדורגל בשם 'Football Shirts'.\n"
        "תשובותיך צריכות להיות מנומסות, טבעיות וברורות בעברית בלבד.\n"
        "אין לבצע מכירות, אלא רק מתן מידע, סיוע כללי ותמיכה לאחר רכישה.\n"
        "הקפד תמיד להיות ידידותי, קצר ולעניין.\n"
        "החזר תמיד JSON בלבד בפורמט:\n"
        "{\"text_to_send\": \"...\"}"
    )

    user_prompt = (
        f"היסטוריית השיחות הקודמות (תמצית):\n{short_history}\n\n"
        f"הודעה חדשה מהלקוח:\n{user_text}\n\n"
        f"תנאי השירות של החברה:\n{TERMS_OF_SERVICE}"
    )

    try:
        response = openai.chat.completions.create(
            model=config.MODEL,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_prompt}
            ]
        )
        content = response.choices[0].message.content.strip()
    except Exception as e:
        print("OpenAI error:", e)
        return {"text_to_send": "מצטערים, יש כרגע בעיה זמנית. נסה שוב מאוחר יותר 🙏"}

    if is_valid_json(content):
        return json.loads(content)
    else:
        return {"text_to_send": content or "מצטערים, לא הצלחתי להבין את הבקשה."}
