from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os



DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./inventario.db")
# DATABASE_URL = "postgresql://sistema_inventario_yoxd_user:HBnIV9scNE6bCZZJgdOHHk6GpN5P7udM@dpg-d1ivem6r433s73fkb0jg-a.oregon-postgres.render.com/sistema_inventario_yoxd"

# Solo incluir `connect_args` si usas SQLite
if DATABASE_URL.startswith("sqlite"):
  engine = create_engine(
      DATABASE_URL, connect_args={"check_same_thread": False}
  )
else:
  engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

