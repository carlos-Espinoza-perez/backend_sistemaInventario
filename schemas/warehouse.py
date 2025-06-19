from pydantic import BaseModel
from datetime import datetime

class WarehouseBase(BaseModel):
    name: str
    location: str | None = None

class WarehouseCreate(WarehouseBase):
    pass

class WarehouseOut(WarehouseBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
