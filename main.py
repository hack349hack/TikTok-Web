from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os, json

app = FastAPI()
templates = Jinja2Templates(directory="templates")

SOUNDS_FILE = "sounds.json"
HISTORY_FILE = "seen_videos.json"

# Загрузка данных
try:
    with open(SOUNDS_FILE, "r") as f:
        SOUND_URLS = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    SOUND_URLS = []

try:
    with open(HISTORY_FILE, "r") as f:
        seen_videos = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    seen_videos = {}

# Главная страница
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "sounds": SOUND_URLS})

# Форма добавления звука
@app.get("/add_sound", response_class=HTMLResponse)
async def add_sound_form(request: Request):
    return templates.TemplateResponse("add_sound.html", {"request": request})

# Обработка добавления звука
@app.post("/add_sound")
async def add_sound_submit(url: str = Form(...), name: str = Form(None)):
    SOUND_URLS.append({"url": url, "name": name})
    with open(SOUNDS_FILE, "w") as f:
        json.dump(SOUND_URLS, f)
    return {"status": "ok"}

# Просмотр последних видео (демо)
@app.get("/last_videos", response_class=HTMLResponse)
async def last_videos(request: Request):
    # Пример: берем последние 5 видео из seen_videos
    videos = []
    for sound in SOUND_URLS:
        url = sound["url"]
        vids = seen_videos.get(url, [])[-5:]
        for v in vids:
            videos.append({"url": v})
    return templates.TemplateResponse("last_videos.html", {"request": request, "videos": videos})
