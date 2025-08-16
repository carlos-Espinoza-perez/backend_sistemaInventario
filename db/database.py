from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os



DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./inventario.db")
# DATABASE_URL = "postgresql://postgres.jeyvqmjzmcdsvrabsszz:Carlos2013:)@aws-0-us-west-1.pooler.supabase.com:5432/postgres?sslmode=require"
print(DATABASE_URL)
# Solo incluir `connect_args` si usas SQLite
if DATABASE_URL.startswith("sqlite"):
  engine = create_engine(
      DATABASE_URL, connect_args={"check_same_thread": False}
  )
else:
  engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

