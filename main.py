# ===================== main.py =====================
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db.create_tables import Base, engine


# Importar routers
from routes.warehouse import router as warehouse_router
from routes.item import router as item_router
from routes.category import router as category_router
from routes.inventory import router as inventory_router
from routes.item_movement import router as movement_router
from routes.user import router as user_router

app = FastAPI(
    title="Sistema de Inventario",
    description="API para gestión de inventario con FastAPI",
    version="1.0.0"
)

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

@app.get("/")
def root():
    return {"message": "Bienvenido al sistema de inventario"}

@app.get("/init")
def init():
    Base.metadata.create_all(bind=engine)
    return {"message": "Base de datos creada correctamente"}