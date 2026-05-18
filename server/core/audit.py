from server.state import AUDIT
import hashlib
import json

LAST_HASH = "GENESIS"


def append_audit(event):

    global LAST_HASH

    payload = json.dumps(event, sort_keys=True)

    event_hash = hashlib.sha256(payload.encode()).hexdigest()

    AUDIT.append({
        "event": event,
        "hash": event_hash,
        "prev_hash": LAST_HASH
    })

    LAST_HASH = event_hash