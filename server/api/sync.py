from fastapi import APIRouter
from server.storage.db import get_conn
import json

router = APIRouter(prefix="/sync")

@router.post("/event")
def sync_event(data: dict):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id FROM sync_events
        WHERE event_id = %s
        """,
        (data["event_id"],)
    )

    existing = cur.fetchone()

    if existing:
        conn.close()
        return {"status": "duplicate"}

    cur.execute(
        """
        INSERT INTO sync_events
        (event_id, event_type, payload)
        VALUES (%s, %s, %s)
        """,
        (
            data["event_id"],
            data["event_type"],
            json.dumps(data["payload"])
        )
    )

    conn.commit()
    conn.close()

    return {"status": "ok"}
