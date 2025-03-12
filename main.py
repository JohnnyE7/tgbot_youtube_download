from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, CallbackContext
import yt_dlp
import os
import random
import datetime

from config import TELEGRAM_TOKEN

SUPPORT_MESSAGE_INTERVAL = datetime.timedelta(days=2)  # Раз в два дня
LAST_SUPPORT_MESSAGE = None

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Привет! Отправь мне ссылку на YouTube, и я помогу скачать видео.")

async def send_support_message(update: Update, context: CallbackContext):
    global LAST_SUPPORT_MESSAGE
    now = datetime.datetime.now()

    if LAST_SUPPORT_MESSAGE and now - LAST_SUPPORT_MESSAGE < SUPPORT_MESSAGE_INTERVAL:
        return  # Если ещё не прошло 2 дня, не отправляем повторно

    LAST_SUPPORT_MESSAGE = now  # Обновляем время последней отправки

    keyboard = [
        [InlineKeyboardButton("☕ Поддержать автора", url="https://www.donationalerts.com/")],
        [InlineKeyboardButton("📢 Мои соцсети", url="https://t.me/your_channel")],
        [InlineKeyboardButton("📩 Оставить отзыв", callback_data="feedback")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "💖 Поддержи проект! Буду рад любой помощи:\n\n"
        "☕ Чай, кофе и печеньки приветствуются!\n"
        "📢 Подпишись на мои соцсети\n"
        "📩 Напиши отзыв о боте",
        reply_markup=reply_markup
    )

async def handle_feedback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("Напиши сюда свои пожелания и жалобы. Я всё читаю, спасибо!")

async def download_video(update: Update, context: CallbackContext):
    url = update.message.text.strip()
    if "youtube.com" not in url and "youtu.be" not in url:
        await update.message.reply_text("Это не похоже на ссылку YouTube.")
        return

    processing_message = await update.message.reply_text("Переходим по ссылочке, пажжи мальца не кипишуй...")

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
            keyboard.append([InlineKeyboardButton("🎵 Скачать MP3", callback_data="mp3")])  # <-- Добавляем кнопку MP3
            keyboard.append([InlineKeyboardButton("Отмена", callback_data="cancel")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            quality_message = await update.message.reply_text("Выбери качество:", reply_markup=reply_markup)

            context.user_data.update({
                'url': url,
                'qualities': qualities,
                'info': info,
                'quality_message': quality_message
            })
        else:
            await update.message.reply_text("Не удалось получить доступные качества.")

    except Exception as e:
        await processing_message.delete()
        await update.message.reply_text(f"Ошибка: {e}")

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

    # Обработка запроса на MP3
    if query.data == "mp3":
        sending_message = await query.message.reply_text("🎶 Качаем аудио в MP3, погоди немного...")

        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',  # Можно 128, 192, 320
            }],
            'outtmpl': '%(title)s.%(ext)s',  # Шаблон имени файла
            'quiet': True,  # Отключаем спам в консоли
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_name = ydl.prepare_filename(info).replace(".webm", ".mp3").replace(".m4a", ".mp3")

            with open(file_name, "rb") as audio_file:
                await query.message.reply_audio(audio_file)

            os.remove(file_name)  # Удаляем после отправки

        except Exception as e:
            await query.message.reply_text(f"Ошибка при скачивании MP3: {e}")

        await sending_message.delete()
        return  # Выходим из функции после обработки MP3

    # Получаем выбранный формат видео
    format_id = qualities.get(query.data)
    if not url or not format_id:
        await query.message.reply_text("Ошибка: не удалось получить информацию о видео.")
        return

    sending_message = await query.message.reply_text("📥 Скидываю видосик, погоди чутка...")

    try:
        ydl_opts = {
            'format': f"{format_id}+bestaudio",  # Комбинируем видео + лучшее аудио
            'merge_output_format': 'mp4',  # Конвертация в mp4
            'outtmpl': '%(title)s.%(ext)s',
            'quiet': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            file_info = ydl.extract_info(url, download=True)
            file_name = ydl.prepare_filename(file_info)

        with open(file_name, "rb") as video_file:
            await query.message.reply_video(video_file)

        os.remove(file_name)  # Удаляем файл после отправки

    except Exception as e:
        await query.message.reply_text(f"Ошибка: {e}")

    await sending_message.delete()

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))
    application.add_handler(CallbackQueryHandler(handle_quality_selection))
    application.run_polling()

if __name__ == '__main__':
    main()
