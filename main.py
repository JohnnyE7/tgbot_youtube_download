from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, CallbackContext
import yt_dlp
import io
import os

from config import TELEGRAM_TOKEN, PROXY

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Привет! Отправь мне ссылку на YouTube, и я помогу скачать видео.")

async def download_video(update: Update, context: CallbackContext):
    url = update.message.text
    if "youtube.com" in url or "youtu.be" in url:
        try:
            processing_message = await update.message.reply_text("Переходим по ссылочке, пажжи мальца не кипишуй...")

            ydl_opts = {
                'noplaylist': True,
                'format': 'bestvideo+bestaudio',
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

            qualities = {}
            for format in info.get('formats', []):
                if 'format_note' in format and 'format_id' in format:
                    note = format['format_note']
                    format_id = format['format_id']
                    if note in ['144p', '240p', '360p', '480p', '720p', '1080p']:
                        qualities[note] = format_id

            await processing_message.delete()

            if qualities:
                keyboard = [[InlineKeyboardButton(q, callback_data=q)] for q in sorted(qualities.keys())]
                keyboard.append([InlineKeyboardButton("Отмена", callback_data="cancel")])
                reply_markup = InlineKeyboardMarkup(keyboard)
                quality_message = await update.message.reply_text("Выбери качество:", reply_markup=reply_markup)
                context.user_data['url'] = url
                context.user_data['qualities'] = qualities
                context.user_data['quality_message'] = quality_message
            else:
                await update.message.reply_text("Не удалось получить доступные качества.")
        except Exception as e:
            await update.message.reply_text(f"Ошибка: {e}")
    else:
        await update.message.reply_text("Это не похоже на ссылку YouTube.")

async def handle_quality_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        await query.message.delete()
        await query.message.reply_text("Отменено!")
        return

    quality = query.data
    url = context.user_data.get('url')
    qualities = context.user_data.get('qualities', {})
    quality_message = context.user_data.get('quality_message')

    if quality_message:
        await quality_message.delete()

    if not url or quality not in qualities:
        await query.message.reply_text("Ошибка: не удалось получить информацию о видео.")
        return

    format_id = qualities[quality]
    try:
        sending_message = await query.message.reply_text("Скидываю видосик, братишка...")

        ydl_opts = {
            'noplaylist': True,
            'format': format_id,
            'socket_timeout': 30,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_name = ydl.prepare_filename(info)

            with open(file_name, "rb") as video_file:
                video_data = video_file.read()

            video_stream = io.BytesIO(video_data)
            video_stream.name = file_name

        await sending_message.delete()
        await query.message.reply_video(video_stream)
        video_stream.close()

        if os.path.exists(file_name):
            os.remove(file_name)

    except Exception as e:
        await query.message.reply_text(f"Ошибка: {e}")

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))
    application.add_handler(CallbackQueryHandler(handle_quality_selection))
    application.run_polling()

if __name__ == '__main__':
    main()