import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("No DATABASE_URL found in .env")
    exit(1)

engine = create_engine(DATABASE_URL)
try:
    with engine.execution_options(isolation_level="AUTOCOMMIT").connect() as conn:
        conn.execute(text("ALTER TYPE tipo_rol ADD VALUE IF NOT EXISTS 'admin_red';"))
        print("Migración exitosa: 'admin_red' agregado a tipo_rol.")
except Exception as e:
    print(f"Error en la migración: {e}")
