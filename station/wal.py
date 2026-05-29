from pathlib import Path
import json

QUEUE_FILE = Path("station_queue.jsonl")


def write_event(event: dict):
    with open(QUEUE_FILE, "a") as f:
        f.write(json.dumps(event) + "\n")


def flush_queue():
    if not QUEUE_FILE.exists():
        return {"events": []}

    events = []

    with open(QUEUE_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                events.append(json.loads(line))

    QUEUE_FILE.unlink(missing_ok=True)

    return {
        "events": events,
        "count": len(events)
    }