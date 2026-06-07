# ============================================================
# routers/auth.py
# CU1: Gestionar Autenticación
#   POST /auth/login   → Inicia sesión, devuelve JWT
#   POST /auth/logout  → Cierra sesión (invalida el token)
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from uuid import UUID
from typing import Optional
from datetime import datetime, timedelta
from app.database import get_db
from app.models.usuario import Usuario, TipoRol # 👈 Añadido TipoRol
from app.models.taller import Taller
from app.schemas.usuario import LoginRequest, TokenResponse
from app.utils.security import verify_password, create_access_token, decode_access_token

router = APIRouter(prefix="/auth", tags=["CU1 - Autenticación"])

# Esquema OAuth2 para leer el token del header Authorization
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# -------------------------------------------------------
# POST /auth/login
# Recibe email y contraseña, devuelve un token JWT
# -------------------------------------------------------
@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):

    usuario = db.query(Usuario).filter(Usuario.email == request.email).first()

    if not usuario or not verify_password(request.password, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas"
        )
    id_taller_encontrado = None
    if usuario.rol == TipoRol.taller:
        taller = db.query(Taller).filter(Taller.dueño_id == usuario.id_usuario).first()
        if taller:
            id_taller_encontrado = taller.id_taller

    token = create_access_token(data={
        "sub": usuario.email,
        "rol": usuario.rol,
        "tenant_id": str(usuario.tenant_id) if usuario.tenant_id else None
    })

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        rol=usuario.rol,
        nombre=usuario.nombre,
        id_usuario=usuario.id_usuario,  # 👈 ESTO ES LO QUE FALTA
        id_taller=id_taller_encontrado
    )


# -------------------------------------------------------
# POST /auth/logout
# El cliente debe eliminar el token de su lado
# Aquí validamos que el token sea válido antes de cerrar
# -------------------------------------------------------
@router.post("/logout")
def logout(token: str = Depends(oauth2_scheme)):

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o ya expirado"
        )

    return {"message": "Sesión cerrada correctamente"}


# -------------------------------------------------------
# Dependencia reutilizable: obtener el usuario autenticado
# Se importa en otros routers para proteger endpoints
# -------------------------------------------------------
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Usuario:

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado"
        )

    usuario = db.query(Usuario).filter(Usuario.email == payload.get("sub")).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    return usuario


# -------------------------------------------------------
# POST /auth/registrar-tenant
# Registro B2B de una nueva empresa SaaS
# -------------------------------------------------------
from app.schemas.saas import TenantRegisterRequest
from app.models.saas import Tenant, Suscripcion
from app.utils.security import hash_password

@router.post("/registrar-tenant", status_code=status.HTTP_201_CREATED)
def registrar_tenant(datos: TenantRegisterRequest, db: Session = Depends(get_db)):
    # 1. Verificar si el email o el subdominio ya existen
    if db.query(Usuario).filter(Usuario.email == datos.usuario.email).first():
        raise HTTPException(status_code=400, detail="El email ya está registrado.")
    if db.query(Tenant).filter(Tenant.subdominio == datos.tenant.subdominio).first():
        raise HTTPException(status_code=400, detail="El subdominio ya está en uso.")

    # 2. Crear Tenant
    nuevo_tenant = Tenant(
        nombre=datos.tenant.nombre_comercial,
        subdominio=datos.tenant.subdominio,
        nit=f"NIT-{datos.tenant.subdominio}"
    )
    db.add(nuevo_tenant)
    db.flush()

    # 3. Crear Usuario Dueño (admin_red)
    nuevo_usuario = Usuario(
        nombre=datos.usuario.nombre,
        email=datos.usuario.email,
        password_hash=hash_password(datos.usuario.password),
        telefono=datos.usuario.telefono,
        rol=TipoRol.admin_red,
        tenant_id=nuevo_tenant.id_tenant
    )
    db.add(nuevo_usuario)
    db.flush()

    # 4. Crear la Suscripción (si hay plan)
    if datos.tenant.plan_id:
        nueva_suscripcion = Suscripcion(
            tenant_id=nuevo_tenant.id_tenant,
            plan_id=datos.tenant.plan_id,
            fecha_vencimiento=datetime.now() + timedelta(days=30),
            transaccion_pago_simulado="PAYPAL_WEB"
        )
        db.add(nueva_suscripcion)

    db.commit()
    return {"message": "Empresa SaaS registrada exitosamente"}


# -------------------------------------------------------
# Dependencia reutilizable: obtener el tenant_id autenticado
# -------------------------------------------------------
def get_current_tenant(
    current_user: Usuario = Depends(get_current_user)
) -> Optional[UUID]:

    # Regla de Negocio 1: Admin o Cliente pueden no pertenecer a un tenant de forma legítima
    if current_user.rol in [TipoRol.admin, TipoRol.cliente]:
        return None

    # Regla de Negocio 2: Taller, Técnico o Admin_red deben poseer obligatoriamente un tenant_id válido
    if current_user.rol in [TipoRol.taller, TipoRol.tecnico, TipoRol.admin_red]:
        if not current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas: Falta la identidad del Tenant"
            )
        return current_user.tenant_id

    return None