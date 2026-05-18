from fastapi import APIRouter
from server.db import get_conn
import json

router = APIRouter(prefix="/events")

@router.post("/")
def create_event(data: dict):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO events (animal_id, station_id, event_type, payload)
        VALUES (%s, %s, %s, %s)
        RETURNING id
        """,
        (
            data.get("animal_id"),
            data.get("station_id"),
            data["event_type"],
            json.dumps(data.get("payload", {}))
        )
    )

    event_id = cur.fetchone()[0]
    conn.commit()
    conn.close()

    return {"id": event_id}


@router.get("/")
def list_events():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT id, event_type FROM events ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()

    return [{"id": r[0], "type": r[1]} for r in rows]