from pydantic import BaseModel
from datetime import datetime

class ItemMovementBase(BaseModel):
    item_id: int
    warehouse_id: int
    quantity: int
    movement_type: str  # "in" or "out"
    note: str | None = None

class ItemMovementCreate(ItemMovementBase):
    pass

class ItemMovementOut(ItemMovementBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True