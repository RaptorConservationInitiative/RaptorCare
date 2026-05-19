from fastapi import APIRouter, HTTPException
from server.storage.db import get_conn
from server.auth.passwords import verify_password
from server.auth.jwt import create_token

router = APIRouter(prefix="/auth")

@router.post("/login")
def login(data: dict):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, password_hash, role
        FROM users
        WHERE username = %s
        """,
        (data["username"],)
    )

    user = cur.fetchone()
    conn.close()

    if not user:
        raise HTTPException(401, "Invalid credentials")

    if not verify_password(
        data["password"],
        user[1]
    ):
        raise HTTPException(401, "Invalid credentials")

    token = create_token({
        "user_id": user["id"],
        "role": user["role"]
    })

    return {"token": token}
