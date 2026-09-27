from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import get_db
from models import Child
from auth import get_current_user

router = APIRouter(prefix="/api/profile")

@router.get("/children")
def get_children(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    children = db.query(Child).filter(Child.user_id == user.id).all()
    return [{"id": c.id, "name": c.name} for c in children]

@router.post("/children/add")
def add_child(request: Request, name: str = Form(...), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    count = db.query(Child).filter(Child.user_id == user.id).count()
    if count >= 5:
        return JSONResponse({"error": "Максимум 5 детей"}, status_code=400)
    if db.query(Child).filter(Child.user_id == user.id, Child.name == name.strip()).first():
        return JSONResponse({"error": "Уже есть"}, status_code=400)
    child = Child(user_id=user.id, name=name.strip())
    db.add(child)
    db.commit()
    return {"id": child.id, "name": child.name}

@router.post("/children/delete/{child_id}")
def delete_child(child_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    child = db.query(Child).filter(Child.id == child_id, Child.user_id == user.id).first()
    if child:
        db.delete(child)
        db.commit()
    return {"ok": True}
