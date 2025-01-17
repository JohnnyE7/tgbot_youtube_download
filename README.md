# YouTube Telegram Bot

Telegram-бот для скачивания видео с YouTube и отправки их пользователю.

## Установка

### 1. Создание виртуального окружения

Создайте виртуальное окружение:

```bash
python3 -m venv venv
```

Активируйте его:

Для Linux/Mac:
```bash
source venv/bin/activate
```
Для Windows:
```bash
venv\Scripts\activate
```
## 2. Установка зависимостей
Установите все необходимые зависимости:
```bash
pip install -r requirements.txt
```

## 3. Настройка конфигурации
Создайте файл config.py в корневой папке проекта и добавьте туда свой токен Telegram-бота и прокси (если используется):

```python
TELEGRAM_TOKEN = 'your-telegram-bot-token'
PROXY = 'http://username:password@proxyserver:port'  # Если используется прокси
```

## 4. Запуск бота
Запустите бота командой:
```bash
python bot.py
```
