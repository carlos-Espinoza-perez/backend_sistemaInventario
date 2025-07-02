from pydantic import BaseModel
from datetime import datetime

class SaleGroupBase(BaseModel):
    note: str | None = None
    warehouse_id: int | None = None

class SaleGroupCreate(SaleGroupBase):
    pass

class SaleGroupOut(SaleGroupBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        orm_mode = True



class SaleGroupWithSummary(BaseModel):
    id: int
    warehouse_id: int
    note: str | None = None
    user_id: int
    created_at: datetime
    total_items: int

    total_sale_price: float | None = None
    total_debt: float | None = None

    class Config:
        orm_mode = True