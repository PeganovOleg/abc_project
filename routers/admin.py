from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from models import User, Setting
from auth import get_current_user, hash_password, generate_password, generate_username
import os, glob

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="templates")

def require_admin(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user.role not in ("admin", "superadmin"):
        raise HTTPException(status_code=403, detail="Только для администраторов")
    return user

def require_superadmin(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user.role != "superadmin":
        raise HTTPException(status_code=403, detail="Только для суперадминистратора")
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
    admin = require_admin(request, db)
    users = db.query(User).order_by(User.created_at.desc()).all()
    return templates.TemplateResponse(request, "admin/users.html", {
        "user": admin,
        "users": users, "new_user": {"username": username, "password": password, "full_name": full_name}
    })


@router.get("/users/{user_id}/edit", response_class=HTMLResponse)
def edit_user_form(user_id: int, request: Request, db: Session = Depends(get_db)):
    current = require_admin(request, db)
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse(request, "admin/edit_user.html", {"user": current, "edit_user": u})

@router.post("/users/{user_id}/edit")
def edit_user(user_id: int, request: Request,
              full_name: str = Form(...),
              observer_role: str = Form(default=""),
              db: Session = Depends(get_db)):
    current = require_admin(request, db)
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404)
    u.full_name = full_name.strip()
    u.observer_role = observer_role.strip() or None
    db.commit()
    return RedirectResponse("/admin/users", status_code=303)

@router.post("/users/{user_id}/toggle")
def toggle_user(user_id: int, request: Request, db: Session = Depends(get_db)):
    admin = require_admin(request, db)
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(404)
    if u.role in ("admin", "superadmin") and admin.role != "superadmin":
        raise HTTPException(400, "Недостаточно прав")
    u.is_active = not u.is_active
    db.commit()
    return RedirectResponse("/admin/users", status_code=303)

@router.post("/users/{user_id}/delete")
def delete_user(user_id: int, request: Request, db: Session = Depends(get_db)):
    admin = require_admin(request, db)
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(404)
    if u.role in ("admin", "superadmin") and admin.role != "superadmin":
        raise HTTPException(400, "Недостаточно прав")
    if u.id == admin.id:
        raise HTTPException(400, "Нельзя удалить себя")
    db.delete(u)
    db.commit()
    return RedirectResponse("/admin/users", status_code=303)

@router.post("/users/{user_id}/reset-password")
def reset_password(user_id: int, request: Request, new_password: str = Form(...), db: Session = Depends(get_db)):
    admin = require_admin(request, db)
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(404)
    # Менять пароль admin может только superadmin
    if u.role in ("admin", "superadmin") and admin.role != "superadmin":
        raise HTTPException(403, "Только суперадмин может менять пароли администраторов")
    u.hashed_password = hash_password(new_password)
    db.commit()
    users = db.query(User).order_by(User.created_at.desc()).all()
    return templates.TemplateResponse(request, "admin/users.html", {
        "user": admin, "users": users, "new_user": None,
        "password_changed": u.full_name
    })

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
    if yandex_api_key.strip():
        s = db.query(Setting).filter(Setting.key == "yandex_api_key").first()
        if s:
            s.value = yandex_api_key.strip()
        else:
            db.add(Setting(key="yandex_api_key", value=yandex_api_key.strip()))
        db.commit()
    admin = require_admin(request, db)
    yandex_key_saved = db.query(Setting).filter(Setting.key == "yandex_api_key").first()
    return templates.TemplateResponse(request, "admin/settings.html", {
        "user": admin,
        "yandex_api_key": yandex_key_saved.value if yandex_key_saved else "",
        "saved": True
    })

@router.get("/backup/download")
def download_backup(request: Request, db: Session = Depends(get_db)):
    require_superadmin(request, db)
    # Ищем последний бэкап
    backups = sorted(glob.glob(os.path.expanduser("~/backups/abc_diary_*.db")), reverse=True)
    if backups:
        path = backups[0]
    else:
        # Если бэкапов нет — отдаём текущую БД
        path = os.path.expanduser("~/abc-diary/abc_diary.db")
    if not os.path.exists(path):
        raise HTTPException(404, "Файл базы данных не найден")
    filename = os.path.basename(path)
    return FileResponse(path, media_type="application/octet-stream", filename=filename)

@router.post("/users/{user_id}/auto-reset")
def auto_reset_password(user_id: int, request: Request, db: Session = Depends(get_db)):
    admin = require_admin(request, db)
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(404)
    if u.role in ("admin", "superadmin") and admin.role != "superadmin":
        raise HTTPException(403, "Только суперадмин может сбрасывать пароли администраторов")
    new_password = generate_password()
    u.hashed_password = hash_password(new_password)
    db.commit()
    users = db.query(User).order_by(User.created_at.desc()).all()
    return templates.TemplateResponse(request, "admin/users.html", {
        "user": admin, "users": users, "new_user": None,
        "password_reset": {"full_name": u.full_name, "username": u.username, "password": new_password}
    })
