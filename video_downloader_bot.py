# -*- coding: utf-8 -*-
"""
بۆتی داونلۆدی ڤیدیۆ - TikTok / Instagram / Pinterest
دروستکراوە بۆ کارکردن لەسەر Pydroid 3 (ئەندرۆید)

پێش کارپێکردن، ئەم پاکیجانە دابمەزرێنە لە Pydroid (لە Pip دیالۆگی ناو ئەپەکە):
    pip install pyTelegramBotAPI yt-dlp

دوای ئەوە، لە خوارەوە لە شوێنی "PUT_YOUR_BOT_TOKEN_HERE" تۆکنی بۆتەکەت دابنێ
کە لە @BotFather وەریدەگریت.
"""

import os
import re
import time
import threading
import traceback
import concurrent.futures

import telebot
from telebot import types
import yt_dlp

# =========================
# ڕێکخستنی بنەڕەتی
# =========================
BOT_TOKEN = "8965991710:AAGyMAQPTA6wgbkD1RenAx4tjPxoptW_OU8"  # تۆکنی بۆتەکەت
DOWNLOAD_DIR = "downloads"
MAX_TELEGRAM_SIZE_MB = 50  # سنووری ناردنی فایل بە ڕاستەوخۆ لە بۆتدا

DOWNLOAD_TIMEOUT_SEC = 120  # ماوەی زۆرترین چاوەڕوانی بۆ داگرتنی ڤیدیۆیەک

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# num_threads زۆرکراوە بۆ ئەوەی چەند بەکارهێنەر بەیەکەوە بتوانن بەخزمەت بکرێن
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML", threaded=True, num_threads=8)

# هەڵگرتنی زمانی هەر بەکارهێنەرێک لە کاتی کاتی مانا (memory)
user_lang = {}  # {user_id: "ku_sorani" | "ku_badini" | "en" | "tr" | "ru" | "fr"}

# =========================
# دەقەکان بە هەموو زمانەکان
# =========================
TEXTS = {
    "ku_sorani": {
        "choose_lang": "تکایە زمانەکەت هەڵبژێرە 👇",
        "welcome": (
            "🎬 <b>بەخێربێیت بۆ بۆتی داونلۆدی ڤیدیۆ</b>\n\n"
            "لینکی ڤیدیۆیەکت لە TikTok، Instagram یان Pinterest بنێرە،\n"
            "من بە باشترین کوالیتی و بەبێ لۆگۆ بۆت دەینێرمەوە.\n\n"
            "بۆ گۆڕینی زمان: /language بنووسە"
        ),
        "send_link": "🔗 تکایە لینکی ڤیدیۆیەکە بنێرە (TikTok / Instagram / Pinterest)",
        "invalid_link": "⚠️ ئەم لینکە پشتگیری ناکرێت. تکایە لینکێکی دروستی TikTok، Instagram یان Pinterest بنێرە.",
        "downloading": "⏳ چاوەڕێبە... ڤیدیۆکە داونلۆد دەکرێت",
        "uploading": "📤 ناردنی ڤیدیۆکە بۆ تێلگرام...",
        "success": "✅ کوالیتی بەرزی، بەبێ واتەرمارک!",
        "too_big": "⚠️ ئەم فایلە زۆر گەورەیە بۆ ناردن لە تێلگرام ({size} MB). تکایە ڤیدیۆیەکی دیکە تاقی بکەرەوە.",
        "error": "❌ هەڵەیەک ڕوویدا لە کاتی داونلۆدکردن. تکایە دووبارە هەوڵبدەوە یان لینکێکی دیکە تاقی بکەرەوە.",
        "lang_set": "✅ زمان گۆڕدرا بۆ کوردی سۆرانی",
    },
    "ku_badini": {
        "choose_lang": "ژ کەرەمێ خۆ زمانێ خۆ هەلبژێرە 👇",
        "welcome": (
            "🎬 <b>بەخێرهاتنە بۆتێ داگرتنا ڤیدیۆیان</b>\n\n"
            "لینکێ ڤیدیۆیەکێ خۆ ژ TikTok، Instagram یان Pinterest بنێرە،\n"
            "ئەز دێ ب باشترین کوالیتی و بێ لۆگۆ ب تە بدەم زانین.\n\n"
            "بۆ گۆهۆرینا زمانی: /language binivîse"
        ),
        "send_link": "🔗 ژ کەرەمێ خۆ لینکێ ڤیدیۆیێ بنێرە (TikTok / Instagram / Pinterest)",
        "invalid_link": "⚠️ ئەڤ لینکە ناهێتە پشتگیریکرن. لینکەکا دروست ژ TikTok، Instagram یان Pinterest بنێرە.",
        "downloading": "⏳ چاڤەڕێ بە... ڤیدیۆ دهێتە داگرتن",
        "uploading": "📤 ناردنا ڤیدیۆیێ بۆ تێلگرام...",
        "success": "✅ کوالیتیەکا بلند، بێ واتەرمارک!",
        "too_big": "⚠️ ئەڤ فایلە پتر مەزنە ژ بۆ ناردنێ ({size} MB). ژ کەرەمێ خۆ ڤیدیۆیەکا دن تاقی بکە.",
        "error": "❌ خەلەتیەک چێبوو. ژ کەرەمێ خۆ دووبارە هەول بدە.",
        "lang_set": "✅ زمان هاتە گۆهۆرین بۆ کرمانجی (بادینی)",
    },
    "en": {
        "choose_lang": "Please choose your language 👇",
        "welcome": (
            "🎬 <b>Welcome to the Video Downloader Bot</b>\n\n"
            "Send a link from TikTok, Instagram or Pinterest,\n"
            "and I'll send it back in the best quality, watermark-free.\n\n"
            "To change language: /language"
        ),
        "send_link": "🔗 Please send a video link (TikTok / Instagram / Pinterest)",
        "invalid_link": "⚠️ This link isn't supported. Please send a valid TikTok, Instagram, or Pinterest link.",
        "downloading": "⏳ Please wait... downloading your video",
        "uploading": "📤 Uploading video to Telegram...",
        "success": "✅ High quality, no watermark!",
        "too_big": "⚠️ This file is too large to send on Telegram ({size} MB). Please try another video.",
        "error": "❌ Something went wrong while downloading. Please try again or use another link.",
        "lang_set": "✅ Language set to English",
    },
    "tr": {
        "choose_lang": "Lütfen dilinizi seçin 👇",
        "welcome": (
            "🎬 <b>Video İndirme Botuna Hoş Geldiniz</b>\n\n"
            "TikTok, Instagram veya Pinterest'ten bir bağlantı gönderin,\n"
            "en yüksek kalitede ve filigransız olarak geri göndereyim.\n\n"
            "Dili değiştirmek için: /language"
        ),
        "send_link": "🔗 Lütfen bir video bağlantısı gönderin (TikTok / Instagram / Pinterest)",
        "invalid_link": "⚠️ Bu bağlantı desteklenmiyor. Geçerli bir TikTok, Instagram veya Pinterest bağlantısı gönderin.",
        "downloading": "⏳ Lütfen bekleyin... video indiriliyor",
        "uploading": "📤 Video Telegram'a yükleniyor...",
        "success": "✅ Yüksek kalite, filigransız!",
        "too_big": "⚠️ Bu dosya Telegram'da göndermek için çok büyük ({size} MB). Başka bir video deneyin.",
        "error": "❌ İndirme sırasında bir hata oluştu. Lütfen tekrar deneyin.",
        "lang_set": "✅ Dil Türkçe olarak ayarlandı",
    },
    "ru": {
        "choose_lang": "Пожалуйста, выберите язык 👇",
        "welcome": (
            "🎬 <b>Добро пожаловать в бота для скачивания видео</b>\n\n"
            "Отправьте ссылку с TikTok, Instagram или Pinterest,\n"
            "и я пришлю видео в лучшем качестве, без водяного знака.\n\n"
            "Чтобы сменить язык: /language"
        ),
        "send_link": "🔗 Пожалуйста, отправьте ссылку на видео (TikTok / Instagram / Pinterest)",
        "invalid_link": "⚠️ Эта ссылка не поддерживается. Отправьте корректную ссылку TikTok, Instagram или Pinterest.",
        "downloading": "⏳ Подождите... видео скачивается",
        "uploading": "📤 Загрузка видео в Telegram...",
        "success": "✅ Высокое качество, без водяного знака!",
        "too_big": "⚠️ Файл слишком большой для отправки в Telegram ({size} MB). Попробуйте другое видео.",
        "error": "❌ Произошла ошибка при скачивании. Попробуйте снова.",
        "lang_set": "✅ Язык изменён на русский",
    },
    "fr": {
        "choose_lang": "Veuillez choisir votre langue 👇",
        "welcome": (
            "🎬 <b>Bienvenue sur le bot de téléchargement de vidéos</b>\n\n"
            "Envoyez un lien TikTok, Instagram ou Pinterest,\n"
            "et je vous renverrai la vidéo en haute qualité, sans filigrane.\n\n"
            "Pour changer de langue : /language"
        ),
        "send_link": "🔗 Veuillez envoyer un lien vidéo (TikTok / Instagram / Pinterest)",
        "invalid_link": "⚠️ Ce lien n'est pas pris en charge. Envoyez un lien TikTok, Instagram ou Pinterest valide.",
        "downloading": "⏳ Veuillez patienter... téléchargement de la vidéo",
        "uploading": "📤 Envoi de la vidéo sur Telegram...",
        "success": "✅ Haute qualité, sans filigrane !",
        "too_big": "⚠️ Ce fichier est trop volumineux pour Telegram ({size} MB). Essayez une autre vidéo.",
        "error": "❌ Une erreur s'est produite lors du téléchargement. Réessayez.",
        "lang_set": "✅ Langue définie sur le français",
    },
}

LANG_BUTTONS = [
    ("🟢 کوردی سۆرانی", "ku_sorani"),
    ("🟡 کرمانجی (بادینی)", "ku_badini"),
    ("🔵 English", "en"),
    ("🔴 Türkçe", "tr"),
    ("⚪ Русский", "ru"),
    ("🟣 Français", "fr"),
]


def t(user_id, key, **kwargs):
    lang = user_lang.get(user_id, "en")
    text = TEXTS.get(lang, TEXTS["en"]).get(key, "")
    return text.format(**kwargs) if kwargs else text


def language_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [types.InlineKeyboardButton(label, callback_data=f"setlang:{code}")
               for label, code in LANG_BUTTONS]
    markup.add(*buttons)
    return markup


# =========================
# ڕیگەخۆشکراوەکان (پاتەرن بۆ ناسینەوەی لینک)
# =========================
URL_PATTERNS = [
    r"(https?://)?(www\.)?(vm\.|vt\.)?tiktok\.com/\S+",
    r"(https?://)?(www\.)?instagram\.com/\S+",
    r"(https?://)?(www\.)?pin(terest)?\.(com|it)/\S+",
    r"(https?://)?pin\.it/\S+",
]


def extract_url(text):
    for pattern in URL_PATTERNS:
        match = re.search(pattern, text)
        if match:
            url = match.group(0)
            if not url.startswith("http"):
                url = "https://" + url
            return url
    return None


# =========================
# داونلۆدکردن بە yt-dlp (بەبێ واتەرمارک، باشترین کوالیتی)
# =========================
def download_video(url, out_path):
    ydl_opts = {
        "outtmpl": out_path,
        "format": "bestvideo+bestaudio/best/best",
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "retries": 5,
        "fragment_retries": 5,
        "socket_timeout": 20,  # وا لێدەکات کۆنێکشنی هێواو یان بەربەست بۆ هەتاهەتایە چاوەڕوان نەکرێت
        # yt-dlp بۆ TikTok بەشێوەیەکی سرووشتی وەشانی بەبێ واتەرمارک وەردەگرێت
        "extractor_args": {
            "tiktok": {"webpage_download_timeout": ["20"]}
        },
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


def download_video_with_timeout(url, out_path, timeout=DOWNLOAD_TIMEOUT_SEC):
    """
    داگرتنی ڤیدیۆ بە سنووری کات. ئەگەر داگرتنەکە لە کاتی دیاریکراودا تەواو نەبێت،
    TimeoutError هەڵدەدات بۆ ئەوەی بۆتەکە بۆ هەتاهەتایە بەستراو نەمێنێتەوە.
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(download_video, url, out_path)
        future.result(timeout=timeout)


# =========================
# هاندلەرەکانی بۆت
# =========================
@bot.message_handler(commands=["start"])
def handle_start(message):
    uid = message.from_user.id
    if uid not in user_lang:
        bot.send_message(message.chat.id, "🌐 Please choose your language:",
                          reply_markup=language_keyboard())
    else:
        bot.send_message(message.chat.id, t(uid, "welcome"))


@bot.message_handler(commands=["language"])
def handle_language(message):
    bot.send_message(message.chat.id, "🌐 Please choose your language:",
                      reply_markup=language_keyboard())


@bot.callback_query_handler(func=lambda call: call.data.startswith("setlang:"))
def handle_set_language(call):
    uid = call.from_user.id
    lang_code = call.data.split(":")[1]
    user_lang[uid] = lang_code
    bot.answer_callback_query(call.id, t(uid, "lang_set"))
    bot.edit_message_text(t(uid, "welcome"), call.message.chat.id, call.message.message_id)


@bot.message_handler(func=lambda message: True, content_types=["text"])
def handle_message(message):
    uid = message.from_user.id
    if uid not in user_lang:
        bot.send_message(message.chat.id, "🌐 Please choose your language first:",
                          reply_markup=language_keyboard())
        return

    url = extract_url(message.text)
    if not url:
        bot.send_message(message.chat.id, t(uid, "invalid_link"))
        return

    status_msg = bot.send_message(message.chat.id, t(uid, "downloading"))

    file_path = os.path.join(DOWNLOAD_DIR, f"{uid}_{int(time.time())}.mp4")

    try:
        download_video_with_timeout(url, file_path)

        if not os.path.exists(file_path):
            # yt-dlp لەوانەیە پاشگرێکی جیاواز داوینت (webm هتد)
            base, _ = os.path.splitext(file_path)
            for ext in [".mp4", ".webm", ".mkv"]:
                if os.path.exists(base + ext):
                    file_path = base + ext
                    break

        if not os.path.exists(file_path):
            raise FileNotFoundError("Downloaded file not found")

        size_mb = os.path.getsize(file_path) / (1024 * 1024)

        if size_mb > MAX_TELEGRAM_SIZE_MB:
            bot.edit_message_text(t(uid, "too_big", size=round(size_mb, 1)),
                                   message.chat.id, status_msg.message_id)
        else:
            bot.edit_message_text(t(uid, "uploading"), message.chat.id, status_msg.message_id)
            with open(file_path, "rb") as video_file:
                bot.send_video(message.chat.id, video_file, caption=t(uid, "success"))
            bot.delete_message(message.chat.id, status_msg.message_id)

    except concurrent.futures.TimeoutError:
        print(f"⏱️ Download timed out for url: {url}")
        try:
            bot.edit_message_text(t(uid, "error"), message.chat.id, status_msg.message_id)
        except Exception:
            bot.send_message(message.chat.id, t(uid, "error"))
    except Exception:
        traceback.print_exc()
        try:
            bot.edit_message_text(t(uid, "error"), message.chat.id, status_msg.message_id)
        except Exception:
            bot.send_message(message.chat.id, t(uid, "error"))
    finally:
        # پاککردنەوەی فایلی داونلۆدکراو دوای ناردن
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass


# =========================
# ڕاکردنی بۆت بە شێوەیەکی بەردەوام (بەبێ ڕاوەستان لەبەر هەڵە)
# =========================
def run_bot():
    while True:
        try:
            print("🤖 Bot is running...")
            # skip_pending=True: نامەی کۆنی چاوەڕوان پشتگوێدەخات، بۆ ئەوەی لە کاتی
            # ڕاکردنەوەی بۆتەکە قەڵەبالغی نامە کۆن دووبارە پرۆسێس نەکرێن
            bot.infinity_polling(timeout=30, long_polling_timeout=30, skip_pending=True)
        except Exception as e:
            # ئەگەر هەڵەی "409 Conflict" ببینیت، ئەوا وایە کۆپیایەکی تری ئەم
            # بۆتە (بە هەمان تۆکن) لە شوێنێکی تردا خۆی ڕادەکات - تەنها یەک
            # کۆپیا لە یەک کاتدا دەتوانێت بە هەمان تۆکن ڕابکات.
            print("⚠️ Bot crashed, restarting in 5 seconds:", e)
            time.sleep(5)


if __name__ == "__main__":
    if BOT_TOKEN == "PUT_YOUR_BOT_TOKEN_HERE":
        print("❗ تکایە یەکەم جار BOT_TOKEN دابنێ لە سەرەوەی فایلەکە.")
    else:
        run_bot()
