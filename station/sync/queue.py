import json
from pathlib import Path

WAL_FILE = Path("station/wal.log")

def load_unsynced():

    if not WAL_FILE.exists():
        return []

    events = []

    with open(WAL_FILE) as f:
        for line in f:

            event = json.loads(line)

            if not event.get("synced"):
                events.append(event)

    return events
