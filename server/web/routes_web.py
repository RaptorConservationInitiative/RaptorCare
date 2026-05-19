from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from server.auth.jwt import create_token
from server.storage.db import get_conn
from psycopg2.extras import RealDictCursor
import os
from fastapi import Depends
from server.auth.dependencies import require_user


router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "web/templates"))

# -------------------
# LOGIN PAGE
# -------------------
@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(
        request,
        "login.html",
        {}
    )


@router.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "SELECT id, username, password_hash FROM users WHERE username = %s",
        (username,)
    )

    user = cur.fetchone()
    conn.close()

    if not user:
        return {"error": "invalid credentials"}

    # TODO: password check (abhängig von deinem hashing)
    token = create_token({"user_id": user[0]})

    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(key="token", value=token, httponly=True)
    return response


# -------------------
# DASHBOARD
# -------------------
@router.get("/dashboard")
def dashboard(request: Request, user=Depends(require_user)):

    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT id, tag_id, species FROM animals")
    animals = cur.fetchall()

    conn.close()

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "animals": animals
        }
    )
