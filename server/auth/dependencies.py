from fastapi import Header, HTTPException
from server.auth.jwt import verify_token

from fastapi import Request, HTTPException

def require_user(request: Request):
    token = request.cookies.get("token")

    if not token:
        raise HTTPException(status_code=401, detail="Missing token")

    return token
