import time
import json
from station.sync.queue import load_unsynced
from station.sync.transport import send_event
from pathlib import Path

WAL_FILE = Path("station/wal.log")

def mark_synced(event_id):

    lines = []

    with open(WAL_FILE) as f:
        for line in f:

            event = json.loads(line)

            if event["event_id"] == event_id:
                event["synced"] = True

            lines.append(json.dumps(event))

    with open(WAL_FILE, "w") as f:
        f.write("\n".join(lines) + "\n")


def sync_loop():

    while True:

        events = load_unsynced()

        for event in events:

            try:

                ok = send_event(event)

                if ok:
                    mark_synced(event["event_id"])

            except Exception as e:
                print("SYNC ERROR:", e)

        time.sleep(30)
