from fastapi import Header, HTTPException
from server.auth.jwt import verify_token

def require_user(authorization: str = Header(None)):

    if not authorization:
        raise HTTPException(401, "Missing token")

    token = authorization.replace("Bearer ", "")

    try:
        return verify_token(token)

    except Exception:
        raise HTTPException(401, "Invalid token")
