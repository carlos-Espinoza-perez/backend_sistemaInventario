from typing import List
from pydantic import BaseModel
from datetime import datetime

from schemas.item import ItemOut


class ItemMovementBase(BaseModel):
    item_id: int
    source_warehouse_id: int | None = None
    target_warehouse_id: int | None = None
    quantity: int
    type: str  # Assuming MovementType is a string representation
    user_id: int | None = None
    timestamp: datetime | None = None
    item_movement_group_id: int | None = None


class ItemMovementCreate(ItemMovementBase):
    # Agregar precio de compra y precio de venta para Inventory
    purchase_price: float | None = None
    sale_price: float | None = None

class ItemMovementOut(ItemMovementBase):
    id: int
    # Agregar precio de compra y precio de venta para Inventory
    purchase_price: float | None = None
    sale_price: float | None = None
    item_name: str | None = None

    class Config:
        orm_mode = True




class ItemMovementBulkCreate(BaseModel):
    items: List[ItemMovementCreate]