from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler  # Добавлен импорт CallbackQueryHandler
import yt_dlp
import os
from config import TELEGRAM_TOKEN, PROXY

# Функция для начала работы
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Привет! Отправь мне ссылку на YouTube, и я помогу скачать видео.")

# Функция для скачивания видео
async def download_video(update: Update, context: CallbackContext):
    url = update.message.text
    if "youtube.com" in url or "youtu.be" in url:
        # Сначала получаем информацию о видео
        try:
            ydl_opts = {
                'proxy': PROXY,  # Указываем прокси
                'noplaylist': True,  # Не скачиваем плейлисты
                'format': 'bestvideo+bestaudio',  # Загружаем лучшее видео и аудио
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)  # Загружаем только информацию, без скачивания

            # Получаем доступные качества видео
            formats = info.get('formats', [])
            qualities = [format['format_note'] for format in formats if 'format_note' in format]

            # Если доступные качества найдены
            if qualities:
                keyboard = [
                    [InlineKeyboardButton(quality, callback_data=quality)] for quality in qualities
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                # Просим пользователя выбрать качество
                await update.message.reply_text(
                    "Выбери качество, в котором скачается видео:",
                    reply_markup=reply_markup
                )

                context.user_data['url'] = url  # Сохраняем URL для дальнейшего использования

            else:
                await update.message.reply_text("Не удалось получить доступные качества для этого видео.")
        except Exception as e:
            await update.message.reply_text(f"Ошибка при получении информации о видео: {e}")
    else:
        await update.message.reply_text("Это не похоже на ссылку YouTube.")

# Функция для обработки выбора качества
async def quality_choice(update: Update, context: CallbackContext):
    query = update.callback_query
    selected_quality = query.data  # Получаем выбранное качество
    await query.answer()  # Подтверждаем выбор пользователя

    # Скачиваем видео с выбранным качеством
    url = context.user_data['url']  # Получаем ссылку на видео из контекста
    try:
        ydl_opts = {
            'outtmpl': 'downloads/%(title)s.%(ext)s',  # Путь для сохранения файла
            'proxy': PROXY,  # Указываем адрес прокси
            'format': f'bestvideo[format_note={selected_quality}]+bestaudio[ext=m4a]/mp4',  # Скачиваем видео в указанном качестве
            'noplaylist': True,  # Не скачиваем плейлисты
            'socket_timeout': 30,  # Увеличиваем тайм-аут
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_name = ydl.prepare_filename(info)

        # Отправляем сообщение о завершении загрузки
        await query.edit_message_text("Готово! Отправляю видео...")
        with open(file_name, 'rb') as video:
            await query.message.reply_video(video)

        # Удаляем файл после отправки
        os.remove(file_name)

    except Exception as e:
        await query.edit_message_text(f"Ошибка при скачивании: {e}")

def main():
    # Создаём приложение
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))
    application.add_handler(CallbackQueryHandler(quality_choice))  # Добавляем обработчик CallbackQuery

    # Запуск приложения
    application.run_polling()

if __name__ == '__main__':
    main()
