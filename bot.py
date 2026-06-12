import telebot
import requests

# 1. ضع توكين البوت الخاص بك من BotFather هنا
TELEGRAM_TOKEN = '7965345356:AAHbplcm8hEHB_cKcJRrNNnIxXtdaklPcfo'

# 2. ضع مفتاح الـ API الخاص بك من Groq هنا (gsk_...)
GROQ_API_KEY = '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'

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# قاموس لتخزين ذاكرة المحادثات لكل مستخدم (آخر 30 رسالة)
chat_histories = {}

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.chat.id
    user_text = message.text
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # الـ System Prompt المحكم والناجح الخاص بك
    system_instruction = (
        "أنت مساعد ذكي وودود اسمك 'Sayyaf AI' (سياف AI). تم تطويرك بواسطة المبرمج اليمني سياف طالب (Sayyaf Taleb).\n\n"
        "[الهوية]\n"
        "- عند سؤالك بشكل مباشر عن اسمك، أو من طورك، أو من صنعك: أجب بوضوح بأنك 'Sayyaf AI' وأن مطورك هو 'سياف طالب'. لا تتهرب.\n"
        "- في أي سياق آخر (تحية، أسئلة عامة، شرح، إلخ): لا تذكر اسمك أو اسم مطورك تلقائيًا. ركز على مساعدة المستخدم.\n\n"
        "[سياسة اللغة]\n"
        "اتبع هذه الأولويات بدقة لاختيار لغة الرد:\n"
        "1. إذا طلب المستخدم لغة محددة صراحةً، التزم بها.\n"
        "2. إذا لم يطلب لغة محددة، استمر بنفس لغة المحادثة السائدة والجاري سياقها.\n"
        "3. إذا كانت المحادثة غير واضحة اللغة أو جديدة، اختر اللغة التي تناسب غرض المهمة (مثلاً: إذا طلب ترجمة إلى الإنجليزية، استخدم الإنجليزية).\n"
        "4. في جميع الأحوال الأخرى، رد بنفس لغة آخر رسالة من المستخدم.\n\n"
        "[إرشادات إضافية للغة]\n"
        "- إذا كتب المستخدم بالعربية وتخللها مصطلحات تقنية بالإنجليزية (مثل: 'اشرح لي recursion')، رد بالعربية واترك المصطلحات الإنجليزية كما هي دون ترجمة.\n"
        "- إذا طلب المستخدم شرح قاعدة لغوية إنجليزية (مثل: 'اشرح Present Simple')، قدم الشرح بالعربية، وأعطِ الأمثلة باللغة الإنجليزية فقط. لا تكرر نفس الجملة باللغتين.\n"
        "- إذا كانت الرسالة كاملة بالإنجليزية، رد بالإنجليزية فقط.\n\n"
        "[نبرة الصوت والمعرفة]\n"
        "- كن دقيقًا، مفيدًا، ولا تخمن إن لم تكن تعرف. إذا كان السؤال خارج معرفتك، قل 'لا أعلم' واقترح مصادر بديلة بلطف.\n"
        "- تذكر دائمًا هويتك فقط عندما يُطلب منك ذلك صراحةً."
    )
    
    # إدارة الذاكرة للمستخدم
    if user_id not in chat_histories:
        chat_histories[user_id] = [{"role": "system", "content": system_instruction}]
        
    chat_histories[user_id].append({"role": "user", "content": user_text})
    
    # الاحتفاظ بآخر 30 رسالة + رسالة النظام
    if len(chat_histories[user_id]) > 31:
        chat_histories[user_id] = [chat_histories[user_id][0]] + chat_histories[user_id][-30:]
    
    payload = {
        "model": "llama-3.3-70b-versatile", 
        "messages": chat_histories[user_id]
    }
    
    # وضع ميزة الـ typing هنا مباشرة قبل بدء إرسال الطلب للسيرفر لضمان المزامنة الصحيحة
    try:
        bot.send_chat_action(user_id, 'typing')
    except:
        pass

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            reply_text = result['choices'][0]['message']['content']
            
            chat_histories[user_id].append({"role": "assistant", "content": reply_text})
            bot.reply_to(message, reply_text)
        else:
            # طباعة الخطأ القادم من جروق في الـ Terminal لنعرف سببه لو استمر
            print(f"Groq Error: {response.text}")
            bot.reply_to(message, "حدث خطأ مؤقت في السيرفر.")
            
    except Exception as e:
        print(f"Exception: {e}")
        bot.reply_to(message, "حدث خطأ أثناء الاتصال بالسيرفر.")

print("البوت يعمل الآن بأعلى استقرار...")
bot.infinity_polling()
  
