# ============================================================
# routers/tecnicos.py
#
# CU6: Administrar Staff Técnico (CRUD)
#   Actor principal: A2 (Taller)
#
# ENDPOINTS:
#   POST   /tecnicos/          → Registrar técnico (solo taller dueño)
#   GET    /tecnicos/taller/{id} → Listar técnicos de un taller
#   GET    /tecnicos/{id}      → Ver técnico específico
#   PUT    /tecnicos/{id}      → Actualizar técnico completo
#   PATCH  /tecnicos/{id}      → Cambiar disponibilidad
#   DELETE /tecnicos/{id}      → Eliminar técnico
#

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.utils.security import hash_password
from app.database import get_db
from app.models.tecnico import Tecnico
from app.models.taller import Taller
from app.models.usuario import Usuario, TipoRol
from app.schemas.tecnico import TecnicoCreate, TecnicoUpdate, TecnicoPartial, TecnicoOut
from app.routers.auth import get_current_user

router = APIRouter(prefix="/tecnicos", tags=["CU6 - Staff Técnico"])


# -------------------------------------------------------
# Función auxiliar: verifica que el usuario sea taller o admin
# -------------------------------------------------------
def require_taller_o_admin(current_user: Usuario = Depends(get_current_user)):
    if current_user.rol not in [TipoRol.taller, TipoRol.admin]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado: se requiere rol taller o administrador"
        )
    return current_user


# -------------------------------------------------------
# POST /tecnicos/
# Registrar nuevo técnico en un taller
# Solo el taller dueño o admin puede registrar técnicos
# -------------------------------------------------------
@router.post("/", response_model=TecnicoOut, status_code=status.HTTP_201_CREATED)
def crear_tecnico(
    datos: TecnicoCreate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_taller_o_admin)
):
    # 1. Buscar el taller de forma segura
    # Intentamos buscar por taller_id O por el dueño (current_user)
    taller = db.query(Taller).filter(
        (Taller.id_taller == datos.taller_id) | (Taller.dueño_id == current_user.id_usuario)
    ).first()
    
    if not taller: 
        raise HTTPException(status_code=404, detail="No se encontró un taller asociado a tu cuenta")

    # 2. Verificar si el email ya existe
    existe = db.query(Usuario).filter(Usuario.email == datos.email).first()
    if existe: 
        raise HTTPException(status_code=400, detail="El correo electrónico ya está registrado")

    # 3. CREAR USUARIO
    nuevo_usuario = Usuario(
        nombre=datos.nombre,
        email=datos.email,
        password_hash=hash_password(datos.password), 
        rol=TipoRol.tecnico,
        telefono=datos.telefono
    )
    db.add(nuevo_usuario)
    db.flush() 

    # 4. CREAR TECNICO (Usamos el taller.id_taller REAL que encontramos)
    nuevo_tecnico = Tecnico(
        taller_id=taller.id_taller,
        tenant_id=taller.tenant_id,
        usuario_id=nuevo_usuario.id_usuario,
        nombre=datos.nombre,
        especialidad=datos.especialidad,
        disponible_boolean=datos.disponible_boolean
    )
    db.add(nuevo_tecnico)
    db.commit()
    db.refresh(nuevo_tecnico)

    return {
        "id_tecnico": nuevo_tecnico.id_tecnico,
        "taller_id": nuevo_tecnico.taller_id,
        "usuario_id": nuevo_tecnico.usuario_id,
        "nombre": nuevo_usuario.nombre,
        "especialidad": nuevo_tecnico.especialidad,
        "disponible_boolean": nuevo_tecnico.disponible_boolean
    }


# -------------------------------------------------------
# GET /tecnicos/taller/{taller_id}
# Listar todos los técnicos de un taller específico
# Usado por el taller para ver su equipo en CU11
# -------------------------------------------------------
@router.get("/taller/{id_recibido}", response_model=List[TecnicoOut])
def listar_tecnicos_por_taller(
    id_recibido: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # 1. Buscamos el taller. El id_recibido puede ser el ID del Taller 
    #    O el ID del Usuario (Dueño).
    taller = db.query(Taller).filter(
        (Taller.id_taller == id_recibido) | (Taller.dueño_id == id_recibido)
    ).first()

    if not taller:
        print(f"DEBUG: No se encontró taller para el ID {id_recibido}")
        return [] 

    # 2. Traemos los técnicos del taller REAL encontrado
    tecnicos = db.query(Tecnico).filter(Tecnico.taller_id == taller.id_taller).all()
    print(f"DEBUG: Taller encontrado: {taller.id_taller}. Técnicos: {len(tecnicos)}")
    
    return tecnicos
# -------------------------------------------------------
# GET /tecnicos/{id_tecnico}
# Ver un técnico específico por su ID
# -------------------------------------------------------
@router.get("/{id_tecnico}", response_model=TecnicoOut)
def obtener_tecnico(
    id_tecnico: int,
    db: Session = Depends(get_db),
    _: Usuario  = Depends(get_current_user)
):
    tecnico = db.query(Tecnico).filter(Tecnico.id_tecnico == id_tecnico).first()
    if not tecnico:
        raise HTTPException(status_code=404, detail="Técnico no encontrado")
    return tecnico


# -------------------------------------------------------
# PUT /tecnicos/{id_tecnico}
# Actualizar todos los datos del técnico
# -------------------------------------------------------
@router.put("/{id_tecnico}", response_model=TecnicoOut)
def actualizar_tecnico(
    id_tecnico: int,
    datos: TecnicoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_taller_o_admin)
):
    tecnico = db.query(Tecnico).filter(Tecnico.id_tecnico == id_tecnico).first()
    if not tecnico:
        raise HTTPException(status_code=404, detail="Técnico no encontrado")

    # Verificar que el taller solo edite sus propios técnicos
    if current_user.rol == TipoRol.taller:
        taller = db.query(Taller).filter(Taller.id_taller == tecnico.taller_id).first()
        if taller.dueño_id != current_user.id_usuario:
            raise HTTPException(status_code=403, detail="No puedes editar técnicos de otro taller")

    tecnico.nombre             = datos.nombre
    tecnico.especialidad       = datos.especialidad
    tecnico.disponible_boolean = datos.disponible_boolean

    db.commit()
    db.refresh(tecnico)
    return tecnico


# -------------------------------------------------------
# PATCH /tecnicos/{id_tecnico}
# Actualización parcial - principalmente para cambiar
# disponibilidad del técnico (disponible/en ruta)
# -------------------------------------------------------
@router.patch("/{id_tecnico}", response_model=TecnicoOut)
def actualizar_tecnico_parcial(
    id_tecnico: int,
    datos: TecnicoPartial,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_taller_o_admin)
):
    tecnico = db.query(Tecnico).filter(Tecnico.id_tecnico == id_tecnico).first()
    if not tecnico:
        raise HTTPException(status_code=404, detail="Técnico no encontrado")

    # Solo actualiza los campos que vengan en el body
    if datos.nombre             is not None: tecnico.nombre             = datos.nombre
    if datos.especialidad       is not None: tecnico.especialidad       = datos.especialidad
    if datos.disponible_boolean is not None: tecnico.disponible_boolean = datos.disponible_boolean

    db.commit()
    db.refresh(tecnico)
    return tecnico


# -------------------------------------------------------
# DELETE /tecnicos/{id_tecnico}
# Eliminar técnico del sistema
# -------------------------------------------------------
@router.delete("/{id_tecnico}", status_code=status.HTTP_200_OK)
def eliminar_tecnico(
    id_tecnico: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_taller_o_admin)
):
    tecnico = db.query(Tecnico).filter(Tecnico.id_tecnico == id_tecnico).first()
    if not tecnico:
        raise HTTPException(status_code=404, detail="Técnico no encontrado")

    db.delete(tecnico)
    db.commit()
    return {"message": f"Técnico '{tecnico.nombre}' eliminado correctamente"}