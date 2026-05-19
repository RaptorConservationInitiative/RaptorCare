from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from server.auth.jwt import create_token
from server.storage.db import get_conn
from psycopg2.extras import RealDictCursor
import os

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "web/templates"))

# -------------------
# LOGIN PAGE
# -------------------
@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})



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

    return {
        "access_token": token,
        "token_type": "bearer"
    }


# -------------------
# DASHBOARD
# -------------------
@router.get("/dashboard")
def dashboard(request: Request):

    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT id, tag_id, species FROM animals")
    animals = cur.fetchall()

    conn.close()

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "animals": animals
        }
    )
