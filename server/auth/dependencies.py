from fastapi import Request, HTTPException, Header
from server.auth.jwt import verify_token
"""
def require_user(request: Request):

    token = request.cookies.get("token")

    if not token:
        raise HTTPException(status_code=401, detail="Missing token")

    payload = verify_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    return payload
"""



def require_user(
    request: Request,
    authorization: str | None = Header(default=None)
):
    token = None

    # 1. Bearer Token (optional)
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]

    # 2. Cookie fallback (dein aktueller Flow)
    if not token:
        token = request.cookies.get("token")

    if not token:
        raise HTTPException(status_code=401, detail="Missing token")

    try:
        payload = verify_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    return payload
