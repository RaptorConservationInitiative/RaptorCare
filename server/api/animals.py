from fastapi import APIRouter
from server.storage.db import get_conn
import json
from fastapi import Depends
from server.auth.dependencies import require_user

router = APIRouter(prefix="/animals")

@router.post("/")
def create_animal(data: dict):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO animals (tag_id, species, status, station_id, metadata)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
        """,
        (
            data.get("tag_id"),
            data.get("species"),
            data.get("status", "intake"),
            data.get("station_id"),
            json.dumps(data.get("metadata", {}))
        )
    )

    animal_id = cur.fetchone()[0]
    conn.commit()
    conn.close()

    return {"id": animal_id}


@router.get("/")
def list_animals():
    user=Depends(require_user)
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT id, tag_id, species, status FROM animals")
    rows = cur.fetchall()
    conn.close()

    return [
        {"id": r[0], "tag_id": r[1], "species": r[2], "status": r[3]}
        for r in rows
    ]
