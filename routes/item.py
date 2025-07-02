from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.generar_codigo import generar_codigo
from core.dependencies import get_current_user
from db.database import SessionLocal
from models.item import Item
from models.user import User
from schemas.item import ItemCreate, ItemOut

router = APIRouter(prefix="/items", tags=["Items"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=ItemOut)
def create_item(item: ItemCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_item = Item(**item.dict())
    if db_item.code == '' or db_item.code is None:
        db_item.code = generar_codigo(db_item.name)

    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.get("/", response_model=list[ItemOut])
def get_items(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Item).all()

@router.get("/{item_id}", response_model=ItemOut)
def get_item(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(Item).get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@router.put("/{item_id}", response_model=ItemOut)
def update_item(item_id: int, data: ItemCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(Item).get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    for key, value in data.dict().items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item

@router.delete("/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(Item).get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
    return {"ok": True}
