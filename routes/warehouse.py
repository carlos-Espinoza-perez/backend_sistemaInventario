from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.dependencies import get_current_user
from db.database import SessionLocal
from models.user import User
from models.warehouse import Warehouse
from schemas.warehouse import WarehouseCreate, WarehouseOut

router = APIRouter(prefix="/warehouses", tags=["Warehouses"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=WarehouseOut)
def create_warehouse(warehouse: WarehouseCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_warehouse = Warehouse(**warehouse.dict())
    db.add(db_warehouse)
    db.commit()
    db.refresh(db_warehouse)
    return db_warehouse

@router.get("/", response_model=list[WarehouseOut])
def get_warehouses(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Warehouse).all()

@router.get("/{warehouse_id}", response_model=WarehouseOut)
def get_warehouse(warehouse_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    warehouse = db.query(Warehouse).get(warehouse_id)
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    return warehouse

@router.put("/{warehouse_id}", response_model=WarehouseOut)
def update_warehouse(warehouse_id: int, data: WarehouseCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    warehouse = db.query(Warehouse).get(warehouse_id)
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    for key, value in data.dict().items():
        setattr(warehouse, key, value)
    db.commit()
    db.refresh(warehouse)
    return warehouse

@router.delete("/{warehouse_id}")
def delete_warehouse(warehouse_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    warehouse = db.query(Warehouse).get(warehouse_id)
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    db.delete(warehouse)
    db.commit()
    return {"ok": True}
