import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.pylocal', 'lib', 'python3.11', 'site-packages'))

from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import engine, get_db, Base
from models import User, Setting
from auth import hash_password, verify_password, create_token, get_current_user
from routers import admin, observations, speech, whisper, profile
from dotenv import load_dotenv

load_dotenv()
Base.metadata.create_all(bind=engine)

app = FastAPI(title="ABC Дневник")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(admin.router)
app.include_router(observations.router)
app.include_router(speech.router)
app.include_router(whisper.router)
app.include_router(profile.router)

def create_default_admin():
    from database import SessionLocal
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.role == "admin").first():
            db.add(User(username="admin", hashed_password=hash_password("admin123"),
                        full_name="Администратор", role="admin", is_active=True))
            db.commit()
            print("✅ Создан admin / admin123")
    finally:
        db.close()

create_default_admin()

@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    return RedirectResponse("/dashboard" if request.cookies.get("access_token") else "/login")

@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse(request, "login.html", {"error": None})

@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse(request, "login.html", {"error": "Неверный логин или пароль"})
    if not user.is_active:
        return templates.TemplateResponse(request, "login.html", {"error": "Аккаунт заблокирован"})
    response = RedirectResponse("/dashboard", status_code=303)
    response.set_cookie("access_token", create_token({"sub": user.username}), httponly=True, max_age=60*60*24*7)
    return response

@app.get("/logout")
def logout():
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie("access_token")
    return response
