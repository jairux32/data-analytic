"""
Vistas HTML de la aplicación.

Endpoints que renderizan templates HTML usando Jinja2.
"""
import json
import os

from typing import Optional

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.core.security import get_current_user
from app.models.user import User

router = APIRouter(tags=["vistas"])

# Configurar templates
templates = Jinja2Templates(directory="app/templates")


def user_to_dict(user: Optional[User]) -> dict:
    """Convierte el usuario a un diccionario serializable."""
    if not user:
        return {}
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "zone": user.zone,
        "is_active": user.is_active
    }


from sqlalchemy.orm import Session
from app.core.database import get_db

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, db: Session = Depends(get_db)):
    """Página de login con verificación de primer uso."""
    # Verificar si es el primer uso (no hay usuarios)
    if db.query(User).count() == 0:
        return RedirectResponse(url="/setup", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/setup", response_class=HTMLResponse)
def setup_page(request: Request, db: Session = Depends(get_db)):
    """Página de configuración inicial (Primer Uso)."""
    # Si ya hay usuarios, bloquear acceso
    if db.query(User).count() > 0:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("setup.html", {"request": request})


@router.get("/", response_class=HTMLResponse)
def index(request: Request, current_user: Optional[User] = Depends(get_current_user), db: Session = Depends(get_db)):
    """Página principal - redirige al dashboard o al setup inicial."""
    if db.query(User).count() == 0:
        return RedirectResponse(url="/setup", status_code=302)
        
    return templates.TemplateResponse("index.html", {
        "request": request,
        "user": user_to_dict(current_user),
        "user_json": json.dumps(user_to_dict(current_user))
    })


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request, current_user: Optional[User] = Depends(get_current_user)):
    """Página del dashboard analítico."""
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user_to_dict(current_user),
        "user_json": json.dumps(user_to_dict(current_user))
    })


@router.get("/maps", response_class=HTMLResponse)
def maps_page(request: Request, current_user: Optional[User] = Depends(get_current_user)):
    """Página de mapas geoespaciales."""
    return templates.TemplateResponse("maps.html", {
        "request": request,
        "user": user_to_dict(current_user),
        "user_json": json.dumps(user_to_dict(current_user))
    })


@router.get("/tables", response_class=HTMLResponse)
def tables_page(request: Request, current_user: Optional[User] = Depends(get_current_user)):
    """Página de tablas de datos."""
    return templates.TemplateResponse("tables.html", {
        "request": request,
        "user": user_to_dict(current_user),
        "user_json": json.dumps(user_to_dict(current_user))
    })


@router.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request, current_user: Optional[User] = Depends(get_current_user)):
    """Página de administración."""
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "user": user_to_dict(current_user),
        "user_json": json.dumps(user_to_dict(current_user))
    })


@router.get("/profile", response_class=HTMLResponse)
def profile_page(request: Request, current_user: Optional[User] = Depends(get_current_user)):
    """Página de perfil de usuario."""
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user": user_to_dict(current_user),
        "user_json": json.dumps(user_to_dict(current_user))
    })
