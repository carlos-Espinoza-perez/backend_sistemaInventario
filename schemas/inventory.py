from typing import List
from pydantic import BaseModel
from datetime import datetime

from schemas.item import ItemOut

class InventoryBase(BaseModel):
    warehouse_id: int
    item_id: int
    quantity: int

    purchase_price: float
    sale_price: float

class InventoryCreate(InventoryBase):
    pass

class InventoryOut(InventoryBase):
    id: int
    updated_at: datetime
    item: ItemOut

    class Config:
        orm_mode = True



class InventoryBulkCreate(BaseModel):
    items: List[InventoryCreate]