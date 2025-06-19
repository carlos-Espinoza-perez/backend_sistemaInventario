from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import SessionLocal
from models.inventory import Inventory
from schemas.inventory import InventoryCreate, InventoryOut

router = APIRouter(prefix="/inventory", tags=["Inventory"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=InventoryOut)
def create_inventory(entry: InventoryCreate, db: Session = Depends(get_db)):
    db_entry = Inventory(**entry.dict())
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return db_entry

@router.get("/", response_model=list[InventoryOut])
def get_inventory(db: Session = Depends(get_db)):
    return db.query(Inventory).all()

@router.get("/{inventory_id}", response_model=InventoryOut)
def get_inventory_entry(inventory_id: int, db: Session = Depends(get_db)):
    entry = db.query(Inventory).get(inventory_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Inventory entry not found")
    return entry

@router.put("/{inventory_id}", response_model=InventoryOut)
def update_inventory(inventory_id: int, data: InventoryCreate, db: Session = Depends(get_db)):
    entry = db.query(Inventory).get(inventory_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Inventory entry not found")
    for key, value in data.dict().items():
        setattr(entry, key, value)
    db.commit()
    db.refresh(entry)
    return entry

@router.delete("/{inventory_id}")
def delete_inventory(inventory_id: int, db: Session = Depends(get_db)):
    entry = db.query(Inventory).get(inventory_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Inventory entry not found")
    db.delete(entry)
    db.commit()
    return {"ok": True}