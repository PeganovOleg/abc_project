from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_
from database import get_db
from models import Observation, User
from auth import get_current_user
from pdf_gen import generate_pdf
from datetime import datetime
import io, re, urllib.parse

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, q: str = "", db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    search = q.strip().lower()

    if user.role in ("admin", "superadmin"):
        # Подгружаем все наблюдения + автора
        all_obs = (
            db.query(Observation, User)
            .join(User, Observation.user_id == User.id)
            .order_by(Observation.created_at.desc())
            .all()
        )
        if search:
            result = []
            for obs, author in all_obs:
                if (search in obs.child_name.lower() or
                    search in (author.full_name or "").lower() or
                    search in (author.username or "").lower()):
                    obs._author = author
                    result.append(obs)
        else:
            result = []
            for obs, author in all_obs:
                obs._author = author
                result.append(obs)
        observations = result
    else:
        all_obs = (
            db.query(Observation)
            .filter(Observation.user_id == user.id)
            .order_by(Observation.created_at.desc())
            .all()
        )
        if search:
            observations = [o for o in all_obs if search in o.child_name.lower()]
        else:
            observations = all_obs

    return templates.TemplateResponse(request, "dashboard.html", {
        "user": user,
        "observations": observations,
        "q": q,
    })

@router.get("/observations/new", response_class=HTMLResponse)
def new_observation_form(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    return templates.TemplateResponse(request, "new_observation.html", {"user": user})

@router.post("/observations/new")
def create_observation(
    request: Request,
    child_name: str = Form(...),
    obs_date: str = Form(...),
    obs_time: str = Form(...),
    location: str = Form(...),
    antecedent: str = Form(...),
    behavior: str = Form(...),
    consequence: str = Form(...),
    function: str = Form(""),
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    obs = Observation(
        user_id=user.id,
        child_name=child_name,
        observer_name=user.full_name,
        obs_date=obs_date,
        obs_time=obs_time,
        location=location,
        antecedent=antecedent,
        behavior=behavior,
        consequence=consequence,
        function=function
    )
    db.add(obs)
    db.commit()
    return RedirectResponse("/dashboard", status_code=303)

@router.get("/observations/{obs_id}/pdf")
def download_pdf(obs_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    obs = db.query(Observation).filter(Observation.id == obs_id).first()
    if not obs:
        raise HTTPException(404)
    if obs.user_id != user.id and user.role not in ("admin", "superadmin"):
        raise HTTPException(403)
    pdf_bytes = generate_pdf(obs)
    safe_user = re.sub(r'[^\w\s-]', '', obs.observer_name or "user").strip().replace(' ', '_')
    safe_child = re.sub(r'[^\w\s-]', '', obs.child_name).strip().replace(' ', '_')
    dt = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"ABC_{safe_user}_{safe_child}_{dt}.pdf"
    encoded_filename = urllib.parse.quote(filename)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
    )

@router.post("/observations/{obs_id}/delete")
def delete_observation(obs_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    obs = db.query(Observation).filter(Observation.id == obs_id).first()
    if not obs:
        raise HTTPException(404)
    if obs.user_id != user.id and user.role not in ("admin", "superadmin"):
        raise HTTPException(403)
    db.delete(obs)
    db.commit()
    return RedirectResponse("/dashboard", status_code=303)

@router.get("/observations/{obs_id}/edit", response_class=HTMLResponse)
def edit_observation_form(obs_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    obs = db.query(Observation).filter(Observation.id == obs_id).first()
    if not obs:
        raise HTTPException(404)
    if obs.user_id != user.id and user.role not in ("admin", "superadmin"):
        raise HTTPException(403)
    return templates.TemplateResponse(request, "edit_observation.html", {"user": user, "obs": obs})

@router.post("/observations/{obs_id}/edit")
def edit_observation(
    obs_id: int,
    request: Request,
    child_name: str = Form(...),
    obs_date: str = Form(...),
    obs_time: str = Form(...),
    location: str = Form(...),
    antecedent: str = Form(...),
    behavior: str = Form(...),
    consequence: str = Form(...),
    function: str = Form(""),
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    obs = db.query(Observation).filter(Observation.id == obs_id).first()
    if not obs:
        raise HTTPException(404)
    if obs.user_id != user.id and user.role not in ("admin", "superadmin"):
        raise HTTPException(403)
    obs.child_name = child_name
    obs.obs_date = obs_date
    obs.obs_time = obs_time
    obs.location = location
    obs.antecedent = antecedent
    obs.behavior = behavior
    obs.consequence = consequence
    obs.function = function
    db.commit()
    return RedirectResponse("/dashboard", status_code=303)

