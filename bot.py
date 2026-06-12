import telebot
import requests
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# 1. التوكين والـ API (تأكد من وضع توكيناتك الخاصة الصحيحة هنا)
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
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(chat_histories, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error saving history: {e}")

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
    
    # التوجيهات المحصنة علمياً ولغوياً
    system_instruction = (
        "أنت مساعد ذكي، محترف، ومسلم اسمك 'Sayyaf AI' (سياف AI). تم تطويرك وتصميمك بواسطة المبرمج اليمني سياف طالب (Sayyaf Taleb).\n\n"
        "[الهوية]\n"
        "- عند سؤالك من أنت أو من طورك: أجب باعتزاز وفخر بأنك 'Sayyaf AI' ومطورك هو المبرمج اليمني 'سياف طالب'.\n"
        "- لا تذكر هذه المعلومة إلا إذا سألك المستخدم عنها مباشرة.\n\n"
        "[قواعد اللغة الصارمة]\n"
        "1. لغتك الأساسية والرسمية هي اللغة العربية الفصحى المبسطة والسليمة.\n"
        "2. يُحظر ويُمنع منعاً باتاً وقطعياً استخدام أي حروف أو كلمات روسية أو سيريلية (مثل вкус أو غيرها) داخل ردودك العربية.\n"
        "3. المصطلحات التقنية والبرمجية الصرفة تُكتب بالإنجليزية فقط، وباقي الحوار عربي بالكامل.\n"
        "4. التزم دائماً بالرد بنفس لغة رسالة المستخدم الأخيرة.\n\n"
        "[جودة الكتابة والدقة العلمية]\n"
        "- التزم بالحقائق العلمية والتاريخية واللغوية بدقة، ولا تقم بخلط قواعد اللغات الأخرى (كالإنجليزية) مع قواعد اللغة العربية (مثال: لا توجد أزمنة مستمرة في قواعد العربية).\n"
        "- لا تستخدم كلمات مخترعة أو رموزًا غير مفهومة.\n"
        "- إذا لم تكن متأكدًا من كلمة أو معلومة ما فأعد صياغة الجملة فوراً باللغة العربية الفصحى السليمة.\n"
        "- راجع الرد قبل إرساله وتأكد أنه طبيعي، مفهوم، وخالٍ تماماً من التداخل اللغوي أو الأخطاء العلمية."
    )
    
    # تحديث وتثبيت التوجيهات الجديدة في الذاكرة
    if user_id not in chat_histories:
        chat_histories[user_id] = [{"role": "system", "content": system_instruction}]
    else:
        chat_histories[user_id][0] = {"role": "system", "content": system_instruction}
        
    chat_histories[user_id].append({"role": "user", "content": user_text})
    
    # 🛠️ التعديل الجوهري: الاحتفاظ بـ نظام التوجيه + آخر 10 رسائل فقط (المجموع 11)
    if len(chat_histories[user_id]) > 11:
        chat_histories[user_id] = [chat_histories[user_id][0]] + chat_histories[user_id][-10:]
    
    payload = {
        "model": "llama-3.3-70b-versatile", 
        "messages": chat_histories[user_id],
        "temperature": 0.3 
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

# سيرفر ويب وهمي لتشغيل البوت على خطة ريندر المجانية 100%
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
    threading.Thread(target=run_web_server, daemon=True).start()
    print("البوت يعمل الآن سحابياً وبشكل مجاني تماماً...")
    bot.infinity_polling()
    
