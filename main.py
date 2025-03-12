from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, CallbackContext
import yt_dlp
import os

from config import TELEGRAM_TOKEN

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Привет! Отправь мне ссылку на YouTube, и я помогу скачать видео.")

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
    info = context.user_data.get('info')

    if quality_message:
        await quality_message.delete()

    format_id = qualities.get(query.data)
    if not url or not format_id:
        await query.message.reply_text("Ошибка: не удалось получить информацию о видео.")
        return

    sending_message = await query.message.reply_text("Скидываю видосик, братишка...")

    try:
        ydl_opts = {
            'format': f"{format_id}+bestaudio",  # Комбинируем формат с лучшим аудио
            'merge_output_format': 'mp4',
            'quiet': True,
            'outtmpl': '%(title)s.%(ext)s',
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
