from football_service_matcher import user_text_to_message

# מספר דמה של המשתמש
user_phone = "+972547509607"

# היסטוריה ריקה
history = ""

# הודעה לבדיקה
user_text = "שלום, אפשר לדעת מתי יהיו חולצות של ריאל מדריד?"

response = user_text_to_message(user_phone, user_text, history)
print(response['text_to_send'])
