import json
import uuid
from datetime import datetime
from pathlib import Path

WAL_FILE = Path("station/wal.log")

def append_event(event_type, payload):

    event = {
        "event_id": str(uuid.uuid4()),
        "event_type": event_type,
        "payload": payload,
        "created_at": datetime.utcnow().isoformat(),
        "synced": False
    }

    with open(WAL_FILE, "a") as f:
        f.write(json.dumps(event) + "\n")

    return event
