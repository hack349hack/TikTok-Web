from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
import os
import requests
from bs4 import BeautifulSoup

app = FastAPI()

# Статика и шаблоны
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

SOUNDS_FILE = "sounds.json"

# Загружаем звуки
if os.path.exists(SOUNDS_FILE):
    with open(SOUNDS_FILE, "r") as f:
        SOUND_URLS = json.load(f)
else:
    SOUND_URLS = []

# Главная страница
@app.get("/", response_class=HTMLResponse)
async def index(request: Request, message: str = None):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "sounds": SOUND_URLS, "message": message}
    )

# Добавление звука
@app.post("/add_sound")
async def add_sound(url: str = Form(...), name: str = Form(None)):
    SOUND_URLS.append({"url": url, "name": name})
    with open(SOUNDS_FILE, "w") as f:
        json.dump(SOUND_URLS, f)
    return await index(Request(scope={"type":"http"}), message="✅ Звук добавлен!")

# Удаление звука
@app.post("/remove_sound")
async def remove_sound(index: int = Form(...)):
    if 0 <= index < len(SOUND_URLS):
        SOUND_URLS.pop(index)
        with open(SOUNDS_FILE, "w") as f:
            json.dump(SOUND_URLS, f)
    return await index(Request(scope={"type":"http"}), message="🗑 Звук удалён!")

# Получаем последние 5 видео под звуком
def get_last_videos(sound_url, limit=5):
    videos = []
    try:
        r = requests.get(sound_url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", href=True):
            if "/video/" in a["href"]:
                if a["href"] not in videos:
                    videos.append(a["href"])
                if len(videos) >= limit:
                    break
    except:
        pass
    return videos

# Страница с последними 5 видео
@app.get("/last_videos/{index}", response_class=HTMLResponse)
async def last_videos(request: Request, index: int):
    if 0 <= index < len(SOUND_URLS):
        sound = SOUND_URLS[index]
        videos = get_last_videos(sound["url"])
        return templates.TemplateResponse(
            "last_videos.html",
            {"request": request, "sound": sound, "videos": videos}
        )
    return await index(request, message="❌ Звук не найден")
