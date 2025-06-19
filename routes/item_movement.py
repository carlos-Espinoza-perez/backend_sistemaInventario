from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import SessionLocal
from models.item_movement import ItemMovement
from schemas.item_movement import ItemMovementCreate, ItemMovementOut

router = APIRouter(prefix="/movements", tags=["Item Movements"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=ItemMovementOut)
def create_movement(movement: ItemMovementCreate, db: Session = Depends(get_db)):
    db_movement = ItemMovement(**movement.dict())
    db.add(db_movement)
    db.commit()
    db.refresh(db_movement)
    return db_movement

@router.get("/", response_model=list[ItemMovementOut])
def get_movements(db: Session = Depends(get_db)):
    return db.query(ItemMovement).all()

@router.get("/{movement_id}", response_model=ItemMovementOut)
def get_movement(movement_id: int, db: Session = Depends(get_db)):
    movement = db.query(ItemMovement).get(movement_id)
    if not movement:
        raise HTTPException(status_code=404, detail="Movement not found")
    return movement

@router.put("/{movement_id}", response_model=ItemMovementOut)
def update_movement(movement_id: int, data: ItemMovementCreate, db: Session = Depends(get_db)):
    movement = db.query(ItemMovement).get(movement_id)
    if not movement:
        raise HTTPException(status_code=404, detail="Movement not found")
    for key, value in data.dict().items():
        setattr(movement, key, value)
    db.commit()
    db.refresh(movement)
    return movement

@router.delete("/{movement_id}")
def delete_movement(movement_id: int, db: Session = Depends(get_db)):
    movement = db.query(ItemMovement).get(movement_id)
    if not movement:
        raise HTTPException(status_code=404, detail="Movement not found")
    db.delete(movement)
    db.commit()
    return {"ok": True} 