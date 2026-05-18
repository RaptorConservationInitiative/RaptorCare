from fastapi import FastAPI
from station.wal import write_event, flush_queue

app = FastAPI()

@app.post("/event")
def event(event: dict):

    write_event(event)

    return {"stored": True}

@app.post("/sync")
def sync():
    return flush_queue()