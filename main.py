from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, CallbackContext
import yt_dlp
import os

from config import TELEGRAM_TOKEN, PROXY

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Привет! Отправь мне ссылку на YouTube, и я помогу скачать видео.")

# Функция для выбора качества
async def download_video(update: Update, context: CallbackContext):
    url = update.message.text
    if "youtube.com" in url or "youtu.be" in url:
        # Получаем информацию о видео
        try:
            ydl_opts = {
                # 'proxy': PROXY,  # Указываем прокси
                'noplaylist': True,  # Не скачиваем плейлисты
                'format': 'bestvideo+bestaudio',  # Загружаем лучшее видео и аудио
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)  # Загружаем только информацию, без скачивания

            cnt = 0
            for format in info['formats']:
                cnt += 1
                print(f"{cnt} Available format: {format}")

            # Получаем доступные качества
            formats = info.get('formats', [])
            qualities = set()

            for format in formats:
                if 'format_note' in format:
                    note = format['format_note']
                    if note in ['144p', '240p', '360p', '480p', '720p', '1080p']:
                        qualities.add(note)

            if qualities:
                keyboard = [
                    [InlineKeyboardButton(quality, callback_data=quality)] for quality in sorted(qualities)
                ]
                keyboard.append([InlineKeyboardButton("Отмена", callback_data="cancel")])  # Добавляем кнопку отмены
                reply_markup = InlineKeyboardMarkup(keyboard)

                # Сообщение выбора качества
                await update.message.reply_text(
                    "Выбери качество, в котором скачается видео:",
                    reply_markup=reply_markup
                )

                # Сохраняем информацию для обработки
                context.user_data['url'] = url

            else:
                await update.message.reply_text("Не удалось получить доступные качества для этого видео.")
        except Exception as e:
            await update.message.reply_text(f"Ошибка при получении информации о видео: {e}")
    else:
        await update.message.reply_text("Это не похоже на ссылку YouTube.")

# Функция для скачивания видео в выбранном качестве
async def handle_quality_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()  # Обязательно отвечаем на запрос, чтобы Telegram не показывал "часики"

    if query.data == "cancel":
        # Обработка отмены
        await query.message.delete()
        await query.message.reply_text("Отменено!")
        return

    quality = query.data
    url = context.user_data.get('url')

    if not url:
        await query.message.reply_text("Ошибка: не удалось получить ссылку на видео.")
        return

    try:
        # Фильтруем доступные форматы по качеству (параметры могут быть адаптированы)
        ydl_opts = {
            'outtmpl': 'downloads/%(title)s.%(ext)s',  # Путь для сохранения файла
            # 'proxy': PROXY,  # Указываем адрес прокси
            'noplaylist': True,  # Не скачиваем плейлисты
            'merge_output_format': 'mp4',  # Скачиваем в формате mp4
            'format': f'bestvideo[height<={quality[:-1]}][vcodec!*=vp9]+bestaudio/best',  # Для видео: ограничиваем высоту и исключаем VP9 кодек
            'socket_timeout': 30,  # Увеличиваем тайм-аут
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_name = ydl.prepare_filename(info)

        # Отправляем видео
        await query.message.delete()
        await query.message.reply_text(f"Готово! Отправляю видео в разрешении {quality}...")
        with open(file_name, 'rb') as video:
            await query.message.reply_video(video)

        # os.remove(file_name)

    except Exception as e:
        await query.message.reply_text(f"Ошибка при скачивании: {e}")

def main():
    # Создаём приложение
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))
    application.add_handler(CallbackQueryHandler(handle_quality_selection))

    # Запуск приложения
    application.run_polling()

if __name__ == '__main__':
    # main()
    handle_quality_selection()