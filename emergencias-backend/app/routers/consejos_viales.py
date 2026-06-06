# ============================================================
# Router de Consejos de Seguridad Vial - Ciclo 5 - CU25
# CRUD + IA para consejos personalizados según tipo de incidente
# ============================================================

import os
import json
import requests
import re
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.consejo_vial import ConsejoSeguridad
from app.models.incidente import Incidente, EvidenciaIA
from app.models.usuario import Usuario, TipoRol
from app.routers.auth import get_current_user
from app.schemas.consejo_vial import ConsejoCreate, ConsejoUpdate, ConsejoOut

router = APIRouter(prefix="/consejos-viales", tags=["CU25 - Asistente IA Seguridad Vial"])

# API Key de Groq - Ciclo 5 - CU25
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")


# ===================================================================
# CU25: LISTAR TODOS LOS CONSEJOS ACTIVOS - Ciclo 5 - CU25
# ===================================================================
# Descripción: Lista todos los consejos de seguridad vial activos
# Ciclo: Ciclo 5
# CU: CU25
@router.get("/", response_model=List[ConsejoOut])
def listar_consejos(db: Session = Depends(get_db)):
    return db.query(ConsejoSeguridad).filter(
        ConsejoSeguridad.activo == True
    ).all()


# ===================================================================
# CU25: FILTRAR POR CATEGORÍA - Ciclo 5 - CU25
# ===================================================================
# Descripción: Filtra consejos de seguridad por una categoría específica
# Ciclo: Ciclo 5
# CU: CU25
@router.get("/por-categoria/{categoria}", response_model=List[ConsejoOut])
def consejos_por_categoria(
    categoria: str,
    db: Session = Depends(get_db)
):
    return db.query(ConsejoSeguridad).filter(
        ConsejoSeguridad.categoria == categoria.lower(),
        ConsejoSeguridad.activo == True
    ).all()


# ===================================================================
# CU25: CONSEJOS PERSONALIZADOS PARA UN INCIDENTE - Ciclo 5 - CU25
# Analiza la clasificación IA del incidente y retorna consejos relevantes
# ===================================================================
# Descripción: Obtiene consejos personalizados según el tipo de daño del incidente
# Ciclo: Ciclo 5
# CU: CU25
@router.get("/para-incidente/{incidente_id}", response_model=List[ConsejoOut])
def consejos_para_incidente(
    incidente_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Obtener la clasificación IA del incidente - Ciclo 5 - CU25
    incidente = db.query(Incidente).filter(
        Incidente.id_incidente == incidente_id
    ).first()
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado.")

    # Buscar clasificación en las evidencias - Ciclo 5 - CU25
    evidencia = db.query(EvidenciaIA).filter(
        EvidenciaIA.incidente_id == incidente_id,
        EvidenciaIA.clasificacion_ia_texto.isnot(None)
    ).first()

    categoria_detectada = None
    if evidencia and evidencia.clasificacion_ia_texto:
        # Extraer categoría de "[CHOQUE] Prioridad ALTA: ..." - Ciclo 5 - CU25
        match = re.search(r'\[(\w+)\]', evidencia.clasificacion_ia_texto)
        if match:
            categoria_detectada = match.group(1).lower()

    # Buscar consejos de la categoría + generales - Ciclo 5 - CU25
    if categoria_detectada:
        consejos = db.query(ConsejoSeguridad).filter(
            ConsejoSeguridad.activo == True,
            ConsejoSeguridad.categoria.in_([categoria_detectada, 'general'])
        ).all()
    else:
        consejos = db.query(ConsejoSeguridad).filter(
            ConsejoSeguridad.activo == True,
            ConsejoSeguridad.categoria == 'general'
        ).all()

    return consejos


# ===================================================================
# CU25: CREAR NUEVO CONSEJO (admin) - Ciclo 5 - CU25
# ===================================================================
# Descripción: Administrador crea un nuevo consejo de seguridad vial
# Ciclo: Ciclo 5
# CU: CU25
@router.post("/", response_model=ConsejoOut, status_code=status.HTTP_201_CREATED)
def crear_consejo(
    datos: ConsejoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol != TipoRol.admin:
        raise HTTPException(status_code=403, detail="Solo el admin puede crear consejos.")

    nuevo = ConsejoSeguridad(
        categoria=datos.categoria.lower(),
        titulo=datos.titulo,
        contenido=datos.contenido,
        icono=datos.icono
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


# ===================================================================
# CU25: GENERAR CONSEJOS CON IA PARA UN INCIDENTE - Ciclo 5 - CU25
# ===================================================================
# Descripción: Invoca al agente conversacional LLM para generar consejos precisos
# Ciclo: Ciclo 5
# CU: CU25
@router.post("/generar-ia/{incidente_id}")
def generar_consejos_ia(
    incidente_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    incidente = db.query(Incidente).filter(
        Incidente.id_incidente == incidente_id
    ).first()
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado.")

    descripcion = incidente.descripcion_texto or "Sin descripción"

    # Buscar clasificación existente - Ciclo 5 - CU25
    evidencia = db.query(EvidenciaIA).filter(
        EvidenciaIA.incidente_id == incidente_id,
        EvidenciaIA.clasificacion_ia_texto.isnot(None)
    ).first()
    clasificacion = evidencia.clasificacion_ia_texto if evidencia else "No clasificado"

    # Llamar a Groq para generar consejos personalizados - Ciclo 5 - CU25
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}

    prompt = f"""
    Eres un experto en seguridad vial. Un conductor tiene una emergencia vehicular:
    - Descripción: "{descripcion}"
    - Clasificación IA: "{clasificacion}"

    Genera exactamente 3 consejos de seguridad específicos para esta emergencia.
    Responde ESTRICTAMENTE en JSON con esta estructura:
    [
        {{"titulo": "Consejo corto", "contenido": "Explicación detallada de 1-2 líneas", "icono": "emoji"}},
        {{"titulo": "Consejo corto", "contenido": "Explicación detallada de 1-2 líneas", "icono": "emoji"}},
        {{"titulo": "Consejo corto", "contenido": "Explicación detallada de 1-2 líneas", "icono": "emoji"}}
    ]
    Solo devuelve el JSON puro, sin explicaciones adicionales.
    """

    body = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 500
    }

    try:
        res = requests.post(url, headers=headers, json=body, timeout=15)
        if res.status_code == 200:
            texto = res.json()["choices"][0]["message"]["content"]
            # Limpiar markdown si viene envuelto - Ciclo 5 - CU25
            texto = texto.replace("```json", "").replace("```", "").strip()
            consejos = json.loads(texto)
            return {"consejos_generados": consejos, "incidente_id": incidente_id}
    except Exception as e:
        print(f"Error Groq Consejos: {e}")

    # Fallback si IA falla - Ciclo 5 - CU25
    return {
        "consejos_generados": [
            {"titulo": "Mantente seguro", "contenido": "Permanece dentro del vehículo si estás en una vía rápida.", "icono": "🛡️"},
            {"titulo": "Señaliza tu posición", "contenido": "Activa las luces de emergencia y coloca triángulos de seguridad.", "icono": "⚠️"},
            {"titulo": "Espera al técnico", "contenido": "No intentes reparaciones si no tienes experiencia, el auxilio va en camino.", "icono": "🔧"}
        ],
        "incidente_id": incidente_id
    }


# ===================================================================
# CU25: ACTUALIZAR CONSEJO (admin) - Ciclo 5 - CU25
# ===================================================================
# Descripción: Actualiza un consejo de seguridad vial existente
# Ciclo: Ciclo 5
# CU: CU25
@router.put("/{id_consejo}", response_model=ConsejoOut)
def actualizar_consejo(
    id_consejo: int,
    datos: ConsejoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol != TipoRol.admin:
        raise HTTPException(status_code=403, detail="Solo el admin puede editar consejos.")

    consejo = db.query(ConsejoSeguridad).filter(
        ConsejoSeguridad.id_consejo == id_consejo
    ).first()
    if not consejo:
        raise HTTPException(status_code=404, detail="Consejo no encontrado.")

    # Actualización parcial - Ciclo 5 - CU25
    if datos.categoria is not None:
        consejo.categoria = datos.categoria.lower()
    if datos.titulo is not None:
        consejo.titulo = datos.titulo
    if datos.contenido is not None:
        consejo.contenido = datos.contenido
    if datos.icono is not None:
        consejo.icono = datos.icono
    if datos.activo is not None:
        consejo.activo = datos.activo

    db.commit()
    db.refresh(consejo)
    return consejo


# ===================================================================
# CU25: ELIMINAR CONSEJO (admin) - Ciclo 5 - CU25
# ===================================================================
@router.delete("/{id_consejo}")
def eliminar_consejo(
    id_consejo: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol != TipoRol.admin:
        raise HTTPException(status_code=403, detail="Solo el admin puede eliminar consejos.")

    consejo = db.query(ConsejoSeguridad).filter(
        ConsejoSeguridad.id_consejo == id_consejo
    ).first()
    if not consejo:
        raise HTTPException(status_code=404, detail="Consejo no encontrado.")

    db.delete(consejo)
    db.commit()
    return {"mensaje": f"Consejo '{consejo.titulo}' eliminado correctamente."}
