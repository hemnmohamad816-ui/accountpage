import os
import shutil
import uuid
from threading import Thread
from flask import Flask
import telebot
from telebot import types
import yt_dlp

# --- دروستکردنی وێب سێرڤەر بۆ Render (Free Web Service) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is active 24/7!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web_server)
    t.start()

keep_alive()
# -----------------------------------------------------------

BOT_TOKEN = "8965991710:AAHUK2VwSefBARzBzrbmpMUB9yswn9xExi4"
CHANNEL_USERNAME = "@hararash1"
CHANNEL_LINK = "https://t.me/hararash1"

bot = telebot.TeleBot(BOT_TOKEN)

MESSAGES = {
    'ku': {
        'welcome': "سڵاو! 👋\nتکایە بۆ بەکارهێنانی بۆتەکە سەرەتا پێویستە جۆینی گروپەکەمان بکەیت:\n\n{link}",
        'not_joined': "❌ هێشتا جۆینی گروپەکەمانت نەکردووە! تکایە سەرەتا جۆین بکە پاشان کلیک لەسەر 'جۆینم کرد' بکەرەوە.",
        'joined': "✅ سوپاس بۆ جۆینکردنت!\nئێستا دەتوانیت لینکی ڤیدیۆ یان وێنە بنێریت تا بۆت داوبەزێنم (TikTok, Instagram, Pinterest, Snapchat...).",
        'btn_join': "📢 جۆینی گروپ بکە",
        'btn_check': "✅ جۆینم کرد",
        'btn_lang': "🌐 Language / زمان",
        'downloading': "کەمێک چاوەڕێ بکە... لە حاڵەتی داولۆندکردندایە ⏳",
        'err_link': "⚠️ تکایە لینکێکی ڕاست و دروست بنێرە!",
        'err_info': "❌ نەتوانرا زانیاری لەم لینکەوە دەرهێنرێت. دڵنیابەوە لەوەی پۆستەکە گشتییە (Public).",
        'err_none': "❌ هیچ فایلێک نەدۆزرایەوە یان داولۆند نەبوو.",
        'err_size': "⚠️ قەبارەی فایلەکە لە 50MB گەورەترە و تیلیگرام ڕێگەی نادات بنێردرێت.",
        'select_lang': "تکایە زمانێک هەڵبژێرە / Please select a language / الرجاء اختيار اللغة:"
    },
    'en': {
        'welcome': "Hello! 👋\nPlease join our group first to use the bot:\n\n{link}",
        'not_joined': "❌ You haven't joined the group yet! Please join first then click 'I Joined'.",
        'joined': "✅ Thank you for joining!\nNow send any video or photo link to download (TikTok, Instagram, Pinterest, Snapchat...).",
        'btn_join': "📢 Join Group",
        'btn_check': "✅ I Joined",
        'btn_lang': "🌐 Language / زمان",
        'downloading': "Please wait... Downloading ⏳",
        'err_link': "⚠️ Please send a valid link!",
        'err_info': "❌ Couldn't fetch media. Make sure the post is public.",
        'err_none': "❌ No files found or downloaded.",
        'err_size': "⚠️ File size exceeds Telegram's 50MB limit.",
        'select_lang': "Please select a language:"
    },
    'ar': {
        'welcome': "أهلاً بك! 👋\nيرجى الانضمام إلى مجموعتنا أولاً لاستخدام البوت:\n\n{link}",
        'not_joined': "❌ لم تقم بالانضمام إلى المجموعة بعد! يرجى الانضمام أولاً ثم الضغط على 'تم الانضمام'.",
        'joined': "✅ شكراً لانضمامك!\nالآن أرسل أي رابط فيديو أو صورة للتحميل (TikTok, Instagram, Pinterest, Snapchat...).",
        'btn_join': "📢 الانضمام للمجموعة",
        'btn_check': "✅ تم الانضمام",
        'btn_lang': "🌐 Language / زمان",
        'downloading': "انتظر قليلاً... جاري التحميل ⏳",
        'err_link': "⚠️ يرجى إرسال رابط صحيح!",
        'err_info': "❌ متعذر جلب المحتوى. تأكد من أن المنشور عام.",
        'err_none': "❌ لم يتم العثور على أي ملف.",
        'err_size': "⚠️ حجم الملف يتجاوز الحد المسموح 50MB.",
        'select_lang': "الرجاء اختيار اللغة:"
    }
}

user_languages = {}

class QuietLogger:
    def debug(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): print(f"yt-dlp error: {msg}")

def get_lang(user_id):
    return user_languages.get(user_id, 'ku')

def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['creator', 'administrator', 'member']
    except Exception as e:
        print(f"Subscription check error: {e}")
        return False

def make_sub_keyboard(lang):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_join = types.InlineKeyboardButton(text=MESSAGES[lang]['btn_join'], url=CHANNEL_LINK)
    btn_check = types.InlineKeyboardButton(text=MESSAGES[lang]['btn_check'], callback_data="check_sub")
    btn_lang = types.InlineKeyboardButton(text=MESSAGES[lang]['btn_lang'], callback_data="change_lang")
    markup.add(btn_join)
    markup.add(btn_check)
    markup.add(btn_lang)
    return markup

def make_lang_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=3)
    btn_ku = types.InlineKeyboardButton(text="کوردی ☀️", callback_data="setlang_ku")
    btn_en = types.InlineKeyboardButton(text="English 🇬🇧", callback_data="setlang_en")
    btn_ar = types.InlineKeyboardButton(text="العربية 🇸🇦", callback_data="setlang_ar")
    markup.add(btn_ku, btn_en, btn_ar)
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    lang = get_lang(user_id)

    if is_subscribed(user_id):
        bot.reply_to(message, MESSAGES[lang]['joined'], reply_markup=make_sub_keyboard(lang))
    else:
        text = MESSAGES[lang]['welcome'].format(link=CHANNEL_LINK)
        bot.reply_to(message, text, reply_markup=make_sub_keyboard(lang))

@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    user_id = call.from_user.id
    lang = get_lang(user_id)

    if call.data == "check_sub":
        if is_subscribed(user_id):
            bot.answer_callback_query(call.id, "✅")
            bot.edit_message_text(MESSAGES[lang]['joined'], call.message.chat.id, call.message.message_id, reply_markup=make_sub_keyboard(lang))
        else:
            bot.answer_callback_query(call.id, "❌", show_alert=True)
            text = MESSAGES[lang]['not_joined'] + f"\n\n{CHANNEL_LINK}"
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=make_sub_keyboard(lang))

    elif call.data == "change_lang":
        bot.edit_message_text(MESSAGES[lang]['select_lang'], call.message.chat.id, call.message.message_id, reply_markup=make_lang_keyboard())

    elif call.data.startswith("setlang_"):
        new_lang = call.data.split("_")[1]
        user_languages[user_id] = new_lang
        bot.answer_callback_query(call.id, "Done!")

        if is_subscribed(user_id):
            bot.edit_message_text(MESSAGES[new_lang]['joined'], call.message.chat.id, call.message.message_id, reply_markup=make_sub_keyboard(new_lang))
        else:
            text = MESSAGES[new_lang]['welcome'].format(link=CHANNEL_LINK)
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=make_sub_keyboard(new_lang))

@bot.message_handler(func=lambda message: True)
def process_link(message):
    user_id = message.from_user.id
    lang = get_lang(user_id)

    if not is_subscribed(user_id):
        text = MESSAGES[lang]['not_joined'] + f"\n\n{CHANNEL_LINK}"
        bot.reply_to(message, text, reply_markup=make_sub_keyboard(lang))
        return

    url = message.text.strip()
    if not url.startswith(("http://", "https://")):
        bot.reply_to(message, MESSAGES[lang]['err_link'])
        return

    status_msg = bot.reply_to(message, MESSAGES[lang]['downloading'])

    req_id = str(uuid.uuid4())
    task_dir = os.path.join("downloads", req_id)
    os.makedirs(task_dir, exist_ok=True)

    ydl_opts = {
        'format': 'b/best',
        'outtmpl': os.path.join(task_dir, '%(id)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
        'noprogress': True,
        'logger': QuietLogger(),
        'restrictfilenames': True,
        'windowsfilenames': True,
        'ignoreerrors': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                bot.edit_message_text(MESSAGES[lang]['err_info'], message.chat.id, status_msg.message_id)
                return

        downloaded_files = [os.path.join(task_dir, f) for f in os.listdir(task_dir) if os.path.isfile(os.path.join(task_dir, f))]

        if not downloaded_files:
            bot.edit_message_text(MESSAGES[lang]['err_none'], message.chat.id, status_msg.message_id)
            return

        for filepath in downloaded_files:
            file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
            if file_size_mb > 50:
                bot.send_message(message.chat.id, MESSAGES[lang]['err_size'])
                continue

            ext = filepath.lower().split('.')[-1]
            with open(filepath, 'rb') as file:
                if ext in ['mp4', 'mkv', 'mov', 'webm']:
                    bot.send_video(message.chat.id, file, caption="✨ @hararash1")
                elif ext in ['jpg', 'jpeg', 'png', 'webp']:
                    bot.send_photo(message.chat.id, file, caption="✨ @hararash1")
                else:
                    bot.send_document(message.chat.id, file, caption="✨ @hararash1")

        bot.delete_message(message.chat.id, status_msg.message_id)

    except Exception as e:
        error_text = str(e)
        bot.edit_message_text(f"❌ Error:\n`{error_text[:200]}`", message.chat.id, status_msg.message_id, parse_mode="Markdown")
    finally:
        if os.path.exists(task_dir):
            shutil.rmtree(task_dir, ignore_errors=True)

print("بۆتەکە چالاک بوو...")
bot.infinity_polling()
