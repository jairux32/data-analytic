"""
API de autenticación y gestión de usuarios.

Endpoints para:
- Registro de usuarios (solo admin)
- Login con JWT
- Refresh de tokens
- Obtención de usuario actual
- Cambio de contraseña
- Gestión de usuarios (CRUD)
- Roles y permisos
- Auditoría
"""
import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response, JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core.security import (
    get_current_user,
    get_password_hash,
    require_permission,
    require_role,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    log_audit,
    get_user_permissions,
    ROLE_PERMISSIONS,
    PERMISSIONS,
    ROLES,
    ZONES,
)
from app.models.user import User
from app.models.audit_log import AuditLog
from app.schemas.auth import (
    TokenRequest,
    TokenResponse,
    UserResponse,
    UserCreateRequest,
    UserUpdateRequest,
    UserListResponse,
    UserFilterRequest,
    PasswordChangeRequest,
    MessageResponse,
    RoleResponse,
    PermissionsResponse,
    AuditLogResponse,
    AuditLogListResponse,
)

router = APIRouter(prefix="/api/auth", tags=["autenticación"])


# === Endpoints de autenticación ===

@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Endpoint de login.

    Autentica al usuario y retorna tokens JWT de acceso y refresh.
    Registra el intento de login en auditoría.
    """
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user or not verify_password(form_data.password, user.password_hash):
        # Registrar intento fallido
        log_audit(db, "login_failed", details=f"Email: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        log_audit(db, "login_inactive", user_id=user.id, details="Usuario inactivo")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo",
        )

    # Actualizar último login
    user.last_login = datetime.utcnow()
    db.commit()

    # Registrar login exitoso
    log_audit(db, "login_success", user_id=user.id, details=f"Rol: {user.role}, Zona: {user.zone}")

    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    response = JSONResponse(
        content={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    )
    # Establecer cookie HTTP-only para autenticación
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        max_age=30 * 60,  # 30 minutos
        path="/",
        secure=False,  # Cambiar a True en producción
    )
    return response


@router.post("/logout", response_model=MessageResponse)
def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Endpoint de logout."""
    log_audit(db, "logout", user_id=current_user.id)
    response = JSONResponse(content={"message": "Sesión cerrada exitosamente"})
    response.delete_cookie("access_token")
    return response


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    request: TokenRequest,
    db: Session = Depends(get_db)
):
    """Endpoint para refresh de token."""
    payload = decode_token(request.refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de refresco inválido",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de refresco inválido",
        )
    user = db.query(User).filter(User.id == int(str(user_id))).first()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado o inactivo",
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Obtiene información del usuario actual."""
    return current_user


@router.get("/me/permissions", response_model=PermissionsResponse)
def get_my_permissions(
    current_user: User = Depends(get_current_user)
):
    """Obtiene los permisos del usuario actual."""
    permissions = get_user_permissions(current_user.role)
    return PermissionsResponse(
        role=current_user.role,
        zone=current_user.zone,
        permissions=permissions,
        all_permissions=PERMISSIONS
    )


@router.put("/password", response_model=MessageResponse)
def change_password(
    request: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cambia la contraseña del usuario actual."""
    if not verify_password(request.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contraseña actual incorrecta",
        )

    current_user.password_hash = get_password_hash(request.new_password)
    db.commit()

    log_audit(db, "password_change", user_id=current_user.id, details="Cambio de contraseña")

    return MessageResponse(message="Contraseña actualizada exitosamente")


@router.get("/stats")
def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("ver_usuarios"))
):
    """Obtiene estadísticas rápidas del sistema."""
    from app.models.survey import Survey
    
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    total_surveys = db.query(Survey).count()
    
    # Distribución por rol
    role_dist = db.query(
        User.role, 
        func.count(User.id)
    ).group_by(User.role).all()
    by_role = {role: count for role, count in role_dist}
    
    # Distribución por zona
    zone_dist = db.query(
        User.zone, 
        func.count(User.id)
    ).group_by(User.zone).all()
    by_zone = {zone: count for zone, count in zone_dist}
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_surveys": total_surveys,
        "by_role": by_role,
        "by_zone": by_zone,
    }


@router.get("/me", response_model=UserResponse)
def get_my_profile(
    current_user: User = Depends(get_current_user)
):
    """Obtiene el perfil del usuario actual."""
    return current_user


@router.put("/me", response_model=UserResponse)
def update_my_profile(
    request: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualiza el perfil del usuario actual."""
    if request.full_name:
        current_user.full_name = request.full_name
    
    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)
    
    log_audit(db, "profile_update", user_id=current_user.id, details="Actualización de perfil")
    
    return current_user


# === Endpoints de gestión de usuarios ===

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    request: UserCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("gestionar_usuarios"))
):
    """Registra un nuevo usuario (requiere permiso gestionar_usuarios)."""
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado",
        )

    user = User(
        email=request.email,
        password_hash=get_password_hash(request.password),
        full_name=request.full_name,
        role=request.role,
        zone=request.zone,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    log_audit(db, "user_create", user_id=current_user.id, entity_type="user", entity_id=user.id,
              details=f"Creado usuario: {user.email}, Rol: {user.role}, Zona: {user.zone}")

    return user


@router.get("/users", response_model=UserListResponse)
def list_users(
    page: int = 1,
    per_page: int = 20,
    role: Optional[str] = None,
    zone: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("ver_usuarios"))
):
    """Lista usuarios con filtros (requiere permiso ver_usuarios)."""
    query = db.query(User).order_by(User.created_at.desc())

    if role:
        query = query.filter(User.role == role)
    if zone:
        query = query.filter(User.zone == zone)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    if search:
        query = query.filter(
            (User.email.ilike(f"%{search}%")) |
            (User.full_name.ilike(f"%{search}%"))
        )

    total = query.count()
    offset = (page - 1) * per_page
    users = query.offset(offset).limit(per_page).all()

    return UserListResponse(
        total=total,
        page=page,
        per_page=per_page,
        items=[UserResponse.model_validate(u) for u in users],
    )


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("ver_usuarios"))
):
    """Obtiene un usuario por ID (requiere permiso ver_usuarios)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )
    return user


@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    request: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("gestionar_usuarios"))
):
    """Actualiza un usuario (requiere permiso gestionar_usuarios)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    changes = []

    if request.email and request.email != user.email:
        existing = db.query(User).filter(User.email == request.email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está en uso",
            )
        changes.append(f"email: {user.email} -> {request.email}")
        user.email = request.email

    if request.full_name and request.full_name != user.full_name:
        changes.append(f"nombre: {user.full_name} -> {request.full_name}")
        user.full_name = request.full_name

    if request.role and request.role != user.role:
        changes.append(f"rol: {user.role} -> {request.role}")
        user.role = request.role

    if request.zone and request.zone != user.zone:
        changes.append(f"zona: {user.zone} -> {request.zone}")
        user.zone = request.zone

    if request.is_active is not None and request.is_active != user.is_active:
        changes.append(f"activo: {user.is_active} -> {request.is_active}")
        user.is_active = request.is_active

    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    if changes:
        log_audit(db, "user_update", user_id=current_user.id, entity_type="user", entity_id=user.id,
                  details=f"Cambios: {', '.join(changes)}")

    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("gestionar_usuarios"))
):
    """Desactiva un usuario (requiere permiso gestionar_usuarios)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes desactivar tu propia cuenta",
        )

    user.is_active = False
    user.updated_at = datetime.utcnow()
    db.commit()

    log_audit(db, "user_deactivate", user_id=current_user.id, entity_type="user", entity_id=user.id,
              details=f"Desactivado usuario: {user.email}")

    return None


@router.post("/users/{user_id}/activate", response_model=UserResponse)
def activate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("gestionar_usuarios"))
):
    """Activa un usuario (requiere permiso gestionar_usuarios)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    user.is_active = True
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    log_audit(db, "user_activate", user_id=current_user.id, entity_type="user", entity_id=user.id,
              details=f"Activado usuario: {user.email}")

    return user


@router.post("/users/{user_id}/reset-password", response_model=MessageResponse)
def reset_user_password(
    user_id: int,
    new_password: str = Query(..., min_length=6),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("gestionar_usuarios"))
):
    """Resetea la contraseña de un usuario (requiere permiso gestionar_usuarios)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    user.password_hash = get_password_hash(new_password)
    user.updated_at = datetime.utcnow()
    db.commit()

    log_audit(db, "password_reset", user_id=current_user.id, entity_type="user", entity_id=user.id,
              details=f"Reseteada contraseña de: {user.email}")

    return MessageResponse(message="Contraseña reseteada exitosamente")


# === Endpoints de roles y permisos ===

@router.get("/roles", response_model=list[RoleResponse])
def list_roles(
    current_user: User = Depends(require_permission("ver_usuarios"))
):
    """Lista todos los roles disponibles con sus permisos."""
    return [
        RoleResponse(
            name=role,
            description=f"Rol de {role}",
            permissions=ROLE_PERMISSIONS.get(role, [])
        )
        for role in ROLES
    ]


@router.get("/roles/{role_name}/permissions", response_model=list[str])
def get_role_permissions(
    role_name: str,
    current_user: User = Depends(require_permission("ver_usuarios"))
):
    """Obtiene los permisos de un rol específico."""
    if role_name not in ROLES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rol no encontrado",
        )
    return ROLE_PERMISSIONS.get(role_name, [])


@router.get("/permissions", response_model=dict)
def list_all_permissions(
    current_user: User = Depends(require_permission("ver_usuarios"))
):
    """Lista todos los permisos disponibles."""
    return PERMISSIONS


# === Endpoints de auditoría ===

@router.get("/audit", response_model=AuditLogListResponse)
def list_audit_logs(
    page: int = 1,
    per_page: int = 20,
    action: Optional[str] = None,
    user_id: Optional[int] = None,
    entity_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("gestionar_usuarios"))
):
    """Lista registros de auditoría (requiere permiso gestionar_usuarios)."""
    query = db.query(AuditLog).order_by(AuditLog.created_at.desc())

    if action:
        query = query.filter(AuditLog.action == action)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)

    total = query.count()
    offset = (page - 1) * per_page
    logs = query.offset(offset).limit(per_page).all()

    return AuditLogListResponse(
        total=total,
        page=page,
        per_page=per_page,
        items=[AuditLogResponse.model_validate(l) for l in logs],
    )


@router.get("/audit/user/{user_id}", response_model=AuditLogListResponse)
def get_user_audit_logs(
    user_id: int,
    page: int = 1,
    per_page: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("gestionar_usuarios"))
):
    """Obtiene el historial de acciones de un usuario específico."""
    query = db.query(AuditLog).filter(AuditLog.user_id == user_id).order_by(AuditLog.created_at.desc())

    total = query.count()
    offset = (page - 1) * per_page
    logs = query.offset(offset).limit(per_page).all()

    return AuditLogListResponse(
        total=total,
        page=page,
        per_page=per_page,
        items=[AuditLogResponse.model_validate(l) for l in logs],
    )
