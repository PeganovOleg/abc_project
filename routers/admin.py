from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from models import User, Setting
from auth import get_current_user, hash_password, generate_password, generate_username

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="templates")

def require_admin(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Только для администраторов")
    return user

@router.get("/", response_class=HTMLResponse)
def admin_index(request: Request, db: Session = Depends(get_db)):
    admin = require_admin(request, db)
    users = db.query(User).all()
    return templates.TemplateResponse(request, "admin/index.html", {"user": admin, "users": users})

@router.get("/users", response_class=HTMLResponse)
def admin_users(request: Request, db: Session = Depends(get_db)):
    admin = require_admin(request, db)
    users = db.query(User).order_by(User.created_at.desc()).all()
    return templates.TemplateResponse(request, "admin/users.html", {"user": admin, "users": users, "new_user": None})

@router.post("/users/create")
def create_user(request: Request, full_name: str = Form(...), db: Session = Depends(get_db)):
    require_admin(request, db)
    username = generate_username(full_name, db)
    password = generate_password()
    user = User(username=username, hashed_password=hash_password(password), full_name=full_name, role="parent")
    db.add(user)
    db.commit()
    db.refresh(user)
    users = db.query(User).order_by(User.created_at.desc()).all()
    return templates.TemplateResponse(request, "admin/users.html", {
        "user": db.query(User).filter(User.role == "admin").first(),
        "users": users, "new_user": {"username": username, "password": password, "full_name": full_name}
    })

@router.post("/users/{user_id}/toggle")
def toggle_user(user_id: int, request: Request, db: Session = Depends(get_db)):
    require_admin(request, db)
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(404)
    if u.role == "admin":
        raise HTTPException(400, "Нельзя заблокировать администратора")
    u.is_active = not u.is_active
    db.commit()
    return RedirectResponse("/admin/users", status_code=303)

@router.post("/users/{user_id}/delete")
def delete_user(user_id: int, request: Request, db: Session = Depends(get_db)):
    require_admin(request, db)
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(404)
    if u.role == "admin":
        raise HTTPException(400, "Нельзя удалить администратора")
    db.delete(u)
    db.commit()
    return RedirectResponse("/admin/users", status_code=303)

@router.get("/settings", response_class=HTMLResponse)
def admin_settings(request: Request, db: Session = Depends(get_db)):
    admin = require_admin(request, db)
    def get_setting(key):
        s = db.query(Setting).filter(Setting.key == key).first()
        return s.value if s else ""
    return templates.TemplateResponse(request, "admin/settings.html", {
        "user": admin,
        "yandex_api_key": get_setting("yandex_api_key"),
        "saved": False
    })

@router.post("/settings")
def save_settings(request: Request, yandex_api_key: str = Form(default=""), db: Session = Depends(get_db)):
    require_admin(request, db)
    # Обновляем только если передан непустой ключ
    if yandex_api_key.strip():
        s = db.query(Setting).filter(Setting.key == "yandex_api_key").first()
        if s:
            s.value = yandex_api_key.strip()
        else:
            db.add(Setting(key="yandex_api_key", value=yandex_api_key.strip()))
        db.commit()
    admin = db.query(User).filter(User.role == "admin").first()
    yandex_key_saved = db.query(Setting).filter(Setting.key == "yandex_api_key").first()
    return templates.TemplateResponse(request, "admin/settings.html", {
        "user": admin,
        "yandex_api_key": yandex_key_saved.value if yandex_key_saved else "",
        "saved": True
    })
