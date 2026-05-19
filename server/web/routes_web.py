from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from server.auth.jwt import create_token
from server.storage.db import get_conn

router = APIRouter()
templates = Jinja2Templates(directory="server/web/templates")


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
        "SELECT id, password_hash, role FROM users WHERE username=%s",
        (username,)
    )

    user = cur.fetchone()
    conn.close()

    if not user:
        return RedirectResponse("/login", status_code=302)

    # NOTE: password check kommt aus Auth Phase (vereinfachen wir hier)
    token = create_token({"user_id": user[0], "role": user[2]})

    response = RedirectResponse("/dashboard", status_code=302)
    response.set_cookie("token", token)

    return response


# -------------------
# DASHBOARD
# -------------------
@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT id, name, species FROM animals")
    animals = cur.fetchall()

    conn.close()

    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "animals": animals}
    )
