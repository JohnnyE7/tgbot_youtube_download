from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import yt_dlp
import os
from config import TELEGRAM_TOKEN, PROXY


async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Привет! Отправь мне ссылку на YouTube, и я помогу скачать видео.")


async def download_video(update: Update, context: CallbackContext):
    url = update.message.text
    if "youtube.com" in url or "youtu.be" in url:
        # Отправляем сообщение о начале загрузки
        loading_message = await update.message.reply_text("Начинаю загрузку, подожди немного...")

        try:
            ydl_opts = {
                'outtmpl': 'downloads/%(title)s.%(ext)s',  # Путь для сохранения файла
                'proxy': PROXY,  # Указываем адрес прокси
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',  # Скачиваем видео в mp4 формате
                'noplaylist': True,  # Не скачиваем плейлисты
                'socket_timeout': 30,  # Увеличиваем тайм-аут до 30 секунд
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_name = ydl.prepare_filename(info)

            # Удаляем сообщение о начале загрузки
            await loading_message.delete()

            # Отправляем сообщение о завершении загрузки и отправляем видео
            await update.message.reply_text("Готово! Отправляю видео...")
            with open(file_name, 'rb') as video:
                await update.message.reply_video(video)

            # Удаляем файл после отправки
            os.remove(file_name)

        except Exception as e:
            # Удаляем сообщение о начале загрузки в случае ошибки
            await loading_message.delete()
            await update.message.reply_text(f"Ошибка при скачивании: {e}")
    else:
        await update.message.reply_text("Это не похоже на ссылку YouTube.")


def main():
    # Создаём приложение
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))

    # Запуск приложения
    application.run_polling()


if __name__ == '__main__':
    main()
