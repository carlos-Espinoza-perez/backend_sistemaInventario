from pydantic import BaseModel
from datetime import datetime

class SaleBase(BaseModel):
    item_id: int
    warehouse_id: int
    quantity: int
    sale_price: float
    paid: bool = False
    note: str | None = None
    sold_at: datetime | None = None
    sale_group_id: int | None = None

class SaleCreate(SaleBase):
    pass  # user_id se agrega en el backend, no lo manda el frontend

class SaleOut(SaleBase):
    id: int
    user_id: int  # Mostramos quién hizo la venta
    created_at: datetime
    item_name: str | None = None

    class Config:
        orm_mode = True
