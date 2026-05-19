from fastapi import APIRouter, Depends
from server.storage.db import get_conn
from server.auth.dependencies import require_user
from psycopg2.extras import RealDictCursor
import json

router = APIRouter(prefix="/animals")


# -------------------------
# CREATE
# -------------------------
@router.post("/")
def create_animal(
    data: dict,
    user=Depends(require_user)
):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)

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

    animal_id = cur.fetchone()["id"]

    conn.commit()
    conn.close()

    return {"id": animal_id}


# -------------------------
# LIST
# -------------------------
@router.get("/")
def list_animals(
    user=Depends(require_user)
):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT id, tag_id, species, status FROM animals")
    rows = cur.fetchall()

    conn.close()

    return rows
