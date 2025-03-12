import sys
import os
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import start, register, login, handle_text, handle_quality_selection, download_video

import asyncio
from unittest.mock import AsyncMock, patch
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext
from main import start, register, login, handle_text, handle_quality_selection, download_video

@pytest.mark.asyncio
async def test_start_command():
    update = AsyncMock()
    update.message.text = "/start"
    await start(update, None)
    update.message.reply_text.assert_called_once_with("Йо! Кидай мне ссылку на YouTube, и я помогу тебе скачать что угодно 🎬🔥")

@pytest.mark.asyncio
async def test_register_existing_user():
    with patch("main.is_user_logged_in", return_value=True):
        update = AsyncMock()
        await register(update, None)
        update.message.reply_text.assert_called_once_with("Ты уже в системе, друг 😎 Вперёд за видосами!")

@pytest.mark.asyncio
async def test_register_new_user():
    with patch("main.is_user_logged_in", return_value=False):
        update = AsyncMock()
        context = AsyncMock()
        await register(update, context)
        update.message.reply_text.assert_called_once_with("Придумай пароль и отправь мне 🔒")
        assert context.user_data['registering']

@pytest.mark.asyncio
async def test_login_existing_user():
    with patch("main.is_user_logged_in", return_value=True):
        update = AsyncMock()
        await login(update, None)
        update.message.reply_text.assert_called_once_with("Ты уже вошёл, красавчик 😏 Жги!")

@pytest.mark.asyncio
async def test_login_new_user():
    with patch("main.is_user_logged_in", return_value=False):
        update = AsyncMock()
        context = AsyncMock()
        await login(update, context)
        update.message.reply_text.assert_called_once_with("Введи свой пароль, и я тебя пущу 🚪")
        assert context.user_data['logging_in']

@pytest.mark.asyncio
async def test_handle_text_not_logged_in():
    with patch("main.is_user_logged_in", return_value=False):
        update = AsyncMock()
        context = AsyncMock()
        await handle_text(update, context)
        update.message.reply_text.assert_called_once_with("Эй, а ты кто? 🤨 Залогинься командой /login или зарегайся через /register")

@pytest.mark.asyncio
async def test_download_video_invalid_url():
    update = AsyncMock()
    update.message.text = "https://example.com"
    await download_video(update, None)
    update.message.reply_text.assert_called_once_with("Хмм... 🤔 Это не похоже на YouTube-ссылку")

@pytest.mark.asyncio
async def test_handle_quality_selection_cancel():
    update = AsyncMock()
    context = AsyncMock()
    query = AsyncMock()
    query.data = "cancel"
    update.callback_query = query
    await handle_quality_selection(update, context)
    query.message.reply_text.assert_called_once_with("Отменено!")
