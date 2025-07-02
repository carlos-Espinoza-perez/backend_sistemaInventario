from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from core.dependencies import get_current_user
from db.database import SessionLocal

from models.item import Item
from models.item_movement import ItemMovement
from models.user import User
from schemas.item_movement import ItemMovementBulkCreate, ItemMovementCreate, ItemMovementOut

router = APIRouter(prefix="/movements", tags=["Item Movements"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=ItemMovementOut)
def create_movement(movement: ItemMovementCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_movement = ItemMovement(**movement.dict())
    db.add(db_movement)
    db.commit()
    db.refresh(db_movement)
    return db_movement

@router.post("/bulk", response_model=list[ItemMovementOut])
def create_movements_bulk(
    bulk_data: ItemMovementBulkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    created_movements = []

    try:
        for data in bulk_data.items:
            db_movement = ItemMovement(**data.dict())
            db_movement.user_id = current_user.id  # Set the user ID from the current user
            db_movement.timestamp = datetime.utcnow()

            db.add(db_movement)
            created_movements.append(db_movement)

        db.commit()
        for mov in created_movements:
            db.refresh(mov)

        return created_movements

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error procesando movimientos: {str(e)}")


# @router.get("/{item_movement_group_id}", response_model=list[ItemMovementOut])
# def get_movements(item_movement_group_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
#     return db.query(ItemMovement).filter(ItemMovement.item_movement_group_id == item_movement_group_id).all()

@router.get("/{item_movement_group_id}", response_model=list[ItemMovementOut])
def get_movements(
    item_movement_group_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    results = (
        db.query(ItemMovement, Item)
        .join(Item, ItemMovement.item_id == Item.id) # Unimos Item a ItemMovement por su clave foránea
        .filter(ItemMovement.item_movement_group_id == item_movement_group_id)
        .all()
    )

    response = []
    for movement, item in results:
        response.append(
            ItemMovementOut(
                id=movement.id,
                item_movement_group_id=movement.item_movement_group_id,
                item_id=movement.item_id,
                quantity=movement.quantity,
                purchase_price=movement.purchase_price,
                sale_price=movement.sale_price,
                timestamp=movement.timestamp,
                item_name=item.name,
                source_warehouse_id=movement.source_warehouse_id,
                target_warehouse_id=movement.target_warehouse_id,
                type=movement.type,
                user_id=movement.user_id
            )
        )

    return response

@router.get("/", response_model=list[ItemMovementOut])
def get_movements(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(ItemMovement).all()

@router.get("/{movement_id}", response_model=ItemMovementOut)
def get_movement(movement_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    movement = db.query(ItemMovement).get(movement_id)
    if not movement:
        raise HTTPException(status_code=404, detail="Movement not found")
    return movement

@router.put("/{movement_id}", response_model=ItemMovementOut)
def update_movement(movement_id: int, data: ItemMovementCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    movement = db.query(ItemMovement).get(movement_id)
    if not movement:
        raise HTTPException(status_code=404, detail="Movement not found")
    for key, value in data.dict().items():
        setattr(movement, key, value)
    db.commit()
    db.refresh(movement)
    return movement

@router.delete("/{movement_id}")
def delete_movement(movement_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    movement = db.query(ItemMovement).get(movement_id)
    if not movement:
        raise HTTPException(status_code=404, detail="Movement not found")
    db.delete(movement)
    db.commit()
    return {"ok": True} 