from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
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

# Главная страница со списком звуков
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "sounds": SOUND_URLS}
    )

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
    return RedirectResponse("/", status_code=303)

# Просмотр последних 5 видео для конкретного звука
@app.get("/last_videos/{sound_index}", response_class=HTMLResponse)
async def last_videos_for_sound(request: Request, sound_index: int):
    if sound_index < 0 or sound_index >= len(SOUND_URLS):
        return HTMLResponse("❌ Звук не найден", status_code=404)

    sound = SOUND_URLS[sound_index]
    url = sound.get("url")
    vids = seen_videos.get(url, [])
    last5 = vids[-5:] if isinstance(vids, list) else []

    return templates.TemplateResponse(
        "last_videos.html",
        {
            "request": request,
            "sound_name": sound.get("name") or url,
            "videos": last5[::-1]  # последние видео сверху
        }
    )
