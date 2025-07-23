from sqlalchemy.orm import Session
from sqlalchemy import text
from db.database import Base, engine

def limpiar_base_de_datos():
    with engine.begin() as conn:
        # Deshabilita las restricciones de clave foránea (para SQLite y otras)
        # conn.execute(text("PRAGMA foreign_keys = OFF"))  # Para SQLite
        conn.execute(text("SET session_replication_role = replica"))  # Para PostgreSQL

        # Obtener los nombres de las tablas
        tablas = reversed(Base.metadata.sorted_tables)

        for tabla in tablas:
            conn.execute(text(f'DELETE FROM "{tabla.name}"'))

        # Rehabilita las restricciones
        # conn.execute(text("PRAGMA foreign_keys = ON"))
        conn.execute(text("SET session_replication_role = DEFAULT"))

    print("🧨 Todos los datos han sido eliminados.")
