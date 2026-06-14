import telebot
import requests
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# 1. التوكين والـ API (تأكد من وضع توكيناتك الكاملة هنا)
TELEGRAM_TOKEN = '8749887745:AAFa3barQrVDXWJeBzbNR_qAhzVg3ne7U9c' 
GROQ_API_KEY = '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' 

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
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(chat_histories, f, ensure_ascii=False, indent=4)
    except:
        pass

chat_histories = load_histories()

# التوجيهات الثابتة لـ Groq
system_instruction = (
    "أنت مساعد ذكي وودود اسمك 'Sayyaf AI' (سياف AI). تم تطويرك بواسطة المبرمج اليمني سياف طالب (Sayyaf Taleb).\n\n"
    "[الهوية]\n"
    "- عند سؤالك بشكل مباشر عن اسمك، أو من طورك، أو من صنعك: أجب بوضوح بأنك 'Sayyaf AI' وأن مطورك هو 'سياف طالب'.\n"
    "- في أي سياق آخر: لا تذكر اسمك أو اسم مطورك تلقائيًا.\n\n"
    "[سياسة معالجة اللغات والفصل بينها]\n"
    "1. التزم بلغة المستخدم تماماً وبشكل دقيق وبنفس الحروف الأبجدية للغة المحادثة (عربي بالكامل أو إنجليزي بالكامل).\n"
    "2. يُحظر تماماً خلط القواعد اللغوية: إذا طلب المستخدم شرح قاعدة في اللغة الإنجليزية، فاشرحها له باللغة العربية الفصحى كـ 'مادة تعليمية أجنبية'، ولا تزعم أبداً أن هذه الأزمنة الإنجليزية موجودة في قواعد اللغة العربية.\n"
    "3. المصطلحات التقنية والبرمجية الصرفة وأكواد الكمبيوتر تُكتب بالإنجليزية في سياقها الصحيح دون ترجمة تكرارية.\n\n"
    "[جودة الكتابة والدقة العلمية]\n"
    "- لا تستخدم كلمات مخترعة أو رموزًا غير مفهومة.\n"
    "- يُمنع منعاً باتاً وقطعياً إدخال أو حشر أي حروف، رموز، أو كلمات صينية، روسية، أو سيريلية عشوائية داخل النصوص.\n"
    "- يُحظر تماماً كتابة، اقتراح، أو توليد أي روابط لمواقع إلكترونية أو قنوات تليجرام خارجية.\n"
    "- راجع الرد وتأكد أنه طبيعي، مفهوم، ومكتوب بلغة واحدة متناسقة خالية تماماً من الهلوسة أو التداخل اللغوي."
)

# 🛠️ التعديل الأول: معالج خاص بأمر /start لعرض اسم المستخدم تلقائياً
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = str(message.chat.id)
    user_name = message.from_user.first_name if message.from_user.first_name else "المستخدم"
    
    # تفريغ الذاكرة القديمة للمستخدم عند الضغط على start للبدء من جديد بنظافة
    chat_histories[user_id] = [{"role": "system", "content": system_instruction}]
    save_histories()
    
    welcome_text = f"مرحبا ({user_name}) كيف يمكنني مساعدتك اليوم؟"
    bot.send_message(user_id, welcome_text)

# معالج الرسائل النصية العادية
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
    
    if user_id not in chat_histories:
        chat_histories[user_id] = [{"role": "system", "content": system_instruction}]
    else:
        chat_histories[user_id][0] = {"role": "system", "content": system_instruction}
        
    chat_histories[user_id].append({"role": "user", "content": user_text})
    
    # 🛠️ التعديل الثاني: الاحتفاظ بـ system_instruction + آخر 10 رسائل فقط في الذاكرة
    if len(chat_histories[user_id]) > 11:
        chat_histories[user_id] = [chat_histories[user_id][0]] + chat_histories[user_id][-10:]
    
    payload = {
        "model": "llama-3.3-70b-versatile", 
        "messages": chat_histories[user_id],
        "temperature": 0.1
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            result = response.json()
            reply_text = result['choices'][0]['message']['content']
            chat_histories[user_id].append({"role": "assistant", "content": reply_text})
            save_histories()
            bot.send_message(user_id, reply_text, reply_to_message_id=message.message_id, disable_web_page_preview=True)
        else:
            bot.reply_to(message, "حدث خطأ مؤقت في السيرفر.")
    except:
        bot.reply_to(message, "حدث خطأ أثناء الاتصال بالسيرفر.")

class WebServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(b"Sayyaf AI is Running Successfully!")

def run_web_server():
    # Render يفرض استخدام المنفذ الممرر في متغيرات البيئة تلقائياً
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), WebServerHandler)
    print(f"Web Server started on port {port}")
    server.serve_forever()

if __name__ == "__main__":
    # تشغيل السيرفر في تفرع خلفي مستقل كـ Daemon لضمان عدم توقفه أثناء تشغيل البوت
    web_thread = threading.Thread(target=run_web_server)
    web_thread.daemon = True
    web_thread.start()
    
    print("البوت يعمل الآن سحابياً وبشكل مجاني تماماً...")
    bot.infinity_polling()
            
