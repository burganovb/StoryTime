from __future__ import annotations

import json
import re
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "stories.db"
STORAGE_DIR = BASE_DIR / "storage"
AUDIO_DIR = STORAGE_DIR / "audio"

AUDIO_DIR.mkdir(parents=True, exist_ok=True)

BANNED_TERMS = {
    "gun",
    "knife",
    "blood",
    "gore",
    "weapon",
    "kill",
    "murder",
    "sex",
    "sexual",
}

app = FastAPI(title="StoryTime MVP")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS stories (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                audio_url TEXT NOT NULL,
                transcript TEXT NOT NULL,
                panels_json TEXT NOT NULL
            )
            """
        )
        conn.commit()


def safe_text(value: str) -> str:
    tokens = re.split(r"(\W+)", value)
    cleaned: list[str] = []
    for token in tokens:
        if token.lower() in BANNED_TERMS:
            cleaned.append("*")
        else:
            cleaned.append(token)
    return "".join(cleaned)


def generate_panel_plan(transcript: str) -> dict[str, Any]:
    hero = "Luna the Explorer"
    setting = "a sunny park"
    problem = "a lost kite"
    action = "searching with a helpful dog"
    outcome = "finding the kite and celebrating"

    panels = [
        {
            "caption": f"{hero} arrives in {setting}.",
            "image_prompt": f"{hero} in {setting}, bright colors, friendly style",
        },
        {
            "caption": f"A problem appears: {problem}.",
            "image_prompt": f"{hero} noticing {problem}, gentle mood",
        },
        {
            "caption": f"{hero} takes action by {action}.",
            "image_prompt": f"{hero} {action}, playful scene",
        },
        {
            "caption": f"The outcome is {outcome}.",
            "image_prompt": f"{hero} {outcome}, joyful atmosphere",
        },
    ]

    return {
        "title": safe_text("A Day of Adventure"),
        "characters": [{"name": hero, "traits": "curious, brave, kind"}],
        "panels": panels,
    }


def build_panels(panel_plan: dict[str, Any]) -> list[dict[str, str]]:
    panels: list[dict[str, str]] = []
    for index, panel in enumerate(panel_plan["panels"], start=1):
        caption = safe_text(panel["caption"])
        image_prompt = safe_text(panel["image_prompt"])
        placeholder = (
            "https://placehold.co/600x400/png"
            f"?text=Panel+{index}"
        )
        panels.append({
            "image_url": placeholder,
            "caption_text": caption,
            "image_prompt": image_prompt,
        })
    return panels


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/api/stories")
def list_stories() -> list[dict[str, Any]]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT id, title, created_at FROM stories ORDER BY created_at DESC"
        ).fetchall()
    return [dict(row) for row in rows]


@app.get("/api/stories/{story_id}")
def get_story(story_id: str) -> dict[str, Any]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM stories WHERE id = ?", (story_id,)
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Story not found")
    story = dict(row)
    story["panels"] = json.loads(story.pop("panels_json"))
    return story


@app.post("/api/stories")
async def create_story(
    audio: UploadFile = File(...),
    title: Optional[str] = Form(None),
) -> dict[str, Any]:
    story_id = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat()

    audio_path = AUDIO_DIR / f"{story_id}_{audio.filename}"
    with audio_path.open("wb") as handle:
        content = await audio.read()
        handle.write(content)

    transcript = safe_text(
        "".join(["A kid tells a story about a brave friend and a sunny day."])
    )
    panel_plan = generate_panel_plan(transcript)
    panels = build_panels(panel_plan)

    story_title = safe_text(title or panel_plan["title"])
    audio_url = f"/audio/{audio_path.name}"

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO stories (id, title, created_at, audio_url, transcript, panels_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                story_id,
                story_title,
                created_at,
                audio_url,
                transcript,
                json.dumps(panels),
            ),
        )
        conn.commit()

    return {
        "id": story_id,
        "title": story_title,
        "created_at": created_at,
        "audio_url": audio_url,
        "transcript": transcript,
        "panels": panels,
    }


app.mount("/", StaticFiles(directory=str(BASE_DIR / "static"), html=True), name="static")


@app.get("/audio/{filename}")
def get_audio(filename: str) -> FileResponse:
    audio_path = AUDIO_DIR / filename
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Audio not found")
    return FileResponse(audio_path)
