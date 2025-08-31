import asyncio
import json
import os
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from bot import bot, SOUND_URLS, OWNER_ID, HISTORY_FILE

CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 300))

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ===== Фоновая задача для проверки новых видео =====
async def check_new_videos():
    seen_videos = {}
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            seen_videos.update(json.load(f))

    while True:
        for idx, sound in enumerate(SOUND_URLS):
            url = sound['url']
            name = sound.get('name') or f'#{idx+1}'
            try:
                r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
                soup = BeautifulSoup(r.text, "html.parser")
                videos = [a['href'] for a in soup.find_all("a", href=True) if "/video/" in a["href"]]
                new_videos = []

                if url not in seen_videos:
                    seen_videos[url] = []

                for v in videos:
                    if v not in seen_videos[url]:
                        seen_videos[url].append(v)
                        new_videos.append(v)

                if new_videos and OWNER_ID:
                    for v in new_videos:
                        await bot.send_message(OWNER_ID, f"🆕 Новый ролик под звуком: {name}\n{v}")

                with open(HISTORY_FILE, 'w') as f:
                    json.dump(seen_videos, f)
            except Exception as e:
                print("Ошибка при проверке видео:", e)
        await asyncio.sleep(CHECK_INTERVAL)

@app.on_event("startup")
async def startup_event():
    # Запуск фоновой задачи проверки новых видео
    asyncio.create_task(check_new_videos())

# ===== Главная страница =====
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "sounds": SOUND_URLS})

# ===== Страница конкретного звука и последние 5 видео =====
@app.get("/sound/{sound_idx}", response_class=HTMLResponse)
async def sound_page(request: Request, sound_idx: int):
    if 0 <= sound_idx < len(SOUND_URLS):
        sound = SOUND_URLS[sound_idx]
        url = sound['url']
        name = sound.get('name') or f'#{sound_idx+1}'
        # Получаем последние 5 видео
        try:
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(r.text, "html.parser")
            videos = [a['href'] for a in soup.find_all("a", href=True) if "/video/" in a["href"]]
            latest_videos = videos[:5]  # последние 5
        except Exception:
            latest_videos = []

        return templates.TemplateResponse("sound.html", {
            "request": request,
            "sound": sound,
            "latest_videos": latest_videos
        })
    return HTMLResponse("Звук не найден", status_code=404)
