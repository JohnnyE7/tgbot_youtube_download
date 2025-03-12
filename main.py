from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, CallbackContext
import yt_dlp
import os
import datetime
import mysql.connector

from config import TELEGRAM_TOKEN, DB_HOST, DB_USER, DB_PASSWORD, DB_NAME


MAX_REQUESTS = 3
TIME_WINDOW = 60
QUALITY_TIMEOUT = 180


SUPPORT_MESSAGE_INTERVAL = datetime.timedelta(days=2)
LAST_SUPPORT_MESSAGE = None


def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )


def is_user_logged_in(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE telegram_id = %s", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None


async def register(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if is_user_logged_in(user_id):
        await update.message.reply_text("Ты уже в системе, друг 😎 Вперёд за видосами!")
        return

    await update.message.reply_text("Придумай пароль и отправь мне 🔒")
    context.user_data['registering'] = True


async def login(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if is_user_logged_in(user_id):
        await update.message.reply_text("Ты уже вошёл, красавчик 😏 Жги!")
        return

    await update.message.reply_text("Введи свой пароль, и я тебя пущу 🚪")
    context.user_data['logging_in'] = True


async def handle_text(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    text = update.message.text.strip()

    if context.user_data.get('registering'):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (telegram_id, password) VALUES (%s, %s)", (user_id, text))
        conn.commit()
        conn.close()
        context.user_data.pop('registering', None)
        await update.message.reply_text("Ты в игре! Теперь залогинься с помощью /login 🔑")
        return

    if context.user_data.get('logging_in'):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE telegram_id = %s AND password = %s", (user_id, text))
        result = cursor.fetchone()
        conn.close()
        if result:
            context.user_data.pop('logging_in', None)
            await update.message.reply_text("Добро пожаловать! Ты теперь в клубе 🎉")
        else:
            await update.message.reply_text("Упс, пароль не тот 🤔 Попробуй ещё раз")
        return

    if not is_user_logged_in(user_id):
        await update.message.reply_text("Эй, а ты кто? 🤨 Залогинься командой /login или зарегайся через /register")
        return

    await download_video(update, context)


async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Йо! Кидай мне ссылку на YouTube, и я помогу тебе скачать что угодно 🎬🔥")



async def send_support_message(update: Update, context: CallbackContext):
    global LAST_SUPPORT_MESSAGE
    now = datetime.datetime.now()

    if LAST_SUPPORT_MESSAGE and now - LAST_SUPPORT_MESSAGE < SUPPORT_MESSAGE_INTERVAL:
        return

    LAST_SUPPORT_MESSAGE = now

    keyboard = [
        [InlineKeyboardButton("☕ Поддержать автора", url="https://www.tbank.ru/cf/7Bl1tQ07Aw6")],
        [InlineKeyboardButton("📢 Мои соцсети", url="https://t.me/JohnnySvnt")],
        [InlineKeyboardButton("📩 Оставить отзыв", callback_data="feedback")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = update.message if update.message else update.callback_query.message

    await message.reply_text(
        "🔥 Поддержи проект! Буду рад любой помощи 💖\n\n"
        "☕ Чай, кофе, печеньки – всё в дело!\n"
        "📢 Подпишись, будь на связи\n"
        "📩 Оставь фидбэк, это важно!",
        reply_markup=reply_markup
    )


async def handle_feedback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("Напиши сюда свои мысли и пожелания, я всё читаю! Спасибо 🤗")


async def download_video(update: Update, context: CallbackContext):
    url = update.message.text.strip()
    if "youtube.com" not in url and "youtu.be" not in url:
        await update.message.reply_text("Хмм... 🤔 Это не похоже на YouTube-ссылку")
        return

    processing_message = await update.message.reply_text("Дай мне пару секунд, сейчас замучу видос 🎥⚡")

    try:
        ydl_opts = {'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        qualities = {
            f['format_note']: f['format_id']
            for f in info.get('formats', [])
            if 'format_note' in f and 'format_id' in f and f['format_note'] in ['144p', '240p', '360p', '480p', '720p', '1080p']
        }

        await processing_message.delete()

        if qualities:
            keyboard = [[InlineKeyboardButton(q, callback_data=q)] for q in sorted(qualities.keys())]
            keyboard.append([InlineKeyboardButton("🎵 MP3", callback_data="mp3")])
            keyboard.append([InlineKeyboardButton("🚫 Отмена", callback_data="cancel")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            quality_message = await update.message.reply_text("Выбери качество 🎬", reply_markup=reply_markup)

            context.user_data.update({
                'url': url,
                'qualities': qualities,
                'info': info,
                'quality_message': quality_message
            })
        else:
            await update.message.reply_text("Упс! Качество не найдено 😕")

    except Exception as e:
        await processing_message.delete()
        await update.message.reply_text(f"Ой, ошибочка вышла: {e} 😢")


async def handle_quality_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        await query.message.delete()
        await query.message.reply_text("Отменено!")
        return

    url = context.user_data.get('url')
    qualities = context.user_data.get('qualities', {})
    quality_message = context.user_data.pop('quality_message', None)

    if quality_message:
        await quality_message.delete()

    if query.data == "mp3":
        sending_message = await query.message.reply_text("🎶 Качаем аудио в MP3, погоди немного...")

        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': '%(title)s.%(ext)s',
            'quiet': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_name = ydl.prepare_filename(info).replace(".webm", ".mp3").replace(".m4a", ".mp3")

            with open(file_name, "rb") as audio_file:
                await query.message.reply_audio(audio_file)

            os.remove(file_name)

        except Exception as e:
            await query.message.reply_text(f"Ошибка при скачивании MP3: {e}")

        await sending_message.delete()
        await send_support_message(update, context)  # Отправляем кнопки поддержки
        return

    format_id = qualities.get(query.data)
    if not url or not format_id:
        await query.message.reply_text("Ошибка: не удалось получить информацию о видео.")
        return

    sending_message = await query.message.reply_text("📥 Скидываю видосик, погоди чутка...")

    try:
        ydl_opts = {
            'format': f"{format_id}+bestaudio",
            'merge_output_format': 'mp4',
            'outtmpl': '%(title)s.%(ext)s',
            'quiet': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            file_info = ydl.extract_info(url, download=True)
            file_name = ydl.prepare_filename(file_info)

        with open(file_name, "rb") as video_file:
            await query.message.reply_video(video_file)

        os.remove(file_name)

    except Exception as e:
        await query.message.reply_text(f"Ошибка: {e}")

    await sending_message.delete()
    await send_support_message(update, context)  # Отправляем кнопки поддержки


def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("register", register))
    application.add_handler(CommandHandler("login", login))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(CallbackQueryHandler(handle_quality_selection))
    application.run_polling()


if __name__ == '__main__':
    main()