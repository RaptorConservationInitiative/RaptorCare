from fastapi import Request, HTTPException
from server.auth.jwt import verify_token

def require_user(request: Request):

    token = request.cookies.get("token")

    if not token:
        raise HTTPException(status_code=401, detail="Missing token")

    payload = verify_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    return payload
