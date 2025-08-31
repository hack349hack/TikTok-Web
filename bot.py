import asyncio
import os
import json
from aiogram import Bot, Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

TOKEN = os.getenv("TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

bot = Bot(token=TOKEN)
dp = Dispatcher()

SOUNDS_FILE = "sounds.json"
HISTORY_FILE = "seen_videos.json"

# Загружаем звуки
try:
    with open(SOUNDS_FILE, "r") as f:
        SOUND_URLS = json.load(f)
except:
    SOUND_URLS = []

# Загружаем историю видео
try:
    with open(HISTORY_FILE, "r") as f:
        seen_videos = json.load(f)
except:
    seen_videos = {}

async def notify_new_video(sound_name, video_url):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶️ Открыть в TikTok", url=video_url)]
    ])
    await bot.send_message(OWNER_ID, f"🆕 Новый ролик под звуком: {sound_name}", reply_markup=kb)
