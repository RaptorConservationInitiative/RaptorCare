from fastapi import Request, HTTPException
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

    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]

    if not token:
        token = request.cookies.get("token")

    if not token:
        raise HTTPException(status_code=401, detail="Missing token")

    return token
