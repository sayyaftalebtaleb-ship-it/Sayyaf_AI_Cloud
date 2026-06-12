import telebot
import requests
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# 1. التوكين والـ API (تأكد من وضع التوكينات الخاصة بك هنا)
TELEGRAM_TOKEN = '7965345356:AAHbplcm8hEHB_cKcJRrNNnIxXtdaklPcfo' # ضع توكين تليجرام الكامل هنا
GROQ_API_KEY = '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' # ضع مفتاح جروق الكامل هنا

bot = telebot.TeleBot(TELEGRAM_TOKEN)
DB_FILE = 'chat_histories.json'

def load_histories():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_histories():
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(chat_histories, f, ensure_ascii=False, indent=4)

chat_histories = load_histories()

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = str(message.chat.id)
    user_text = message.text
    
    try:
        bot.send_chat_action(user_id, 'typing')
    except:
        pass
        
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # التوجيهات الأصلية مضافاً إليها فقرة جودة الكتابة التي طلبتها
    system_instruction = (
        "أنت مساعد ذكي وودود اسمك 'Sayyaf AI' (سياف AI). تم تطويرك بواسطة المبرمج اليمني سياف طالب (Sayyaf Taleb).\n\n"
        "[الهوية]\n"
        "- عند سؤالك بشكل مباشر عن اسمك, أو من طورك، أو من صنعك: أجب بوضوح بأنك 'Sayyaf AI' وأن مطورك هو 'سياف طالب'.\n"
        "- في أي سياق آخر: لا تذكر اسمك أو اسم مطورك تلقائيًا.\n\n"
        "[سياسة اللغة]\n"
        "1. التزم بلغة المستخدم.\n"
        "2. الشرح بالعربية والمصطلحات التقنية أو الأمثلة الإنجليزية تترك كما هي دون ترجمة تكرارية.\n\n"
        "[جودة الكتابة]\n"
        "- لا تستخدم كلمات مخترعة أو رموزًا غير مفهومة.\n"
        "- إذا لم تكن متأكدًا من كلمة ما فأعد صياغة الجملة.\n"
        "- راجع الرد قبل إرساله وتأكد أنه طبيعي ومفهوم."
    )
    
    if user_id not in chat_histories:
        chat_histories[user_id] = [{"role": "system", "content": system_instruction}]
    else:
        # لتحديث التوجيهات في الذاكرة الحالية للمستخدمين
        chat_histories[user_id][0] = {"role": "system", "content": system_instruction}
        
    chat_histories[user_id].append({"role": "user", "content": user_text})
    
    if len(chat_histories[user_id]) > 31:
        chat_histories[user_id] = [chat_histories[user_id][0]] + chat_histories[user_id][-30:]
    
    payload = {
        "model": "llama-3.3-70b-versatile", 
        "messages": chat_histories[user_id]
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            result = response.json()
            reply_text = result['choices'][0]['message']['content']
            chat_histories[user_id].append({"role": "assistant", "content": reply_text})
            save_histories()
            bot.reply_to(message, reply_text)
        else:
            bot.reply_to(message, "حدث خطأ مؤقت في السيرفر.")
    except Exception as e:
        bot.reply_to(message, "حدث خطأ أثناء الاتصال بالسيرفر.")

# سيرفر ويب وهمي لكي يقبل موقع Render تشغيل البوت مجاناً 100%
class WebServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Sayyaf AI is Running Successfully!")

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), WebServerHandler)
    print(f"Web Server started on port {port}")
    server.serve_forever()

if __name__ == "__main__":
    # تشغيل سيرفر الويب في خلفية منفصلة
    threading.Thread(target=run_web_server, daemon=True).start()
    
    print("البوت يعمل الآن سحابياً وبشكل مجاني تماماً...")
    bot.infinity_polling()
        
