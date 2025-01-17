from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import yt_dlp

from config import TELEGRAM_TOKEN, PROXY

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Привет! Отправь мне ссылку на YouTube, и я помогу скачать видео.")

async def download_video(update: Update, context: CallbackContext):
    url = update.message.text
    if "youtube.com" in url or "youtu.be" in url:
        await update.message.reply_text("Начинаю загрузку, подожди немного...")
        try:
            ydl_opts = {
                'outtmpl': 'downloads/%(title)s.%(ext)s',
                'proxy': PROXY,  # Указываем адрес прокси
                'format': 'bestvideo+bestaudio/best',
                'noplaylist': True,
                'socket_timeout': 30,  # Увеличиваем тайм-аут до 30 секунд
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_name = ydl.prepare_filename(info)

            await update.message.reply_text("Готово! Отправляю видео...")
            with open(file_name, 'rb') as video:
                await update.message.reply_video(video)

        except Exception as e:
            await update.message.reply_text(f"Ошибка при скачивании: {e}")
    else:
        await update.message.reply_text("Это не похоже на ссылку YouTube.")

def main():
    # Создаём приложение
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Обработчики-
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))

    # Запуск приложения
    application.run_polling()

if __name__ == '__main__':
    main()
