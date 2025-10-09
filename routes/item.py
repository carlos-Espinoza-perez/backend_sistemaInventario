from fastapi import APIRouter, Depends, HTTPException
from models.inventory import Inventory
from sqlalchemy.orm import Session
from core.generar_codigo import generar_codigo
from core.dependencies import get_current_user
from db.database import SessionLocal
from models.item import Item
from models.user import User
from schemas.item import ItemCreate, ItemOut
from sqlalchemy.orm import aliased
from sqlalchemy import  func



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

@router.get("/grouped_from_items/{warehouse_id}")
def get_inventory_grouped_from_items(
    warehouse_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Subconsulta para obtener el último registro de cada item_id en la bodega
    subquery = (
        db.query(
            Inventory.item_id,
            func.max(Inventory.updated_at).label("max_updated_at")
        )
        .filter(Inventory.warehouse_id == warehouse_id)
        .group_by(Inventory.item_id)
        .subquery()
    )

    LastInventory = aliased(Inventory)

    # Consulta principal iniciando desde Item
    results = (
        db.query(
            Item.id.label("item_id"),
            Item.name.label("item_name"),
            func.coalesce(func.sum(Inventory.quantity), 0).label("total_quantity"),
            func.coalesce(func.sum(Inventory.quantity * Inventory.purchase_price), 0).label("total_investment"),
            LastInventory.sale_price.label("last_sale_price"),
            LastInventory.purchase_price.label("last_purchase_price")
        )
        .outerjoin(Inventory, (Inventory.item_id == Item.id) & (Inventory.warehouse_id == warehouse_id))
        .outerjoin(subquery,
                   (Inventory.item_id == subquery.c.item_id) &
                   (Inventory.updated_at == subquery.c.max_updated_at))
        .outerjoin(LastInventory,
                   (LastInventory.item_id == subquery.c.item_id) &
                   (LastInventory.updated_at == subquery.c.max_updated_at))
        .group_by(
            Item.id,
            Item.name,
            LastInventory.sale_price,
            LastInventory.purchase_price
        )
        .all()
    )

    # Armar la respuesta
    summary = [
        {
            "item_id": r.item_id,
            "item_name": r.item_name,
            "total_quantity": r.total_quantity,
            "total_investment": r.total_investment,
            "last_sale_price": r.last_sale_price,
            "last_purchase_price": r.last_purchase_price,
        }
        for r in results
    ]

    return summary

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
