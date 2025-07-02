# ===================== main.py =====================
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.params import Depends

from fastapi import Depends
from sqlalchemy.orm import Session
from core.security import hash_password
from db.database import engine, Base, SessionLocal
from models.user import User

from db.create_tables import Base, engine
from models import *





# Importar routers
from db.database import SessionLocal
from routes.warehouse import router as warehouse_router
from routes.item import router as item_router
from routes.category import router as category_router
from routes.inventory import router as inventory_router
from routes.item_movement import router as movement_router
from routes.user import router as user_router
from routes.auth import router as auth_router
from routes.sale_group import router as sale_group_router
from routes.sale import router as sale_router
from routes.item_movement_group import router as item_movement_group_router

app = FastAPI(
    title="Sistema de Inventario",
    description="API para gestión de inventario con FastAPI",
    version="1.0.0"
)

origins = [
    "http://localhost:3000",
]


# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Podés ajustar esto a tus dominios frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rutas
app.include_router(warehouse_router)
app.include_router(item_router)
app.include_router(category_router)
app.include_router(inventory_router)
app.include_router(movement_router)
app.include_router(user_router)
app.include_router(auth_router)
app.include_router(sale_group_router)
app.include_router(sale_router)
app.include_router(item_movement_group_router)

@app.get("/")
def root():
    return {"message": "Bienvenido al sistema de inventario"}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/init")
def init(db: Session = Depends(get_db)):
    Base.metadata.create_all(bind=engine)

       # Verificar si el usuario ya existe
    existing_user = db.query(User).filter(User.email == "user@example.com").first()
    if not existing_user:
        user = User(
            username="admin",
            email="user@example.com",
            full_name="Usuario Default",
            hashed_password=hash_password("Carlos20:)")  # Hashea la contraseña
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    #Agregando categoria General por si no existe
    category_gen = db.query(Category).filter(Category.id == 1)
    if not category_gen:
        category = Category(
            name = "General"
        )

        db.add(category)
        db.commit()
        db.refresh(category)


    return {"message": "Base de datos creada"}


# uvicorn main:app --ssl-keyfile=key.pem --ssl-certfile=cert.pem