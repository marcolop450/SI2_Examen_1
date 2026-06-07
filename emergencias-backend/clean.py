import sys
sys.path.append('c:\\Users\\dell\\SI2_Examen_1\\emergencias-backend')
from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    sql = "DELETE FROM tenants WHERE nombre_comercial NOT IN ('KAKIS COR', 'GATOS')"
    result = db.execute(text(sql))
    db.commit()
    print(f'=== LIMPIEZA COMPLETADA: {result.rowcount} Tenants eliminados (con cascada nativa). ===')
except Exception as e:
    db.rollback()
    print('Error:', e)
finally:
    db.close()
