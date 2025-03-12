import sqlite3
import bcrypt


# Функция для инициализации базы данных
def init_db():
    conn = sqlite3.connect("user_settings.db")
    c = conn.cursor()

    # Создаем таблицу пользователей
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            password_hash TEXT,
            need_description BOOLEAN
        )
    ''')

    conn.commit()
    conn.close()


# Регистрация пользователя
def register_user(telegram_id, password):
    # Хэшируем пароль
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    conn = sqlite3.connect("user_settings.db")
    c = conn.cursor()

    # Добавляем пользователя в БД
    c.execute("INSERT INTO users (telegram_id, password_hash, need_description) VALUES (?, ?, ?)",
              (telegram_id, password_hash, False))  # По умолчанию описание не нужно
    conn.commit()
    conn.close()


# Логин пользователя
def login_user(telegram_id, password):
    conn = sqlite3.connect("user_settings.db")
    c = conn.cursor()

    c.execute("SELECT password_hash FROM users WHERE telegram_id=?", (telegram_id,))
    result = c.fetchone()

    conn.close()

    if result and bcrypt.checkpw(password.encode('utf-8'), result[0]):
        return True
    return False


# Обновление предпочтений описания
def set_description_preference(telegram_id, need_description):
    conn = sqlite3.connect("user_settings.db")
    c = conn.cursor()

    c.execute("UPDATE users SET need_description=? WHERE telegram_id=?", (need_description, telegram_id))
    conn.commit()
    conn.close()


# Получение предпочтений описания
def get_description_preference(telegram_id):
    conn = sqlite3.connect("user_settings.db")
    c = conn.cursor()

    c.execute("SELECT need_description FROM users WHERE telegram_id=?", (telegram_id,))
    result = c.fetchone()

    conn.close()

    return result[0] if result else False
