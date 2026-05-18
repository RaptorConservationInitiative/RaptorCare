from fastapi import APIRouter
from server.db import get_conn

router = APIRouter(prefix="/stations")

@router.post("/")
def create_station(data: dict):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO stations (name, country, location_lat, location_lon)
        VALUES (%s, %s, %s, %s)
        RETURNING id
        """,
        (
            data["name"],
            data.get("country"),
            data.get("lat"),
            data.get("lon")
        )
    )

    station_id = cur.fetchone()[0]
    conn.commit()
    conn.close()

    return {"id": station_id}


@router.get("/")
def list_stations():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT id, name, country FROM stations")
    rows = cur.fetchall()
    conn.close()

    return [{"id": r[0], "name": r[1], "country": r[2]} for r in rows]