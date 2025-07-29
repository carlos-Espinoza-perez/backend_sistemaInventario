from sqlalchemy.orm import Session
from sqlalchemy import text
from db.database import Base, engine

def limpiar_base_de_datos():
    with engine.connect() as conn:
        # Deshabilitar claves foráneas temporalmente (solo mientras ejecuta)
        conn.execute(text("SET CONSTRAINTS ALL DEFERRED"))

        # Borrar una por una en orden inverso
        for tabla in reversed(Base.metadata.sorted_tables):
            conn.execute(text(f'DELETE FROM "{tabla.name}"'))

        # Reiniciar IDs (auto-incrementales)
        for tabla in Base.metadata.sorted_tables:
            conn.execute(text(f'ALTER SEQUENCE "{tabla.name}_id_seq" RESTART WITH 1'))

        conn.commit()

    print("✅ Base limpiada y contadores reiniciados.")