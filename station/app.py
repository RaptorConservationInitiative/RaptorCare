from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from station.wal import write_event, flush_queue

app = FastAPI()

# =========================================================
# UI
# =========================================================

BASE_DIR = Path(__file__).resolve().parent
UI_DIR = BASE_DIR / "static_ui"

app.mount(
    "/",
    StaticFiles(directory=str(UI_DIR), html=True),
    name="ui"
)

# =========================================================
# API
# =========================================================

@app.post("/api/event")
def event(event: dict):

    write_event(event)

    return {"stored": True}


@app.post("/api/sync")
def sync():
    return flush_queue()