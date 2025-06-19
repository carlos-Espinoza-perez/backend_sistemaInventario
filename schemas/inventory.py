from pydantic import BaseModel
from datetime import datetime

class InventoryBase(BaseModel):
    warehouse_id: int
    item_id: int
    quantity: int

class InventoryCreate(InventoryBase):
    pass

class InventoryOut(InventoryBase):
    id: int
    updated_at: datetime

    class Config:
        orm_mode = True