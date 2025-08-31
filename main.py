from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import requests
from bs4 import BeautifulSoup
import json, asyncio
from bot import notify_new_video, SOUND_URLS, HISTORY_FILE, bot

app = FastAPI()
templates = Jinja2Templates(directory="templates")

CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 300))

# Загрузка истории
try:
    with open(HISTORY_FILE, "r") as f:
        seen_videos = json.load(f)
except:
    seen_videos = {}

# Главная страница
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "sounds": SOUND_URLS})

# Добавление звука
@app.get("/add_sound", response_class=HTMLResponse)
async def add_sound_form(request: Request):
    return templates.TemplateResponse("add_sound.html", {"request": request})

@app.post("/add_sound")
async def add_sound_submit(url: str = Form(...), name: str = Form(None)):
    SOUND_URLS.append({"url": url, "name": name})
    with open("sounds.json", "w") as f:
        json.dump(SOUND_URLS, f)
    return RedirectResponse("/", status_code=303)

# Последние 5 видео
@app.get("/last_videos/{sound_index}", response_class=HTMLResponse)
async def last_videos(request: Request, sound_index: int):
    if sound_index < 0 or sound_index >= len(SOUND_URLS):
        return HTMLResponse("❌ Звук не найден", status_code=404)

    sound = SOUND_URLS[sound_index]
    vids = seen_videos.get(sound['url'], [])
    last5 = vids[-5:] if isinstance(vids, list) else []

    return templates.TemplateResponse("last_videos.html", {
        "request": request,
        "sound_name": sound.get("name") or sound['url'],
        "videos": last5[::-1]
    })

# === Парсер TikTok и уведомления в боте ===
async def check_new_videos():
    while True:
        for idx, sound in enumerate(SOUND_URLS):
            url = sound['url']
            name = sound.get('name') or f"#{idx+1}"
            try:
                r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
                soup = BeautifulSoup(r.text, "html.parser")
                video_links = [a['href'] for a in soup.find_all("a", href=True) if "/video/" in a['href']]

                if url not in seen_videos:
                    seen_videos[url] = []

                for vlink in video_links:
                    if vlink not in seen_videos[url]:
                        seen_videos[url].append(vlink)
                        with open(HISTORY_FILE, "w") as f:
                            json.dump(seen_videos, f)
                        await notify_new_video(name, vlink)

            except Exception as e:
                print("Ошибка при парсинге:", e)
        await asyncio.sleep(CHECK_INTERVAL)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(check_new_videos())
