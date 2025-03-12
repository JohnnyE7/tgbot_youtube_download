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


