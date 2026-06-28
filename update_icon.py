import os
import base64
import sqlite3
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
CITY = os.getenv("CITY", "Cork")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
DB_PATH = os.getenv("DB_PATH", "history.db")

WEATHER_OVERLAYS = {
    "clear": "clear.png",
    "clouds": "clouds.png",
    "rain": "rain.png",
    "drizzle": "drizzle.png",
    "thunderstorm": "thunderstorm.png",
    "snow": "snow.png",
    "mist": "mist.png",
    "fog": "fog.png",
    "haze": "haze.png",
    "smoke": "smoke.png",
    "dust": "dust.png",
    "sand": "sand.png",
    "ash": "ash.png",
    "squall": "squall.png",
    "tornado": "tornado.png",
}


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp   TEXT    NOT NULL,
                city        TEXT    NOT NULL,
                condition   TEXT    NOT NULL,
                description TEXT    NOT NULL,
                temp        INTEGER NOT NULL,
                season      TEXT    NOT NULL,
                overlay     TEXT    NOT NULL,
                success     INTEGER NOT NULL,
                error       TEXT
            )
        """)


def log_run(city, condition, description, temp, season, overlay, success, error=None):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """INSERT INTO runs
               (timestamp, city, condition, description, temp, season, overlay, success, error)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                datetime.now(timezone.utc).isoformat(),
                city, condition, description, temp, season, overlay,
                1 if success else 0,
                error,
            ),
        )


def get_season(month: int) -> str:
    if month in (3, 4, 5):   return "spring"
    if month in (6, 7, 8):   return "summer"
    if month in (9, 10, 11): return "autumn"
    return "winter"


def get_weather(city: str) -> dict:
    resp = requests.get(
        "https://api.openweathermap.org/data/2.5/weather",
        params={"q": city, "appid": OPENWEATHER_API_KEY, "units": "metric"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def load_image(image_path: str) -> bytes:
    with open(image_path, "rb") as f:
        return f.read()


def update_icon(image_bytes: bytes):
    encoded = base64.b64encode(image_bytes).decode()
    resp = requests.patch(
        f"https://discord.com/api/v10/guilds/{GUILD_ID}",
        headers={"Authorization": f"Bot {DISCORD_TOKEN}"},
        json={"icon": f"data:image/png;base64,{encoded}"},
        timeout=10,
    )
    resp.raise_for_status()


def post_to_discord(message: str):
    if not DISCORD_WEBHOOK_URL:
        return
    requests.post(DISCORD_WEBHOOK_URL, json={"content": message}, timeout=10)


def main():
    init_db()

    data = get_weather(CITY)
    condition = data["weather"][0]["main"].lower()
    description = data["weather"][0]["description"]
    temp = round(data["main"]["temp"])

    month = datetime.now(timezone.utc).month
    season = get_season(month)
    overlay_name = WEATHER_OVERLAYS.get(condition, "clear.png")
    image_path = os.path.join("images", overlay_name)

    if not os.path.exists(image_path):
        error = f"Image not found: {image_path}"
        print(f"ERROR: {error}")
        log_run(CITY, condition, description, temp, season, overlay_name, False, error)
        return

    try:
        image_bytes = load_image(image_path)
        update_icon(image_bytes)
    except Exception as e:
        print(f"ERROR: {e}")
        log_run(CITY, condition, description, temp, season, overlay_name, False, str(e))
        return

    log_run(CITY, condition, description, temp, season, overlay_name, True)

    msg = f"🖼️ **{CITY}**: {description}, {temp}°C | Season: {season} | Overlay: `{overlay_name}`"
    print(msg)
    post_to_discord(msg)


if __name__ == "__main__":
    main()
