from pydantic import BaseModel
from datetime import datetime

class ItemMovementGroupBase(BaseModel):
    note: str | None = None
    warehouse_id: int


class ItemMovementGroupCreate(ItemMovementGroupBase):
    pass

class ItemMovementGroupOut(ItemMovementGroupBase):
    id: int
    user_id: int
    created_at: datetime


    class Config:
        orm_mode = True


class ItemMovementGroupWithSummary(BaseModel):
    id: int
    warehouse_id: int
    note: str | None = None
    user_id: int
    created_at: datetime
    total_items: int

    total_purchase_price: float | None = None  # Nuevo campo
    total_sale_price: float | None = None    # Nuevo campo

    class Config:
        orm_mode = True