import asyncio
import json
import os
from aiogram import Bot, Dispatcher
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext

TOKEN = os.getenv("TOKEN")
OWNER_ID = None

HISTORY_FILE = 'seen_videos.json'
SOUNDS_FILE = 'sounds.json'
SOUNDS_PER_PAGE = 5

storage = MemoryStorage()
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=storage)

# ===== Загрузка звуков и истории =====
if os.path.exists(SOUNDS_FILE):
    with open(SOUNDS_FILE, 'r') as f:
        SOUND_URLS = json.load(f)
else:
    SOUND_URLS = []

if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, 'r') as f:
        seen_videos = json.load(f)
else:
    seen_videos = {}

rename_state = {}

# ===== FSM =====
class AddSoundStates(StatesGroup):
    waiting_for_url = State()
    waiting_for_name = State()

# ===== Клавиатуры =====
def get_main_keyboard():
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton("➕ Добавить звук", callback_data="add_sound"),
                InlineKeyboardButton(
                    "📃 Список звуков",
                    callback_data="list_sounds" if SOUND_URLS else "no_sounds"
                )
            ]
        ]
    )
    return kb

def build_sounds_keyboard(page: int = 0):
    start = page * SOUNDS_PER_PAGE
    end = start + SOUNDS_PER_PAGE
    sounds_page = SOUND_URLS[start:end]
    if not sounds_page:
        return None

    inline_keyboard = []
    for i, sound in enumerate(sounds_page, start=start):
        inline_keyboard.append([
            InlineKeyboardButton(f"🗑 {sound.get('name') or 'Без имени'}", callback_data=f"remove_sound_{i}"),
            InlineKeyboardButton(f"✏️ {sound.get('name') or 'Без имени'}", callback_data=f"rename_sound_{i}")
        ])
    inline_keyboard.append([InlineKeyboardButton("➕ Добавить звук", callback_data="add_sound")])

    nav_buttons = []
    if start > 0:
        nav_buttons.append(InlineKeyboardButton('⬅️ Назад', callback_data=f'page_{page-1}'))
    if end < len(SOUND_URLS):
        nav_buttons.append(InlineKeyboardButton('➡️ Вперёд', callback_data=f'page_{page+1}'))
    if nav_buttons:
        inline_keyboard.append(nav_buttons)

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

# ===== Команды бота =====
@dp.message(Command("start"))
async def start_cmd(message: Message):
    global OWNER_ID
    OWNER_ID = message.chat.id
    await message.answer("✅ Бот запущен!", reply_markup=get_main_keyboard())

# Добавление звука через кнопку
@dp.callback_query(lambda c: c.data == "add_sound")
async def inline_add_sound(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("🔗 Пришли ссылку на звук TikTok:")
    await state.set_state(AddSoundStates.waiting_for_url)
    await callback.answer()

@dp.message(AddSoundStates.waiting_for_url)
async def add_sound_get_url(message: Message, state: FSMContext):
    await state.update_data(url=message.text)
    await message.answer("✏️ Теперь пришли название звука (или напиши 'нет' для пропуска):")
    await state.set_state(AddSoundStates.waiting_for_name)

@dp.message(AddSoundStates.waiting_for_name)
async def add_sound_get_name(message: Message, state: FSMContext):
    data = await state.get_data()
    url = data['url']
    name = message.text if message.text.lower() != 'нет' else None
    SOUND_URLS.append({'url': url, 'name': name})
    with open(SOUNDS_FILE, 'w') as f:
        json.dump(SOUND_URLS, f)
    await message.answer(f"✅ Звук добавлен: {name or url}", reply_markup=get_main_keyboard())
    await state.clear()

# Список звуков
@dp.callback_query(lambda c: c.data == "list_sounds")
async def inline_list_sounds(callback: CallbackQuery):
    kb = build_sounds_keyboard(page=0)
    if kb:
        text = "📃 Список звуков:\n"
        for i, sound in enumerate(SOUND_URLS[:SOUNDS_PER_PAGE], start=1):
            text += f"{i}. {sound.get('name') or 'Без имени'} — {sound['url']}\n"
        await callback.message.answer(text, reply_markup=kb)
    else:
        await callback.answer("❌ Звуков пока нет", show_alert=True)

@dp.callback_query(lambda c: c.data == "no_sounds")
async def inline_no_sounds(callback: CallbackQuery):
    await callback.answer("❌ Звуков пока нет", show_alert=True)

# Удаление
@dp.callback_query(lambda c: c.data.startswith("remove_sound_"))
async def callback_remove_sound(callback: CallbackQuery):
    idx = int(callback.data.split("_")[-1])
    if 0 <= idx < len(SOUND_URLS):
        removed = SOUND_URLS.pop(idx)
        with open(SOUNDS_FILE, 'w') as f:
            json.dump(SOUND_URLS, f)
        name = removed.get('name') or removed['url']
        await callback.message.edit_text(f"🗑 Звук удалён: {name}", reply_markup=get_main_keyboard())
        await callback.answer("Звук удалён")

# Переименование
@dp.callback_query(lambda c: c.data.startswith("rename_sound_"))
async def callback_rename_sound(callback: CallbackQuery):
    idx = int(callback.data.split("_")[-1])
    if 0 <= idx < len(SOUND_URLS):
        rename_state[callback.from_user.id] = idx
        await callback.message.answer("✏️ Введи новое имя для этого звука:")
        await callback.answer()

@dp.message()
async def handle_rename(message: Message):
    if message.from_user.id in rename_state:
        idx = rename_state.pop(message.from_user.id)
        SOUND_URLS[idx]['name'] = message.text
        with open(SOUNDS_FILE, 'w') as f:
            json.dump(SOUND_URLS, f)
        await message.answer(f"✅ Звук переименован: {message.text}", reply_markup=get_main_keyboard())
        return
