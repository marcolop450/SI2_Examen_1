# #Ciclo5 CU25 - Script para poblar la tabla consejos_seguridad con datos iniciales
# Ejecutar: python seed_consejos.py
# Asegura que el móvil tenga consejos disponibles para todas las categorías

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.consejo_vial import ConsejoSeguridad

def seed_consejos():
    db = SessionLocal()
    try:
        # Verificar si ya hay datos
        existe = db.query(ConsejoSeguridad).first()
        if existe:
            print(f"✅ La tabla ya tiene consejos. Nada que hacer.")
            return

        consejos = [
            # ── LLANTA ──────────────────────────────────────────────────────
            ConsejoSeguridad(categoria="llanta", titulo="No frenes bruscamente",
                contenido="Si tienes una llanta ponchada, reduce la velocidad gradualmente usando el motor. No pises el freno de golpe.",
                icono="🛞", activo=True),
            ConsejoSeguridad(categoria="llanta", titulo="Estaciona con seguridad",
                contenido="Busca el costado derecho de la vía, lo más alejado del tráfico posible, antes de detenerte.",
                icono="🅿️", activo=True),
            ConsejoSeguridad(categoria="llanta", titulo="Activa las luces de emergencia",
                contenido="Haz visible tu vehículo ANTES de bajar del auto. Pon los cuatro intermitentes inmediatamente.",
                icono="⚠️", activo=True),
            ConsejoSeguridad(categoria="llanta", titulo="Usa triángulos de seguridad",
                contenido="Coloca triángulos reflectantes a 50 metros detrás del vehículo para alertar a otros conductores.",
                icono="🔺", activo=True),
            ConsejoSeguridad(categoria="llanta", titulo="No cambies en una curva",
                contenido="Nunca cambies una llanta en una curva o pendiente. Espera un lugar plano y seguro.",
                icono="🚫", activo=True),

            # ── MOTOR ───────────────────────────────────────────────────────
            ConsejoSeguridad(categoria="motor", titulo="No abras el capó caliente",
                contenido="Si el motor humeó o recalentó, espera al menos 15-20 minutos antes de abrir el capó para evitar quemaduras.",
                icono="🔥", activo=True),
            ConsejoSeguridad(categoria="motor", titulo="Revisa el nivel de aceite",
                contenido="Un motor sin aceite puede sufrir daños irreversibles en minutos. Verifica el nivel con la varilla.",
                icono="🛢️", activo=True),
            ConsejoSeguridad(categoria="motor", titulo="No arranques repetidamente",
                contenido="Si el motor no enciende, no intentes arrancarlo más de 3 veces seguidas. Dañarías el motor de arranque.",
                icono="🚫", activo=True),
            ConsejoSeguridad(categoria="motor", titulo="Revisa si hay humo del escape",
                contenido="Humo blanco indica agua, humo azul indica aceite, humo negro indica mezcla rica. Comunícalo al técnico.",
                icono="💨", activo=True),
            ConsejoSeguridad(categoria="motor", titulo="Apaga el motor si recalienta",
                contenido="Si el indicador de temperatura está en rojo, apaga inmediatamente. Continuar puede fundir el motor.",
                icono="🌡️", activo=True),

            # ── BATERÍA ─────────────────────────────────────────────────────
            ConsejoSeguridad(categoria="bateria", titulo="No toques los bornes",
                contenido="Los terminales de la batería pueden tener corrosión ácida. No los toques sin guantes.",
                icono="⚡", activo=True),
            ConsejoSeguridad(categoria="bateria", titulo="Apaga todos los accesorios",
                contenido="Luces, radio, aire acondicionado y cargadores consumen la poca carga residual que queda.",
                icono="🔋", activo=True),
            ConsejoSeguridad(categoria="bateria", titulo="Verifica los cables",
                contenido="A veces el problema es un cable flojo o con corrosión en el borne. Míralo antes de llamar al técnico.",
                icono="🔌", activo=True),
            ConsejoSeguridad(categoria="bateria", titulo="No cables en lluvia",
                contenido="Nunca intentes hacer puente de batería si llueve. El riesgo de cortocircuito es alto.",
                icono="🌧️", activo=True),
            ConsejoSeguridad(categoria="bateria", titulo="Pon en neutro si tienes empuje",
                contenido="Si alguien puede empujarte, pon el auto en segunda marcha y suelta el clutch al alcanzar velocidad.",
                icono="🚗", activo=True),

            # ── CHOQUE ──────────────────────────────────────────────────────
            ConsejoSeguridad(categoria="choque", titulo="Documenta todo primero",
                contenido="Antes de mover los vehículos, toma fotos del daño, la posición de los autos y cualquier señal de tráfico.",
                icono="📸", activo=True),
            ConsejoSeguridad(categoria="choque", titulo="No muevas el vehículo",
                contenido="Si hay heridos, no muevas ningún vehículo hasta que lleguen las autoridades. Preserva la escena.",
                icono="🚨", activo=True),
            ConsejoSeguridad(categoria="choque", titulo="Intercambia datos",
                contenido="Obtén nombre, teléfono, número de placa y aseguradora del otro conductor involucrado.",
                icono="📋", activo=True),
            ConsejoSeguridad(categoria="choque", titulo="Verifica si hay heridos",
                contenido="Pregunta a todos los involucrados si están bien. Si alguien se queja de dolor de cuello, no lo muevas.",
                icono="🏥", activo=True),
            ConsejoSeguridad(categoria="choque", titulo="Aleja testigos de combustible",
                contenido="Si hueles gasolina, aleja a todos del vehículo. No enciendas nada hasta estar seguro que no hay fuga.",
                icono="⛽", activo=True),

            # ── GENERAL ─────────────────────────────────────────────────────
            ConsejoSeguridad(categoria="general", titulo="Mantén la calma",
                contenido="Respira profundo y evalúa la situación sin precipitarte. El pánico empeora cualquier emergencia.",
                icono="🛡️", activo=True),
            ConsejoSeguridad(categoria="general", titulo="Enciende luces de emergencia",
                contenido="Lo primero siempre: activa los cuatro intermitentes para alertar a otros conductores de tu situación.",
                icono="🚨", activo=True),
            ConsejoSeguridad(categoria="general", titulo="No abandones el vehículo en vía rápida",
                contenido="Si estás en autopista o avenida de alta velocidad, permanece dentro del vehículo con el cinturón puesto.",
                icono="🚗", activo=True),
            ConsejoSeguridad(categoria="general", titulo="Usa el triángulo de seguridad",
                contenido="Si tienes uno en el maletero, colócalo 50m detrás. Si no tienes, mantén las luces activas.",
                icono="🔺", activo=True),
            ConsejoSeguridad(categoria="general", titulo="Comparte tu ubicación",
                contenido="Envía tu ubicación GPS exacta a un familiar o amigo para que alguien más sepa dónde estás.",
                icono="📍", activo=True),

            # ── CLIMA ───────────────────────────────────────────────────────
            ConsejoSeguridad(categoria="clima", titulo="En lluvia: reduce velocidad",
                contenido="El asfalto mojado reduce la adherencia al 30%. Mantén doble distancia de seguimiento.",
                icono="🌧️", activo=True),
            ConsejoSeguridad(categoria="clima", titulo="Enciende los limpiaparabrisas",
                contenido="Asegúrate de que funcionen bien antes de salir con lluvia. La visibilidad es tu mayor activo.",
                icono="🌊", activo=True),
            ConsejoSeguridad(categoria="clima", titulo="Evita zonas inundadas",
                contenido="No intentes cruzar una calle inundada. 30cm de agua en movimiento puede arrastrar un vehículo.",
                icono="⚠️", activo=True),
        ]

        db.add_all(consejos)
        db.commit()
        print(f"✅ Se insertaron {len(consejos)} consejos de seguridad vial correctamente.")

    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_consejos()
